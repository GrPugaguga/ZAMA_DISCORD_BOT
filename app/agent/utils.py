from typing import List, Dict, Union
from app.init.postgres import get_db_pool
from app.services.redis_service import get_cached_categories, cache_categories, get_cached_titles, cache_titles_by_category, get_cached_documents_by_title_category, cache_documents_by_title_category
import logging

logger = logging.getLogger(__name__)


class DocumentRetriever:
    """Class for retrieving documents from database"""
    
    @staticmethod
    def _build_where_conditions(field_name: str, values: List[str], start_param: int = 1) -> tuple[str, List[str]]:
        """Build WHERE conditions for multiple values"""
        if not values:
            return "", []
        
        placeholders = []
        for i, _ in enumerate(values, start=start_param):
            placeholders.append(f"${i}")
        
        where_clause = f"{field_name} IN ({', '.join(placeholders)})"
        return where_clause, values

    async def vector_search(self, embedding_str: str, limit: int = 4) -> List[Dict]:
        """Search documents by vector similarity"""
        try:
            pool = await get_db_pool()
            
            async with pool.acquire() as conn:
                results = await conn.fetch('''
                    SELECT 
                        title,
                        content,
                        link,
                        category,
                        GREATEST(
                            1 - (t_vector <=> $1::vector),
                            1 - (c_vector <=> $1::vector)
                        ) as similarity
                    FROM zama_fdocs
                    ORDER BY GREATEST(
                        1 - (t_vector <=> $1::vector),
                        1 - (c_vector <=> $1::vector)
                        ) DESC
                    LIMIT $2
                ''', embedding_str, limit)
                
                return [dict(row) for row in results]
        
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []

    async def get_categories(self) -> List[Dict]:
        """Get all categories from cache or database"""
        try:
            # Try to get from cache first
            cached_categories = await get_cached_categories()
            if cached_categories:
                return cached_categories
            
            # If not in cache, get from database
            pool = await get_db_pool()
            
            async with pool.acquire() as conn:
                results = await conn.fetch('''
                    SELECT DISTINCT
                        category
                    FROM zama_fdocs
                    ORDER BY category
                ''')
                
                categories = [dict(row) for row in results]
                
                # Cache the results
                await cache_categories(categories)
                
                return categories
        
        except Exception as e:
            logger.error(f"Get categories error: {e}")
            return []
        
    async def get_titles(self, categories: Union[str, List[str]]) -> List[Dict]:
        """Get titles by categories from cache or database"""
        try:
            # Convert single category to list for uniform handling
            if isinstance(categories, str):
                categories = [categories]
            
            # Try to get from cache first
            cached_titles = await get_cached_titles(categories)
            if cached_titles:
                return cached_titles
            
            # If not in cache, get from database
            pool = await get_db_pool()
            
            async with pool.acquire() as conn:
                where_clause, values = self._build_where_conditions("category", categories)
                
                query = f'''
                    SELECT 
                      id,
                      title,
                      category
                    FROM zama_fdocs
                    WHERE {where_clause}
                    ORDER BY id
                '''
                
                results = await conn.fetch(query, *values)
                all_titles = [dict(row) for row in results]
                
                # Group titles by category for caching
                titles_by_category = {}
                for title in all_titles:
                    category = title['category']
                    if category not in titles_by_category:
                        titles_by_category[category] = []
                    titles_by_category[category].append(title)
                
                # Cache the results by category
                await cache_titles_by_category(titles_by_category)
                
                return all_titles
        
        except Exception as e:
            logger.error(f"Get titles error: {e}")
            return []
        
    async def get_content_by_title(self, titles: Union[str, List[str]]) -> List[Dict]:
        """Get content by titles"""
        try:
            pool = await get_db_pool()
            
            # Convert single title to list for uniform handling
            if isinstance(titles, str):
                titles = [titles]
            
            async with pool.acquire() as conn:
                where_clause, values = self._build_where_conditions("title", titles)
                
                query = f'''
                    SELECT 
                      id,
                      title,
                      content,
                      category
                    FROM zama_fdocs
                    WHERE {where_clause}
                '''
                
                results = await conn.fetch(query, *values)
                
                return [dict(row) for row in results]
        
        except Exception as e:
            logger.error(f"Get content by title error: {e}")
            return []
    
    async def get_content_by_title_and_category(self, titles: Union[str, List[str]], categories: Union[str, List[str]]) -> List[Dict]:
        """Get content by titles filtered by categories from cache or database"""
        try:
            # Convert single values to lists for uniform handling
            if isinstance(titles, str):
                titles = [titles]
            if isinstance(categories, str):
                categories = [categories]
            
            # Try to get from cache first
            cached_documents = await get_cached_documents_by_title_category(titles, categories)
            if cached_documents:
                return cached_documents
            
            # If not in cache, get from database
            pool = await get_db_pool()
            
            async with pool.acquire() as conn:
                # Build WHERE conditions for both titles and categories
                title_clause, title_values = self._build_where_conditions("title", titles, start_param=1)
                category_clause, category_values = self._build_where_conditions("category", categories, start_param=len(titles) + 1)
                
                query = f'''
                    SELECT 
                      title,
                      content,
                      link,
                      category
                    FROM zama_fdocs
                    WHERE {title_clause} AND {category_clause}
                '''
                
                results = await conn.fetch(query, *title_values, *category_values)
                documents = [dict(row) for row in results]
                
                # Cache the results
                await cache_documents_by_title_category(documents)
                
                return documents
        
        except Exception as e:
            logger.error(f"Get content by title and category error: {e}")
            return []
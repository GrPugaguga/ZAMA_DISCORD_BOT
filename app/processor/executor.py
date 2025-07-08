from typing import Dict, List
from app.processor.db_utils import vector_search, title_search
import logging

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Query executor - performs search based on planner results"""
    
    def __init__(self):
        pass
    
    async def execute(self, planner_result: Dict, original_query: str) -> List[Dict]:
        """Execute document search based on planner results"""
        try:
            documents = []
            
            # Search by specific documents
            if planner_result.get("documents"):
                documents.extend(await self._search_by_titles(planner_result))
            
            # Vector search
            if planner_result.get("vector_search", False):
                search_query = self._prepare_vector_query(planner_result, original_query)
                vector_results = await vector_search(
                    query=search_query,
                    limit=5
                )
                documents.extend(vector_results)
            
            return self._remove_duplicates(documents)
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return await self._fallback_search(original_query)
    
    async def _search_by_titles(self, planner_result: Dict) -> List[Dict]:
        """Search documents by titles"""
        documents = []
        document_titles = planner_result.get("document_titles", [])
        
        for title in document_titles:
            title_results = await title_search(
                query=title,
                limit=1
            )
            if title_results:
                documents.extend(title_results)
        
        return documents
    
    def _prepare_vector_query(self, planner_result: Dict, original_query: str) -> str:
        """Prepare query for vector search"""
        suggested_queries = planner_result.get("suggested_queries", [])
        if suggested_queries:
            return f"{original_query} {' '.join(suggested_queries)}"
        return original_query
    
    def _remove_duplicates(self, documents: List[Dict]) -> List[Dict]:
        """Remove duplicates by title"""
        seen_titles = set()
        unique_documents = []
        
        for doc in documents:
            if doc['title'] not in seen_titles:
                seen_titles.add(doc['title'])
                unique_documents.append(doc)
        
        return unique_documents
    
    async def _fallback_search(self, original_query: str) -> List[Dict]:
        """Fallback search on error"""
        try:
            return await vector_search(
                query=original_query,
                limit=5
            )
        except Exception as fallback_error:
            logger.error(f"Error in fallback vector search: {fallback_error}")
            return []

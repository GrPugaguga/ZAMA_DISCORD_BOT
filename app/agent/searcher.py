import json
import re
from typing import Dict, List
from app.init.model import GPT
from app.agent.prompt import  C_SORT_PROMPT,T_SORT_PROMPT,UPDATE_PROMPT
from app.agent.utils import DocumentRetriever
import logging

logger = logging.getLogger(__name__)


class Searcher:
    """Query planner for document selection"""
    
    def __init__(self):
        self.gpt = GPT()
        self.retriever = DocumentRetriever()
        self.max_documents = 3
      

    async def search(self, query: str) -> Dict:
        """Plan document search for query"""
        try:
            categories = await self.sort_by_query(query)
            logger.info(f"categories: {categories}")
            
            if not categories:
                raise Exception("No relevant categories found")
            
            titles = await self.title_sort(query, categories)
            logger.info(f"titles: {titles}")
            
            if not titles:
                raise Exception("No relevant titles found")
            
            # Get documents by titles from selected categories
            documents = await self.retriever.get_content_by_title_and_category(titles, categories)
            
            if len(documents) == 0:
                raise Exception("No documents found")
            
            # Build context from found documents
            context = self._build_context(documents)
            return context
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return await self._create_fallback_response(f"JSON parsing error: {str(e)}", query)
        except Exception as e:
            logger.error(f"Planner error: {e}")
            return await self._create_fallback_response(str(e), query)
    
    async def _create_fallback_response(self, error: str, query: str) -> str:
        """Create fallback response using vector search"""
        logger.info(f"Fallback triggered: {error}")
        logger.info("Using vector search fallback")
        
        try:
            updated_query = await self.update_query(query)
            documents = await self._search_documents(updated_query, limit=4)
            context = self._build_context(documents)
            return context
        except Exception as e:
            logger.error(f"Fallback error: {e}")
            return f"Error in fallback: {str(e)}"
    
    async def sort_by_query(self, query: str) -> List[str]:
        """Sort categories by query"""
        try:
            # Get categories from database
            categories_data = await self.retriever.get_categories()
            
            # Build category list string for prompt
            category_list = "Available categories:\n"
            for i, cat in enumerate(categories_data):
                category_list += f"{i}: {cat['category']}\n"
            
            content = await self.gpt.generate_sort_response([
                {"role": "system", "content": C_SORT_PROMPT},
                {"role": "system", "content": category_list},
                {"role": "user", "content": query}
            ])
            result = json.loads(content)
            
            nums = result.get('nums', '').split(',')
            
            # Convert numbers to category names
            selected_categories = []
            for num in nums:
                if num.strip() and num.strip() != '-1':
                    cat_index = int(num.strip())
                    if 0 <= cat_index < len(categories_data):
                        selected_categories.append(categories_data[cat_index]['category'])
            
            return selected_categories if selected_categories else []
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return []
        except Exception as e:
            logger.error(f"Sort error: {e}")
            return []
    
    async def title_sort(self, query: str, categories: List[str]) -> List[str]:
        """Sort titles by query relevance"""
        try:
            # Get titles for selected categories
            titles_data = await self.retriever.get_titles(categories)
            
            if not titles_data:
                return []
            
            # Build titles list string for prompt
            titles_list = "Available titles:\n"
            for i, title in enumerate(titles_data):
                titles_list += f"{i}: {title['title']}\n"
                        
            content = await self.gpt.generate_sort_response([
                {"role": "system", "content": T_SORT_PROMPT},
                {"role": "system", "content": titles_list},
                {"role": "user", "content": query}
            ])
            result = json.loads(content)
            
            nums = result.get('nums', '').split(',')
            
            # Convert numbers to title names
            selected_titles = []
            for num in nums:
                if num.strip() and num.strip() != '-1':
                    title_index = int(num.strip())
                    if 0 <= title_index < len(titles_data):
                        selected_titles.append(titles_data[title_index]['title'])
            
            return selected_titles if selected_titles else []
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return []
        except Exception as e:
            logger.error(f"Title sort error: {e}")
            return []
    
    # async def validate_relevance(self, query: str, documents: List[Dict]) -> int:
    #     """Validate if documents are relevant to answer the query"""
    #     try:
    #         if not documents:
    #             return -1
    #         
    #         # Build context from documents
    #         context = "Documents:\n"
    #         for i, doc in enumerate(documents, 1):
    #             title = doc.get('title', 'Unknown')
    #             content = doc.get('content', '')  # Limit content length
    #             context += f"{i}. {title}\n{content}...\n\n"
    #         
    #         content = await self.gpt.generate_sort_response([
    #             {"role": "system", "content": VALIDATOR_PROMPT},
    #             {"role": "system", "content": context},
    #             {"role": "user", "content": query}
    #         ])
    #         
    #         result = json.loads(content)
    #         return result.get('relevant', -1)
    #     
    #     except json.JSONDecodeError as e:
    #         logger.error(f"JSON parsing error in validator: {e}")
    #         return -1
    #     except Exception as e:
    #         logger.error(f"Validation error: {e}")
    #         return -1
        
    
    async def update_query(self, query:str) -> str:
        """Update query for search"""
        try:
            return await self.gpt.update_question([
                {"role": "system", "content": UPDATE_PROMPT},
                {"role": "user", "content": query}
            ])
        except Exception as e:
            logger.error(f"Query update error: {e}")
            return query
        
    async def _search_documents(self, question: str, limit: int = 4) -> List[Dict]:
        """Search for documents using vector similarity"""
        try:
            embedding_str = await self.gpt.generate_embedding(question)
            documents = await self.retriever.vector_search(embedding_str, limit=limit)
            
            return documents
        except Exception as e:
            logger.error(f"Document search error: {e}")
            return []

    def _build_context(self, documents: List[Dict]) -> str:
        """Build context string from retrieved documents"""
        # Step 1: Remove duplicates based on title
        unique_docs = {}
        for doc in documents:
            title = doc.get('title', 'Unknown')
            similarity = doc.get('similarity', 0)
            
            # Keep document with highest similarity if duplicate title exists
            if title not in unique_docs or similarity > unique_docs[title]['similarity']:
                unique_docs[title] = doc
        
        # Step 2: Sort by similarity and take all documents
        sorted_docs = sorted(unique_docs.values(), key=lambda x: x.get('similarity', 0), reverse=True)
        top_docs = sorted_docs
        
        # Step 3: Build context
        context_parts = []
        for i, doc in enumerate(top_docs, 1):
            title = doc.get('title', 'Unknown')
            content = doc.get('content', '')
            link = doc.get('link', '')
            context_part = f"Document {i} {title}\n"
            context_part += f"{content}\nLink: {link}"
            
            context_parts.append(context_part)
        
        return "\n".join(context_parts)


if __name__ == "__main__":
    import asyncio
    from app.init.postgres import init_db_pool
    from app.init.redis import init_redis_client
    from app.init.config import get_settings
    

    async def test_planner():
        # Initialize database pool
        config = get_settings()

        await init_redis_client(config.REDIS_URL)

        await init_db_pool(config.DATABASE_URL)
        
        planner = Searcher()
        
        test_queries = [
            "Что такое фхе?",
            "Что такое фхе ос?"
        ]
        
        print("Testing QueryPlanner...\n")
        
        for query in test_queries:
            print(f"Query: {query}")
            try:
                result = await planner.search(query)
                print(f"Result: {result}")
            except Exception as e:
                print(f"Error: {e}")
            print("-" * 50)
    
    asyncio.run(test_planner())


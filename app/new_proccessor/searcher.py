import json
import re
from typing import Dict, List
from app.init.model import GPT
from app.new_proccessor.prompt import  SORT_PROMPT,UPDATE_PROMPT
from app.new_proccessor.utils import vector_search
import logging

logger = logging.getLogger(__name__)


class Searcher:
    """Query planner for document selection"""
    
    def __init__(self):
        self.gpt = GPT()
        self.categories = {
            0:"protocol",
            1:"relayer-sdk-guides",
            2:"solidity-guides",
            3:"zama-protocol-litepaper",
            4:"examples"
        }

        self.max_documents = 5
      

    async def search(self, query: str) -> Dict:
        """Plan document search for query"""
        try:
            categories = await self.sort_by_query(query)
            logger.info(f"categories: {categories}")
            print(categories)
            updated_query = await self.update_query(query)
            print(updated_query)

            logger.info(f"Updated question: {updated_query}")

            documents = await self._search_documents(updated_query,categories)

            if not documents:
                return "Sorry, I couldn't find relevant information for your question."
            
            # Step 3: Collect context from documents
            context = self._build_context(documents)
            return context
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return self._create_fallback_response(f"JSON parsing error: {str(e)}")
        except Exception as e:
            logger.error(f"Planner error: {e}")
            return self._create_fallback_response(str(e))
    
    def _create_fallback_response(self, error: str) -> Dict:
        """Create fallback response on error"""
        return {
            "documents": [], 
            "vector_search": True, 
            "error": error,
            "reasoning": "Error in planning process, falling back to vector search"
        }
    
    async def sort_by_query(self, query: str) -> List[str]:
        """Sort categories by query"""
        try:
            content = await self.gpt.generate_sort_response([
                {"role": "system", "content": SORT_PROMPT},
                {"role": "user", "content": query}
            ])
            result = json.loads(content)
            
            nums = result.get('nums', '').split(',')
            return [self.categories[int(nums[0])], self.categories[int(nums[1])]]
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return ['protocol', 'litepaper']
        except Exception as e:
            logger.error(f"Sort error: {e}")
            return ['protocol', 'litepaper']
        
    
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
        
    async def _search_documents(self, question: str, categories: List[str]) -> List[Dict]:
        """Search for documents using vector similarity"""
        try:
            embedding_str = await self.gpt.generate_embedding(question)
            documents = await vector_search(embedding_str, categories, limit=self.max_documents)
            
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
        
        # Step 2: Sort by similarity and take top 5
        sorted_docs = sorted(unique_docs.values(), key=lambda x: x.get('similarity', 0), reverse=True)
        top_docs = sorted_docs[:self.max_documents]
        
        # Step 3: Build context
        context_parts = []
        for i, doc in enumerate(top_docs, 1):
            title = doc.get('title', 'Unknown')
            content = doc.get('content', '')
            link = doc.get('link', '')
            print(doc.get('similarity', ''))
            context_part = f"Document {i} {title}\n"
            context_part += f"{content}\n {link}"
            
            context_parts.append(context_part)
        
        return "\n".join(context_parts)


if __name__ == "__main__":
    import asyncio
    from app.init.postgres import init_db_pool
    from app.init.config import get_settings
    
    async def test_planner():
        # Initialize database pool
        config = get_settings()
        await init_db_pool(config.DATABASE_URL)
        
        planner = Searcher()
        
        test_queries = [
            "Что такое зама",
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


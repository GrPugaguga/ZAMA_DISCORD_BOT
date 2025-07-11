from typing import List, Dict
from app.init.model import GPT
from app.vc_proccessor.utils import vector_search
from app.vc_proccessor.prompt import MAIN_PROMPT, UPDATE_PROMPT
import logging

logger = logging.getLogger(__name__)


class QueryProcessor_vc:
    """Simple RAG processor for question answering"""
    
    def __init__(self):
        self.gpt_client = GPT()
        self.max_documents = 5
    
    async def process_query(self, question: str) -> str:
        """
        Main method to process user question through RAG pipeline
        1. Convert question to embedding
        2. Search for nearest vectors
        3. Collect context from documents
        4. Generate final answer via LLM
        """
        try:
            # Step 1: Get embedding for the question (handled in vector_search)
            logger.info(f"Processing question: {question}")
            # question = await self._update_query(question)
            # logger.info(f"Updated question: {question}")

            # Step 2: Search for nearest vectors
            documents = await self._search_documents(question)

            if not documents:
                return "Sorry, I couldn't find relevant information for your question."
            
            # Step 3: Collect context from documents
            context = self._build_context(documents)
            logger.info(f"Finded context vc: {context}")

            # Step 4: Generate final answer
            answer = await self._generate_answer(question, context)
            
            return answer
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return "An error occurred while processing your question."
        
    async def _update_query(self, question: str) -> str:
        """Update query for search from llm"""
        try:
            messages = [
                {"role": "system", "content": UPDATE_PROMPT},
                {"role": "user", "content": question}
            ]
            return await self.gpt_client.update_question(messages)
        except Exception as e:
            logger.error(f"Query update error: {e}")
            return question
        
    async def _search_documents(self, question: str) -> List[Dict]:
        """Search for documents using vector similarity"""
        try:
            return await vector_search(question, limit=self.max_documents)
        except Exception as e:
            logger.error(f"Document search error: {e}")
            return []
    
    def _build_context(self, documents: List[Dict]) -> str:
        """Build context string from retrieved documents"""
        context_parts = []
        
        for doc in documents:
            title = doc.get('title', 'Unknown')
            content = doc.get('content', '')
            
            context_part = f"Title: {title}\n"
            context_part += f"Content: {content}\n"
            
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    async def _generate_answer(self, question: str, context: str) -> str:
        """Generate final answer using LLM with context"""
        try:


            messages = [
                {"role": "system", "content": MAIN_PROMPT},
                {"role": "system", "content": f"DOCUMENTATION CONTEXT:\n{context}"},
                {"role": "user", "content": question}
            ]

            response = await self.gpt_client.generate_main_response(messages)
            return f"""ANSWER from vector content\n {response}"""
            
        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            return "Error generating answer."
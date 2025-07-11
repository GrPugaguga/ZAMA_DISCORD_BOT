from typing import List, Dict
from app.init.model import GPT
from app.agent.prompt import MAIN_PROMPT
from app.agent.searcher import Searcher
import logging

logger = logging.getLogger(__name__)


class QueryProcessor:
    """Simple RAG processor for question answering"""
    
    def __init__(self):
        self.gpt_client = GPT()
        self.searcher = Searcher()
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

            context = await self.searcher.search(question)

            answer = await self._generate_answer(question, context)
            
            return answer
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return "An error occurred while processing your question."
        
    
    async def _generate_answer(self, question: str, context: str) -> str:
        """Generate final answer using LLM with context"""
        try:


            messages = [
                {"role": "system", "content": MAIN_PROMPT},
                {"role": "system", "content": f"DOCUMENTATION CONTEXT:\n{context}"},
                {"role": "user", "content": question}
            ]

            response = await self.gpt_client.generate_main_response(messages)
            return response
            
        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            return "Error generating answer."
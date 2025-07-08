from typing import Dict, List
from .planner import QueryPlanner
from .executor import QueryExecutor
from .prompts import MAIN_PROMPT
from app.init.model import GPT
import logging

logger = logging.getLogger(__name__)


class QueryProcessor:
    """Main class for processing queries - orchestrates the entire RAG process"""
    
    def __init__(self):
        self.planner = QueryPlanner()
        self.executor = QueryExecutor()
        self.gpt = GPT()
        
        logger.info("QueryProcessor initialized successfully")
    
    async def process_query(self, question: str) -> str:
        """
        Processes user question and returns final answer
        
        Args:
            question: User's question
            
        Returns:
            Final answer from LLM
        """
        try:
            logger.info(f"Processing query: {question[:100]}...")
            
            # Step 1: Planning
            logger.debug("Starting planning phase")
            planner_result = await self.planner.plan(question)
            logger.debug(f"Planner result: {planner_result}")
            
            # Step 2: Document retrieval execution
            logger.debug("Starting execution phase")
            documents = await self.executor.execute(planner_result, question)
            logger.debug(f"Found {len(documents)} documents")

            # Step 3: Final response generation
            logger.debug("Starting response generation")
            final_answer = await self._generate_final_response(question, documents)
            
            logger.info("Query processed successfully")
            return final_answer
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    async def _generate_final_response(self, question: str, documents: List[Dict]) -> str:
        """Generates final response based on found documents"""
        try:
            # Prepare context from found documents
            context = self._prepare_context(documents)
            
            # Form messages for LLM
            messages = [
                {"role": "system", "content": MAIN_PROMPT},
                {"role": "system", "content": f"DOCUMENTATION CONTEXT:\n{context}"},
                {"role": "user", "content": question}
            ]
            
            # Generate response
            response = await self.gpt.generate_main_response(messages)
            logger.debug("Final response generated successfully")
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating final response: {e}")
            return f"Error generating response: {str(e)}"
    
    def _prepare_context(self, documents: List[Dict]) -> str:
        """Prepares context from list of documents"""
        if not documents:
            return "No relevant documents found."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            doc_info = f"""
DOCUMENT {i}:
Title: {doc.get('title', 'Untitled')}
Content: {doc.get('content', 'Content unavailable')}
"""
            context_parts.append(doc_info)
        
        return "\n".join(context_parts)
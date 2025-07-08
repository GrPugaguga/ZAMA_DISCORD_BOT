import json
import re
from typing import Dict, List
from app.init.model import GPT
from app.processor.prompts import DOCUMENTATION_INDEX, PLANNER_PROMPT
import logging

logger = logging.getLogger(__name__)


class QueryPlanner:
    """Query planner for document selection"""
    
    def __init__(self):
        self.gpt = GPT()
        self.documents_list = DOCUMENTATION_INDEX.strip()
        self._parse_documentation_index()
    
    def _parse_documentation_index(self):
        """Parse documentation index into structured format"""
        self.documents = {}
        lines = self.documents_list.split('\n')
        
        for line in lines:
            line = line.strip()
            if line:
                match = re.match(r'^(\d+)\.\s+(.+)$', line)
                if match:
                    num = int(match.group(1))
                    title = match.group(2)
                    self.documents[num] = title
    
    async def plan(self, query: str) -> Dict:
        """Plan document search for query"""
        try:
            messages = [
                {"role": "system", "content": PLANNER_PROMPT},
                {"role": "system", "content": self.documents_list},
                {"role": "user", "content": query}
            ]
            
            content = await self.gpt.generate_planner_response(messages)
            result = json.loads(content)
            result = self._validate_and_normalize_result(result)
            
            if result.get("documents"):
                result["document_titles"] = self.get_titles_by_numbers(result["documents"])
            
            return result
            
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
    
    def _validate_and_normalize_result(self, result: Dict) -> Dict:
        """Validate and normalize LLM result"""
        if "documents" not in result:
            result["documents"] = []
        
        if isinstance(result["documents"], list):
            valid_docs = []
            for doc in result["documents"]:
                if isinstance(doc, int) and 1 <= doc <= len(self.documents):
                    valid_docs.append(doc)
            result["documents"] = valid_docs[:5]
        else:
            result["documents"] = []
        
        if "vector_search" not in result:
            result["vector_search"] = len(result["documents"]) == 0
        
        if result.get("vector_search") and "suggested_queries" not in result:
            result["suggested_queries"] = []
        
        return result
    
    def get_titles_by_numbers(self, numbers: List[int]) -> List[str]:
        """Get document titles by numbers"""
        titles = []
        for num in numbers:
            if num in self.documents:
                titles.append(self.documents[num])
        return titles


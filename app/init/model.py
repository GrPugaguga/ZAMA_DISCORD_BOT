from openai import AsyncOpenAI
from typing import List, Dict
import logging
from app.init.config import get_settings

logger = logging.getLogger(__name__)


class GPT:
    def __init__(self):
        self.config = get_settings()
        self.client = AsyncOpenAI()
        self.model = self.config.LLM_MODEL
        self.embedding_model = self.config.EMBEDDING_MODEL
    
    async def _generate_response(self, messages: List[Dict], **kwargs) -> str:
        """Base method for generating responses"""
        try:
            # Set defaults from config, but allow override from kwargs
            params = {
                'model': self.model,
                'messages': messages,
                'temperature': self.config.OPENAI_TEMPERATURE,
                'max_tokens': self.config.OPENAI_MAX_TOKENS,
                'timeout': self.config.OPENAI_TIMEOUT,
            }
            
            # Update with any provided kwargs (allows overriding defaults)
            params.update(kwargs)
            
            response = await self.client.chat.completions.create(**params)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    async def generate_planner_response(self, messages: List[Dict]) -> str:
        """Generate response for planner"""
        return await self._generate_response(
            messages,
            temperature=self.config.PLANNER_TEMPERATURE,
            max_tokens=self.config.PLANNER_MAX_TOKENS,
            response_format={"type": "json_object"}
        )
    
    async def generate_main_response(self, messages: List[Dict]) -> str:
        """Generate main response"""
        return await self._generate_response(messages)
    
    async def generate_embedding(self, query: str) -> str:
        """Generate text embedding"""
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=query
            )
            embedding = response.data[0].embedding
            return '[' + ','.join(map(str, embedding)) + ']'
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
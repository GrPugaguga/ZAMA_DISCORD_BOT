import logging
import discord
from discord.ext import commands
from app.agent import QueryProcessor
# from app.hybrid_proccessor import QueryProcessor

from app.init.postgres import init_db_pool
from app.init.redis import init_redis_client
from app.services.rate_limit import check_rate_limit
from app.init.config import get_settings

logger = logging.getLogger(__name__)


class ZamaDiscordBot(commands.Bot):
    """Discord bot for Zama Protocol RAG system"""
    
    def __init__(self):
        self.config = get_settings()
        
        # Set up intents
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(command_prefix='!', intents=intents)
        
        self.processor=None

    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("ZamaDiscordBot is starting up...")
        
        # Initialize database pool
        await init_db_pool(
            self.config.DATABASE_URL,
            min_size=self.config.DB_MIN_SIZE,
            max_size=self.config.DB_MAX_SIZE
        )
        
        # Initialize Redis client
        await init_redis_client(self.config.REDIS_URL)
        
        # Initialize QueryProcessor
        self.processor = QueryProcessor()


    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
    async def on_message(self, message: discord.Message):
        """Handle incoming messages"""
        # Ignore messages from bots
        if message.author.bot:
            return
            
        # Handle DMs (private messages)
        if isinstance(message.channel, discord.DMChannel):
            await self.handle_dm(message)
            return
            
        # Handle mentions in servers
        if self.user in message.mentions:
            await self.handle_mention(message)
            
    async def handle_mention(self, message: discord.Message):
        """Handle bot mentions in any channel"""
        logger.info(f"Received mention from {message.author.id} in channel {message.channel.id}")
        
        # Extract query (remove mention)
        query = message.content
        for mention in message.mentions:
            if mention == self.user:
                query = query.replace(f'<@{mention.id}>', '').strip()
                query = query.replace(f'<@!{mention.id}>', '').strip()  # Handle nickname mentions
                
        if not query:
            await message.reply("Hello! Ask me a question about Zama Protocol.")
            return
            
        # Process the query
        await self.process_query(message, query)
        
    async def handle_dm(self, message: discord.Message):
        """Handle direct messages (private messages)"""
        logger.info(f"Received DM from {message.author.id}")
        
        query = message.content.strip()
        
        if not query:
            await message.reply("Hello! Ask me a question about Zama Protocol.")
            return
            
        # Process the query in DM
        await self.process_query(message, query)
        
    async def process_query(self, message: discord.Message, query: str):
        """Process user query through RAG pipeline with rate limiting"""
        user_id = message.author.id
        channel_id = message.channel.id
        
        # Check rate limits
        is_allowed, wait_seconds = await check_rate_limit(user_id, channel_id)
        
        if not is_allowed:
            rate_limit_message = f"Too many requests! Please wait {wait_seconds} seconds before sending another message."
            await message.reply(rate_limit_message)
            return
        
        # Show typing indicator
        async with message.channel.typing():
            try:
                logger.info(f"Processing query from user {user_id}: {query[:50]}...")
                
                # Use QueryProcessor to get answer
                answer_hd = await self.processor.process_query(query)


                # Send response
                await message.reply(answer_hd)

                logger.info(f"Successfully processed query for user {user_id}")
                        
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                error_response = "Sorry, an error occurred while processing your request. Please try again."
                await message.reply(error_response)
                    
    def run_bot(self):
        """Run the Discord bot"""
        logger.info("Starting Zama Protocol Discord Bot...")
        
        try:
            self.run(self.config.DISCORD_TOKEN)
        except Exception as e:
            logger.error(f"Bot error: {e}")
        finally:
            logger.info("Discord bot stopped.")


def main():
    """Main function to run the Discord bot"""
    bot = ZamaDiscordBot()
    bot.run_bot()


if __name__ == "__main__":
    main()
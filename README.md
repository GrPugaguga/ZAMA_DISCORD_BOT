# Zama Protocol Discord Bot

A production-ready Discord bot powered by **RAG (Retrieval-Augmented Generation)** technology, designed to answer questions about Zama Protocol's Fully Homomorphic Encryption (FHE) documentation.

![Discord](https://img.shields.io/badge/Discord-Bot-7289da?style=for-the-badge&logo=discord&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Vector-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Cache-dc382d?style=for-the-badge&logo=redis&logoColor=white)
![Railway](https://img.shields.io/badge/Deployed_on-Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

---

## 🎯 Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Smart Document Search** | Vector similarity + title-based search | ✅ |
| **Redis Caching** | 24h TTL for frequently accessed documents | ✅ |
| **Rate Limiting** | 20 req/min per user, 60 req/min per channel | ✅ |
| **Multi-language Support** | Responds in user's language (prompts in English) | ✅ |
| **Production Ready** | Docker, Railway deployment, error handling | ✅ |
| **Real-time Responses** | Async architecture with typing indicators | ✅ |

---

## 🏗️ Architecture

```mermaid
graph TD
    A[Discord User] -->|Message| B[Discord Bot]
    B --> C[Rate Limiter]
    C -->|Pass| D[Query Processor]
    C -->|Block| E[Rate Limit Message]
    
    D --> F[Query Planner]
    D --> G[Query Executor]
    D --> H[Response Generator]
    
    F -->|Document Selection| I[GPT-4.1-nano]
    G --> J[Redis Cache]
    G --> K[PostgreSQL + pgvector]
    G --> L[Vector Search]
    G --> M[Title Search]
    
    J -->|Cache Hit| N[Cached Results]
    J -->|Cache Miss| K
    
    H -->|Final Answer| I
    H -->|Response| B
    B -->|Reply| A
    
    style A fill:#7289da,stroke:#fff,stroke-width:2px,color:#fff
    style B fill:#99aab5,stroke:#fff,stroke-width:2px,color:#fff
    style I fill:#10a37f,stroke:#fff,stroke-width:2px,color:#fff
    style J fill:#dc382d,stroke:#fff,stroke-width:2px,color:#fff
    style K fill:#336791,stroke:#fff,stroke-width:2px,color:#fff
```

### 🔄 Data Flow

| Step | Component | Action | Technology |
|------|-----------|--------|------------|
| 1 | **Rate Limiter** | Check user/channel limits | Redis counters |
| 2 | **Query Planner** | Analyze query & select strategy | GPT-4.1-nano + JSON mode |
| 3 | **Query Executor** | Search documents | PostgreSQL + Redis |
| 4 | **Vector Search** | Semantic similarity matching | OpenAI embeddings |
| 5 | **Title Search** | Exact title matching (cached) | PostgreSQL LIKE |
| 6 | **Response Generator** | Generate final answer | GPT-4.1-nano + context |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL with pgvector extension
- Redis instance
- OpenAI API key
- Discord bot token

### Installation

```bash
# Clone repository
git clone <repository-url>
cd ZAMA_DISCORD_BOT

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run the bot
python app/main.py
```

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:password@host:5432/database
REDIS_URL=redis://localhost:6379/0
DISCORD_TOKEN=your_discord_bot_token
LLM_MODEL=GPT-4.1-nano
OPENAI_API_KEY=your_openai_api_key

# Optional (with defaults)
EMBEDDING_MODEL=text-embedding-3-small
LOG_LEVEL=INFO
USER_RATE_LIMIT_PER_MINUTE=20
CHANNEL_RATE_LIMIT_PER_MINUTE=60
CACHE_TTL_SECONDS=86400
```

---

## ⚙️ Configuration

### Database Schema

```sql
CREATE TABLE zama_documents (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    keywords TEXT[],
    content_vector vector(1536),  -- OpenAI embedding dimension
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create vector similarity index
CREATE INDEX ON zama_documents USING ivfflat (content_vector vector_cosine_ops);
```

### Rate Limiting Configuration

| Limit Type | Default Value | Redis Key Pattern | TTL |
|------------|---------------|-------------------|-----|
| Per User | 20 req/min | `rate_limit:user:{user_id}:{minute}` | 60s |
| Per Channel | 60 req/min | `rate_limit:channel:{channel_id}:{minute}` | 60s |

### Cache Configuration

| Cache Type | Key Pattern | TTL | Purpose |
|------------|-------------|-----|---------|
| Title Search | `title_search:{query_hash}` | 24h | Document lookup optimization |
| Document Content | Auto-managed | 24h | Reduce database queries |

---

## 🔧 API Reference

### Core Classes

#### QueryProcessor
```python
class QueryProcessor:
    async def process_query(self, question: str) -> str:
        """Main entry point for processing user queries"""
```

#### QueryPlanner
```python
class QueryPlanner:
    async def plan(self, query: str) -> Dict:
        """Analyze query and determine search strategy"""
```

#### QueryExecutor
```python
class QueryExecutor:
    async def execute(self, planner_result: Dict, original_query: str) -> List[Dict]:
        """Execute document search based on planner results"""
```

### Discord Bot Commands

| Interaction Type | Format | Example |
|------------------|--------|---------|
| **Direct Message** | Send any message | `How does FHE work?` |
| **Server Mention** | `@bot_name <question>` | `@zama_bot What is FHEVM?` |

### Response Format

```json
{
  "type": "text_response",
  "content": "FHE (Fully Homomorphic Encryption) allows...",
  "sources": 3,
  "response_time_ms": 1250,
  "cached": false
}
```

---

## 🚢 Deployment

### Railway Deployment

1. **Connect Repository**
   ```bash
   railway login
   railway link <project-id>
   ```

2. **Set Environment Variables**
   ```bash
   railway variables set DATABASE_URL=<your-db-url>
   railway variables set REDIS_URL=<your-redis-url>
   railway variables set DISCORD_TOKEN=<your-token>
   railway variables set OPENAI_API_KEY=<your-key>
   railway variables set LLM_MODEL=GPT-4.1-nano
   ```

3. **Deploy**
   ```bash
   railway up
   ```

### Docker Deployment

```bash
# Build image
docker build -t zama-discord-bot .

# Run container
docker run -d \
  --name zama-bot \
  --env-file .env \
  zama-discord-bot
```

### Health Monitoring

The bot includes comprehensive logging and error handling:

```python
# Example log output
2025-07-08 12:02:48 - INFO - zama_protocol_bot has connected to Discord!
2025-07-08 12:02:48 - INFO - Bot is in 1 guilds
2025-07-08 12:03:15 - INFO - Processing query from user 123456789: How does FHE work?
2025-07-08 12:03:16 - DEBUG - Found 3 documents
2025-07-08 12:03:17 - INFO - Successfully processed query for user 123456789
```

---

## 📊 Performance Metrics

### Typical Response Times

| Operation | Time Range | Optimization |
|-----------|------------|--------------|
| **Cache Hit** | 50-200ms | Redis lookup |
| **Vector Search** | 300-800ms | PostgreSQL + embeddings |
| **Title Search** | 100-300ms | Database LIKE query |
| **Full Pipeline** | 1-3 seconds | End-to-end processing |

### Resource Usage

| Resource | Development | Production |
|----------|-------------|------------|
| **Memory** | ~100MB | ~200MB |
| **CPU** | Low | Low-Medium |
| **Database Connections** | 5-20 | 5-20 (pooled) |
| **Redis Connections** | 1 | 1 (persistent) |

---

## 🛠️ Development

### Project Structure

```
ZAMA_DISCORD_BOT/
├── app/
│   ├── init/                 # Initialization modules
│   │   ├── config.py        # Configuration management
│   │   ├── model.py         # OpenAI GPT interface
│   │   ├── postgres.py      # Database connection pool
│   │   └── redis.py         # Redis client
│   ├── processor/           # RAG processing pipeline
│   │   ├── __init__.py      # Main QueryProcessor
│   │   ├── planner.py       # Query planning logic
│   │   ├── executor.py      # Search execution
│   │   ├── db_utils.py      # Database utilities
│   │   └── prompts.py       # LLM prompts
│   └── services/            # External services
│       ├── discord_service.py  # Discord bot implementation
│       ├── rate_limit.py       # Rate limiting logic
│       └── redis_service.py    # Redis caching utilities
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
├── railway.json           # Railway deployment config
└── README.md              # This file
```

### Adding New Features

1. **New Search Method**
   ```python
   # In app/processor/executor.py
   async def new_search_method(self, query: str) -> List[Dict]:
       # Implementation here
       pass
   ```

2. **Custom Rate Limits**
   ```python
   # In app/services/rate_limit.py
   CUSTOM_LIMITS = {
       'premium_users': 100,  # 100 req/min for premium
       'admin_users': 0       # No limit for admins
   }
   ```

3. **Additional Caching**
   ```python
   # In app/services/redis_service.py
   async def cache_embeddings(self, text: str, embedding: List[float]):
       # Cache embeddings to avoid recomputation
   ```

---

## 🔐 Security Features

| Feature | Implementation | Purpose |
|---------|----------------|---------|
| **Rate Limiting** | Redis-based counters | Prevent abuse |
| **Input Validation** | Pydantic schemas | Validate configuration |
| **Non-root Container** | Docker user switching | Container security |
| **Environment Isolation** | .env + validation | Secure configuration |
| **Error Handling** | Comprehensive try-catch | Prevent information leakage |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- All code comments and documentation in English
- Follow Python PEP 8 style guidelines
- Add type hints for all functions
- Include comprehensive error handling
- Write tests for new features

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Zama Protocol** for FHE technology and documentation
- **OpenAI** for GPT-4.1-nano and embedding models
- **Discord.py** for Discord API integration
- **Railway** for seamless deployment platform

---

<div align="center">

**[🔗 Deploy on Railway](https://railway.app)** | **[📖 Zama Docs](https://docs.zama.ai)** | **[💬 Discord Support](https://discord.gg/zama)**

Made with ❤️ for the FHE community

</div>

---


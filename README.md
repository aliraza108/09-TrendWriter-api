# TrendWriter — LinkedIn Content Automation API

**LinkedIn Content Automation & Growth Intelligence System**

Closed-loop AI engine: trend detection → content generation → scheduling → publishing → analytics → optimization.

---

## 🏗️ Project Structure

```
trendwriter/
├── main.py                    # FastAPI app entry point (Gemini SDK config here)
├── requirements.txt
├── .env.example
│
├── db/
│   └── database.py            # Async SQLAlchemy engine + session
│
├── models/                    # ORM models (SQLAlchemy)
│   ├── user.py
│   ├── content.py
│   └── analytics.py
│
├── schemas/
│   └── schemas.py             # Pydantic request/response models
│
├── agents/
│   └── content_agent.py       # AI agents (Gemini via openai-agents SDK)
│       ├── trend_agent        # Detects trending LinkedIn topics
│       ├── content_agent      # Generates post variants
│       └── strategy_agent     # 7-day content strategy planner
│
├── services/
│   ├── scheduler.py           # Optimal time prediction + queue management
│   ├── publisher.py           # LinkedIn API publishing
│   └── analytics_service.py  # Engagement metrics + growth tracking
│
└── routers/
    ├── users.py               # User account management
    ├── content.py             # Content generation endpoints
    ├── schedule.py            # Scheduling endpoints
    ├── publish.py             # Publishing endpoints
    ├── analytics.py           # Analytics endpoints
    └── strategy.py            # Strategy recommendation endpoints
```

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env — add GEMINI_API_KEY + LinkedIn credentials

# 3. Run
uvicorn main:app --reload --port 8000
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## 🔌 API Endpoints

### Users
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/users/` | Create user account |
| `GET` | `/users/{user_id}` | Get user profile |
| `PATCH` | `/users/{user_id}` | Update preferences |

### Content Generation
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/content/generate` | Generate AI post variants (from trends or custom topic) |
| `POST` | `/content/variants` | Generate more variants for an existing post |
| `GET` | `/content/{post_id}` | Get a post |
| `GET` | `/content/user/{user_id}` | List all user posts |

### Scheduling
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/schedule/post` | Schedule post (AI picks time if none given) |
| `GET` | `/schedule/calendar?user_id=` | View content calendar |
| `PATCH` | `/schedule/update/{post_id}` | Reschedule a post |

### Publishing
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/publish/` | Publish to LinkedIn immediately |
| `GET` | `/publish/status/{post_id}` | Check publish status |

### Analytics
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/analytics/post/{post_id}` | Post-level metrics |
| `POST` | `/analytics/post/{post_id}/sync` | Sync latest from LinkedIn |
| `GET` | `/analytics/growth/{user_id}` | Follower growth history |
| `GET` | `/analytics/engagement/{user_id}` | Engagement summary (default 30 days) |

### Strategy
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/strategy/recommendations/{user_id}` | AI 7-day content strategy |
| `POST` | `/strategy/update` | Submit feedback / approved topics |

---

## 🧠 AI Agents (Gemini Backend)

Same SDK pattern as your scraper — `openai-agents` + Gemini:

```python
# main.py — same pattern you already use
client = AsyncOpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=api_key,
)
set_default_openai_client(client=client)
```

Three agents inside `agents/content_agent.py`:

| Agent | Purpose |
|-------|---------|
| `trend_agent` | Finds hot LinkedIn topics for user's niche |
| `content_agent` | Writes hook + body + CTA + hashtags (N variants) |
| `strategy_agent` | Plans a 7-day content calendar with timing recommendations |

---

## ♻️ The Optimization Loop

```
User Niche
    ↓
Trend Detection (trend_agent)
    ↓
Content Generation (content_agent) → N Variants with predicted scores
    ↓
Optimal Time Prediction (scheduler.py → learns from engagement history)
    ↓
LinkedIn Publishing (publisher.py → LinkedIn API v2)
    ↓
Engagement Sync (analytics_service.py → impressions, likes, comments...)
    ↓
Strategy Refresh (strategy_agent → adapts based on what worked)
    ↑___________________________|
```

---

## 🔮 Extending the System

- **Cron job for auto-publishing**: Use `APScheduler` or `Celery` to call `POST /publish` at scheduled times
- **LinkedIn OAuth flow**: Add an `/auth/linkedin` router using `authlib`
- **Multi-account agency**: The `user_id` foreign key already supports multiple accounts
- **Postgres in prod**: Change `DATABASE_URL` in `.env` to `postgresql+asyncpg://...`

"""
Strategy Router
GET  /strategy/recommendations → AI-generated content strategy
POST /strategy/update          → user feedback loop
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update as sql_update

from db.database import get_db
from models.user import User
from schemas.schemas import StrategyRecommendation, StrategyUpdateRequest
from ai_agents.content_agent import get_strategy_recommendations
from services.analytics_service import get_engagement_summary

router = APIRouter()


@router.get("/recommendations/{user_id}", response_model=StrategyRecommendation)
async def recommendations(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Full AI strategy:
    1. Load user profile
    2. Pull 30-day engagement summary
    3. Run strategy agent
    4. Return 7-day content plan + insights
    """
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found.")

    # Gather performance context
    perf = await get_engagement_summary(user_id, 30, db)

    user_prefs = {
        "posting_frequency": user.posting_frequency,
        "tone_style": user.tone_style,
        "content_goals": user.content_goals,
        "target_audience": user.target_audience,
    }

    strategy = await get_strategy_recommendations(
        niche=user.niche,
        recent_performance=perf,
        user_prefs=user_prefs,
    )

    return StrategyRecommendation(
        user_id=user_id,
        **strategy,
    )


@router.post("/update")
async def update_strategy(body: StrategyUpdateRequest, db: AsyncSession = Depends(get_db)):
    """
    Feedback loop — user approves / adjusts recommendations.
    Persists preferences to user profile.
    """
    updates = {}
    if body.tone_feedback:
        updates["tone_style"] = body.tone_feedback
    if updates:
        await db.execute(
            sql_update(User).where(User.user_id == body.user_id).values(**updates)
        )
        await db.commit()

    return {
        "status": "ok",
        "message": "Strategy preferences updated.",
        "approved_topics": body.approved_topics or [],
        "preferred_formats": body.preferred_formats or [],
        "preferred_times": body.preferred_times or [],
    }

"""
Analytics Router
GET /analytics/post/{post_id}         → metrics for one post
POST /analytics/post/{post_id}/sync   → pull fresh data from LinkedIn
GET /analytics/growth/{user_id}       → follower growth history
GET /analytics/engagement/{user_id}   → engagement summary
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db
from models.content import Post
from models.user import User
from models.analytics import GrowthSnapshot
from schemas.schemas import PostMetricsOut, GrowthOut, EngagementSummary
from services.analytics_service import (
    get_post_metrics,
    fetch_post_metrics_from_linkedin,
    upsert_metrics,
    get_engagement_summary,
    get_growth_history,
)

router = APIRouter()


@router.get("/post/{post_id}", response_model=PostMetricsOut)
async def get_metrics(post_id: str, db: AsyncSession = Depends(get_db)):
    metrics = await get_post_metrics(post_id, db)
    if not metrics:
        raise HTTPException(404, "No metrics found. Try syncing first.")
    return metrics


@router.post("/post/{post_id}/sync", response_model=PostMetricsOut)
async def sync_metrics(
    post_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Pull latest engagement data from LinkedIn and store it."""
    post_result = await db.execute(select(Post).where(Post.post_id == post_id))
    post = post_result.scalar_one_or_none()
    if not post or not post.linkedin_post_id:
        raise HTTPException(400, "Post not published yet.")

    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.linkedin_access_token:
        raise HTTPException(400, "No LinkedIn token found.")

    li_data = await fetch_post_metrics_from_linkedin(
        post.linkedin_post_id, user.linkedin_access_token
    )
    metrics = await upsert_metrics(
        post_id=post_id,
        user_id=user_id,
        impressions=li_data.get("impressions", 0),
        likes=li_data.get("likes", 0),
        comments=li_data.get("comments", 0),
        shares=li_data.get("shares", 0),
        db=db,
    )
    return metrics


@router.get("/growth/{user_id}", response_model=list[GrowthOut])
async def growth_history(user_id: str, db: AsyncSession = Depends(get_db)):
    snapshots = await get_growth_history(user_id, db)
    return snapshots


@router.get("/engagement/{user_id}", response_model=EngagementSummary)
async def engagement_summary(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    data = await get_engagement_summary(user_id, days, db)
    return EngagementSummary(
        user_id=user_id,
        period_days=days,
        **data,
    )

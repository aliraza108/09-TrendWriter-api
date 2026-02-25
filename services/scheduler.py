"""
Scheduling Service
- Predicts optimal posting time based on engagement history
- Manages post queue
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models.content import Post
from models.analytics import PostMetrics


# Best time slots (day_of_week 0=Mon, hour)
_DEFAULT_SLOTS = [
    (1, 8),   # Tuesday  08:00
    (1, 12),  # Tuesday  12:00
    (2, 9),   # Wednesday 09:00
    (3, 8),   # Thursday  08:00
    (3, 17),  # Thursday  17:00
    (4, 7),   # Friday    07:00
]


async def predict_optimal_time(user_id: str, db: AsyncSession) -> datetime:
    """
    Analyze past engagement to recommend next best posting time.
    Falls back to hardcoded LinkedIn peak times if no history.
    """
    # Try to learn from history
    stmt = (
        select(Post.scheduled_time, PostMetrics.engagement_rate)
        .join(PostMetrics, Post.post_id == PostMetrics.post_id, isouter=True)
        .where(Post.user_id == user_id, Post.status == "published")
        .order_by(PostMetrics.engagement_rate.desc())
        .limit(20)
    )
    rows = (await db.execute(stmt)).fetchall()

    best_slot = None
    if rows:
        # Find most frequent high-engagement hour
        slot_scores: dict[tuple, float] = {}
        for sched, rate in rows:
            if sched:
                key = (sched.weekday(), sched.hour)
                slot_scores[key] = slot_scores.get(key, 0) + (rate or 0)
        if slot_scores:
            best_slot = max(slot_scores, key=lambda k: slot_scores[k])

    if not best_slot:
        best_slot = _DEFAULT_SLOTS[0]  # Tuesday 08:00

    # Next occurrence of that (weekday, hour)
    now = datetime.utcnow()
    days_ahead = (best_slot[0] - now.weekday()) % 7
    if days_ahead == 0 and now.hour >= best_slot[1]:
        days_ahead = 7
    target = (now + timedelta(days=days_ahead)).replace(
        hour=best_slot[1], minute=0, second=0, microsecond=0
    )
    return target


async def schedule_post(
    post_id: str,
    scheduled_time: datetime,
    db: AsyncSession,
) -> Post:
    await db.execute(
        update(Post)
        .where(Post.post_id == post_id)
        .values(scheduled_time=scheduled_time, status="scheduled")
    )
    await db.commit()
    result = await db.execute(select(Post).where(Post.post_id == post_id))
    return result.scalar_one()


async def get_calendar(user_id: str, db: AsyncSession) -> list[Post]:
    result = await db.execute(
        select(Post)
        .where(Post.user_id == user_id, Post.status == "scheduled")
        .order_by(Post.scheduled_time)
    )
    return result.scalars().all()


async def update_schedule(post_id: str, new_time: datetime, db: AsyncSession) -> Post:
    await db.execute(
        update(Post).where(Post.post_id == post_id).values(scheduled_time=new_time)
    )
    await db.commit()
    result = await db.execute(select(Post).where(Post.post_id == post_id))
    return result.scalar_one()

"""
Scheduling Router
POST  /schedule/post       → schedule a post (AI picks time if none given)
GET   /schedule/calendar   → get user's content calendar
PATCH /schedule/update/{post_id} → reschedule a post
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db
from models.content import Post
from schemas.schemas import SchedulePostRequest, ScheduleUpdateRequest, CalendarResponse, ScheduledPostOut
from services.scheduler import predict_optimal_time, schedule_post, get_calendar, update_schedule

router = APIRouter()


@router.post("/post", response_model=ScheduledPostOut)
async def schedule(body: SchedulePostRequest, db: AsyncSession = Depends(get_db)):
    """
    Schedule a draft post.
    If scheduled_time is omitted, AI predicts the optimal window.
    """
    # Validate post exists
    result = await db.execute(select(Post).where(Post.post_id == body.post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(404, "Post not found.")

    # Apply selected variant body if specified
    if body.variant_id and post.variants:
        variant = next(
            (v for v in post.variants if v.get("variant_id") == body.variant_id), None
        )
        if variant:
            post.hook = variant.get("hook", post.hook)
            post.content_body = variant.get("body", post.content_body)
            post.cta = variant.get("cta", post.cta)
            post.hashtags = variant.get("hashtags", post.hashtags)
            await db.commit()

    # Get or predict time
    time = body.scheduled_time or await predict_optimal_time(body.user_id, db)
    updated = await schedule_post(body.post_id, time, db)
    return updated


@router.get("/calendar", response_model=CalendarResponse)
async def calendar(user_id: str, db: AsyncSession = Depends(get_db)):
    posts = await get_calendar(user_id, db)
    return CalendarResponse(user_id=user_id, posts=posts)


@router.patch("/update/{post_id}", response_model=ScheduledPostOut)
async def reschedule(
    post_id: str,
    body: ScheduleUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    updated = await update_schedule(post_id, body.scheduled_time, db)
    if not updated:
        raise HTTPException(404, "Post not found.")
    return updated

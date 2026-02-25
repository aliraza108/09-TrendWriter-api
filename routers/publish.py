"""
Publishing Router
POST /publish        → publish to LinkedIn now
GET  /publish/status → get publish status of a post
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db
from models.content import Post
from schemas.schemas import PublishRequest, PublishStatusOut
from services.publisher import publish_post

router = APIRouter()


@router.post("/", response_model=PublishStatusOut)
async def publish(body: PublishRequest, db: AsyncSession = Depends(get_db)):
    """Publish a post immediately to LinkedIn."""
    try:
        post = await publish_post(body.post_id, body.user_id, db)
        return post
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, f"LinkedIn API error: {e}")


@router.get("/status/{post_id}", response_model=PublishStatusOut)
async def publish_status(post_id: str, db: AsyncSession = Depends(get_db)):
    """Check the publish status of a post."""
    result = await db.execute(select(Post).where(Post.post_id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(404, "Post not found.")
    return post

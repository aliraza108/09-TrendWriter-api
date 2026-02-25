"""
Content Generation Router
POST /content/generate   → generate post variants
POST /content/variants   → generate more variants for existing post
GET  /content/{post_id}  → fetch a single post
GET  /content/user/{user_id} → list all posts for user
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db
from models.content import Post
from models.user import User
from schemas.schemas import (
    ContentGenerateRequest, ContentGenerateResponse,
    ContentVariantsRequest, ContentVariant,
)
from ai_agents.content_agent import detect_trends, generate_post_variants

router = APIRouter()


@router.post("/generate", response_model=ContentGenerateResponse, status_code=201)
async def generate_content(body: ContentGenerateRequest, db: AsyncSession = Depends(get_db)):
    """
    Main generation endpoint.
    If no topic provided → picks from live trends.
    Returns N content variants with predicted scores.
    """
    # 1. Load user
    user_result = await db.execute(select(User).where(User.user_id == body.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found.")

    # 2. Topic: use provided or pull from trends
    topic = body.topic
    trend_context = ""
    if not topic:
        trends = await detect_trends(user.niche)
        if trends:
            top = trends[0]
            topic = top["topic"]
            trend_context = top.get("reason", "")
        else:
            topic = f"Key insights in {user.niche}"

    # 3. Generate variants via AI agent
    tone = body.tone_override or user.tone_style
    raw = await generate_post_variants(
        topic=topic,
        niche=user.niche,
        format_type=body.format,
        tone=tone,
        target_audience=user.target_audience,
        num_variants=body.num_variants,
    )
    variants_data = raw.get("variants", [])
    if not variants_data:
        raise HTTPException(500, "AI did not return variants — check Gemini API key.")

    # 4. Pick best variant
    best = max(variants_data, key=lambda v: v.get("predicted_score", 0))
    variants = [ContentVariant(**v) for v in variants_data]

    # 5. Persist the post (saves best variant as default)
    post_id = str(uuid.uuid4())
    post = Post(
        post_id=post_id,
        user_id=body.user_id,
        topic=topic,
        format=body.format,
        content_body=best.get("body", ""),
        hook=best.get("hook", ""),
        cta=best.get("cta", ""),
        hashtags=best.get("hashtags", []),
        variants=variants_data,
        predicted_score=best.get("predicted_score", 0.0),
        status="draft",
    )
    db.add(post)
    await db.commit()

    return ContentGenerateResponse(
        post_id=post_id,
        topic=topic,
        format=body.format,
        variants=variants,
        best_variant_id=best.get("variant_id", "v1"),
        trend_context=trend_context,
    )


@router.post("/variants", response_model=ContentGenerateResponse)
async def more_variants(body: ContentVariantsRequest, db: AsyncSession = Depends(get_db)):
    """Generate additional variants for an existing draft post."""
    result = await db.execute(select(Post).where(Post.post_id == body.post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(404, "Post not found.")

    user_result = await db.execute(select(User).where(User.user_id == post.user_id))
    user = user_result.scalar_one_or_none()

    raw = await generate_post_variants(
        topic=post.topic,
        niche=user.niche if user else "",
        format_type=post.format,
        tone=user.tone_style if user else "professional",
        target_audience=user.target_audience if user else "",
        num_variants=body.num_variants,
    )
    variants_data = raw.get("variants", [])
    variants = [ContentVariant(**v) for v in variants_data]
    best = max(variants_data, key=lambda v: v.get("predicted_score", 0)) if variants_data else {}

    return ContentGenerateResponse(
        post_id=body.post_id,
        topic=post.topic,
        format=post.format,
        variants=variants,
        best_variant_id=best.get("variant_id", "v1"),
        trend_context="",
    )


@router.get("/user/{user_id}")
async def list_user_posts(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Post).where(Post.user_id == user_id).order_by(Post.created_at.desc())
    )
    posts = result.scalars().all()
    return {"user_id": user_id, "posts": posts}


@router.get("/{post_id}")
async def get_post(post_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Post).where(Post.post_id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(404, "Post not found.")
    return post

"""
LinkedIn Publishing Service
Calls LinkedIn API v2 to publish posts using the user's OAuth access token.
"""
from __future__ import annotations
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models.content import Post
from models.user import User


LINKEDIN_API = "https://api.linkedin.com/v2"


async def _get_linkedin_urn(access_token: str) -> str:
    """Fetch the LinkedIn member URN for the authenticated user."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{LINKEDIN_API}/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        data = resp.json()
        return f"urn:li:person:{data['id']}"


async def publish_to_linkedin(access_token: str, author_urn: str, text: str) -> str:
    """Post to LinkedIn and return the LinkedIn post ID."""
    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{LINKEDIN_API}/ugcPosts",
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            },
        )
        resp.raise_for_status()
        return resp.headers.get("x-restli-id", "unknown")


async def publish_post(post_id: str, user_id: str, db: AsyncSession) -> Post:
    """
    Full publish flow:
    1. Load post + user from DB
    2. Call LinkedIn API
    3. Update post status
    """
    post_result = await db.execute(select(Post).where(Post.post_id == post_id))
    post = post_result.scalar_one_or_none()
    if not post:
        raise ValueError(f"Post {post_id} not found")

    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.linkedin_access_token:
        raise ValueError("User has no LinkedIn access token — connect LinkedIn first.")

    try:
        author_urn = await _get_linkedin_urn(user.linkedin_access_token)
        # Build full post text: hook + body + CTA + hashtags
        full_text = f"{post.hook}\n\n{post.content_body}\n\n{post.cta}\n\n" + " ".join(
            f"#{h}" for h in (post.hashtags or [])
        )
        li_id = await publish_to_linkedin(user.linkedin_access_token, author_urn, full_text)

        await db.execute(
            update(Post)
            .where(Post.post_id == post_id)
            .values(
                linkedin_post_id=li_id,
                status="published",
                published_at=datetime.utcnow(),
            )
        )
    except Exception as exc:
        await db.execute(
            update(Post)
            .where(Post.post_id == post_id)
            .values(status="failed", error_message=str(exc))
        )
        raise
    finally:
        await db.commit()

    result = await db.execute(select(Post).where(Post.post_id == post_id))
    return result.scalar_one()

"""
Analytics Service
Fetches LinkedIn engagement data and computes growth metrics.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from collections import Counter
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.analytics import PostMetrics, GrowthSnapshot
from models.content import Post
from models.user import User


LINKEDIN_API = "https://api.linkedin.com/v2"


# ── LinkedIn data fetcher ──────────────────────────────────────────────────────
async def fetch_post_metrics_from_linkedin(
    linkedin_post_id: str,
    access_token: str,
) -> dict:
    """Pull impression + engagement stats from LinkedIn API."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{LINKEDIN_API}/socialMetadata/(activity~urn%3Ali%3Aactivity%3A{linkedin_post_id})",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "likes": data.get("likesSummary", {}).get("totalLikes", 0),
                    "comments": data.get("commentsSummary", {}).get("totalFirstLevelComments", 0),
                    "shares": data.get("sharesSummary", {}).get("shareCount", 0),
                }
    except Exception:
        pass
    return {"likes": 0, "comments": 0, "shares": 0}


# ── DB helpers ─────────────────────────────────────────────────────────────────
async def upsert_metrics(
    post_id: str,
    user_id: str,
    impressions: int,
    likes: int,
    comments: int,
    shares: int,
    saves: int = 0,
    clicks: int = 0,
    db: AsyncSession = None,
) -> PostMetrics:
    engagement_rate = (
        ((likes + comments + shares + saves + clicks) / impressions * 100)
        if impressions > 0 else 0.0
    )
    virality_score = (shares * 3 + comments * 2 + likes) / max(impressions, 1) * 100

    metrics = PostMetrics(
        post_id=post_id,
        user_id=user_id,
        impressions=impressions,
        likes=likes,
        comments=comments,
        shares=shares,
        saves=saves,
        clicks=clicks,
        engagement_rate=round(engagement_rate, 2),
        virality_score=round(virality_score, 4),
        fetched_at=datetime.utcnow(),
    )
    db.add(metrics)
    await db.commit()
    await db.refresh(metrics)
    return metrics


async def get_post_metrics(post_id: str, db: AsyncSession) -> PostMetrics | None:
    result = await db.execute(
        select(PostMetrics)
        .where(PostMetrics.post_id == post_id)
        .order_by(PostMetrics.fetched_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_engagement_summary(user_id: str, days: int, db: AsyncSession) -> dict:
    since = datetime.utcnow() - timedelta(days=days)

    rows = (
        await db.execute(
            select(PostMetrics, Post.format, Post.scheduled_time)
            .join(Post, PostMetrics.post_id == Post.post_id)
            .where(PostMetrics.user_id == user_id, PostMetrics.fetched_at >= since)
        )
    ).fetchall()

    if not rows:
        return {
            "total_impressions": 0, "total_likes": 0,
            "total_comments": 0, "total_shares": 0,
            "avg_engagement_rate": 0.0,
            "best_format": "N/A",
            "best_posting_day": "Tuesday",
            "best_posting_hour": 8,
            "top_posts": [],
        }

    metrics_list = [r[0] for r in rows]
    format_scores: Counter = Counter()
    day_scores: Counter = Counter()
    hour_scores: Counter = Counter()

    for m, fmt, sched in rows:
        format_scores[fmt or "unknown"] += m.engagement_rate
        if sched:
            day_scores[sched.strftime("%A")] += m.engagement_rate
            hour_scores[sched.hour] += m.engagement_rate

    top_posts = sorted(metrics_list, key=lambda x: x.engagement_rate, reverse=True)[:5]

    return {
        "total_impressions": sum(m.impressions for m in metrics_list),
        "total_likes": sum(m.likes for m in metrics_list),
        "total_comments": sum(m.comments for m in metrics_list),
        "total_shares": sum(m.shares for m in metrics_list),
        "avg_engagement_rate": round(
            sum(m.engagement_rate for m in metrics_list) / len(metrics_list), 2
        ),
        "best_format": format_scores.most_common(1)[0][0] if format_scores else "N/A",
        "best_posting_day": day_scores.most_common(1)[0][0] if day_scores else "Tuesday",
        "best_posting_hour": hour_scores.most_common(1)[0][0] if hour_scores else 8,
        "top_posts": top_posts,
    }


async def get_growth_history(user_id: str, db: AsyncSession) -> list[GrowthSnapshot]:
    result = await db.execute(
        select(GrowthSnapshot)
        .where(GrowthSnapshot.user_id == user_id)
        .order_by(GrowthSnapshot.snapped_at.desc())
        .limit(30)
    )
    return result.scalars().all()

"""
Pydantic schemas — request / response models for every endpoint.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ── Users ─────────────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: str
    name: str
    niche: str
    content_goals: str = ""
    posting_frequency: int = 5
    tone_style: str = "professional"
    target_audience: str = ""


class UserUpdate(BaseModel):
    niche: Optional[str] = None
    content_goals: Optional[str] = None
    posting_frequency: Optional[int] = None
    tone_style: Optional[str] = None
    target_audience: Optional[str] = None
    linkedin_access_token: Optional[str] = None


class UserOut(BaseModel):
    user_id: str
    email: str
    name: str
    niche: str
    content_goals: str
    posting_frequency: int
    tone_style: str
    target_audience: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Content Generation ────────────────────────────────────────────────────────
class ContentGenerateRequest(BaseModel):
    user_id: str
    topic: Optional[str] = None          # if None → system picks from trends
    format: str = Field(
        default="thought_leadership",
        description="thought_leadership | story | insight | hook | carousel"
    )
    num_variants: int = Field(default=3, ge=1, le=5)
    tone_override: Optional[str] = None


class ContentVariant(BaseModel):
    variant_id: str
    hook: str
    body: str
    cta: str
    hashtags: List[str]
    predicted_score: float


class ContentGenerateResponse(BaseModel):
    post_id: str
    topic: str
    format: str
    variants: List[ContentVariant]
    best_variant_id: str
    trend_context: str


class ContentVariantsRequest(BaseModel):
    post_id: str
    num_variants: int = 3


# ── Scheduling ────────────────────────────────────────────────────────────────
class SchedulePostRequest(BaseModel):
    post_id: str
    user_id: str
    variant_id: str
    scheduled_time: Optional[datetime] = None   # None → AI picks optimal time


class ScheduleUpdateRequest(BaseModel):
    scheduled_time: datetime


class ScheduledPostOut(BaseModel):
    post_id: str
    topic: str
    format: str
    scheduled_time: datetime
    predicted_score: float
    status: str

    class Config:
        from_attributes = True


class CalendarResponse(BaseModel):
    user_id: str
    posts: List[ScheduledPostOut]


# ── Publishing ────────────────────────────────────────────────────────────────
class PublishRequest(BaseModel):
    post_id: str
    user_id: str


class PublishStatusOut(BaseModel):
    post_id: str
    status: str
    linkedin_post_id: Optional[str]
    published_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


# ── Analytics ─────────────────────────────────────────────────────────────────
class PostMetricsOut(BaseModel):
    post_id: str
    impressions: int
    likes: int
    comments: int
    shares: int
    saves: int
    clicks: int
    engagement_rate: float
    virality_score: float
    fetched_at: datetime

    class Config:
        from_attributes = True


class GrowthOut(BaseModel):
    user_id: str
    follower_count: int
    connection_count: int
    profile_views: int
    snapped_at: datetime

    class Config:
        from_attributes = True


class EngagementSummary(BaseModel):
    user_id: str
    period_days: int
    total_impressions: int
    total_likes: int
    total_comments: int
    total_shares: int
    avg_engagement_rate: float
    best_format: str
    best_posting_day: str
    best_posting_hour: int
    top_posts: List[PostMetricsOut]


# ── Strategy ──────────────────────────────────────────────────────────────────
class StrategyRecommendation(BaseModel):
    user_id: str
    recommended_topics: List[str]
    recommended_formats: List[str]
    best_times: List[str]
    tone_suggestions: str
    content_calendar_preview: List[dict]
    insights: str


class StrategyUpdateRequest(BaseModel):
    user_id: str
    approved_topics: Optional[List[str]] = None
    preferred_formats: Optional[List[str]] = None
    preferred_times: Optional[List[str]] = None
    tone_feedback: Optional[str] = None

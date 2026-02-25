"""Analytics ORM model — tracks post performance metrics."""
from datetime import datetime
from sqlalchemy import String, DateTime, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from db.database import Base


class PostMetrics(Base):
    __tablename__ = "post_metrics"

    id: Mapped[int]              = mapped_column(Integer, primary_key=True, autoincrement=True)
    post_id: Mapped[str]         = mapped_column(String, ForeignKey("posts.post_id"))
    user_id: Mapped[str]         = mapped_column(String, ForeignKey("users.user_id"))

    # LinkedIn engagement data
    impressions: Mapped[int]     = mapped_column(Integer, default=0)
    likes: Mapped[int]           = mapped_column(Integer, default=0)
    comments: Mapped[int]        = mapped_column(Integer, default=0)
    shares: Mapped[int]          = mapped_column(Integer, default=0)
    saves: Mapped[int]           = mapped_column(Integer, default=0)
    clicks: Mapped[int]          = mapped_column(Integer, default=0)
    profile_views: Mapped[int]   = mapped_column(Integer, default=0)
    followers_gained: Mapped[int] = mapped_column(Integer, default=0)

    # Computed
    engagement_rate: Mapped[float] = mapped_column(Float, default=0.0)
    virality_score: Mapped[float]  = mapped_column(Float, default=0.0)

    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GrowthSnapshot(Base):
    __tablename__ = "growth_snapshots"

    id: Mapped[int]              = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str]         = mapped_column(String, ForeignKey("users.user_id"))
    follower_count: Mapped[int]  = mapped_column(Integer, default=0)
    connection_count: Mapped[int] = mapped_column(Integer, default=0)
    profile_views: Mapped[int]   = mapped_column(Integer, default=0)
    snapped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

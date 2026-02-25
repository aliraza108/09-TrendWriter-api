"""Content / Post ORM model."""
from datetime import datetime
from sqlalchemy import String, DateTime, Float, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from db.database import Base


class Post(Base):
    __tablename__ = "posts"

    post_id: Mapped[str]         = mapped_column(String, primary_key=True)
    user_id: Mapped[str]         = mapped_column(String, ForeignKey("users.user_id"))
    linkedin_post_id: Mapped[str] = mapped_column(String, nullable=True)

    # Content
    topic: Mapped[str]           = mapped_column(String)
    format: Mapped[str]          = mapped_column(String)          # thought_leadership | story | insight | hook | carousel
    content_body: Mapped[str]    = mapped_column(String)
    hook: Mapped[str]            = mapped_column(String, default="")
    cta: Mapped[str]             = mapped_column(String, default="")
    hashtags: Mapped[list]       = mapped_column(JSON, default=list)
    variants: Mapped[list]       = mapped_column(JSON, default=list)

    # Scheduling
    scheduled_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    predicted_score: Mapped[float]   = mapped_column(Float, default=0.0)

    # Status: draft | scheduled | published | failed
    status: Mapped[str]          = mapped_column(String, default="draft")
    error_message: Mapped[str]   = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

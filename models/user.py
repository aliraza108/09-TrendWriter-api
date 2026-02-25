"""User ORM model."""
from datetime import datetime
from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from db.database import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str]       = mapped_column(String, primary_key=True)
    linkedin_id: Mapped[str]   = mapped_column(String, unique=True, nullable=True)
    email: Mapped[str]         = mapped_column(String, unique=True)
    name: Mapped[str]          = mapped_column(String)
    niche: Mapped[str]         = mapped_column(String, default="")
    content_goals: Mapped[str] = mapped_column(String, default="")
    posting_frequency: Mapped[int] = mapped_column(default=5)   # posts per week
    tone_style: Mapped[str]    = mapped_column(String, default="professional")
    target_audience: Mapped[str] = mapped_column(String, default="")
    linkedin_access_token: Mapped[str] = mapped_column(String, nullable=True)
    preferences: Mapped[dict]  = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

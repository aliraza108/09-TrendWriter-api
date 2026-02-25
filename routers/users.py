"""Users router — CRUD for user accounts."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from db.database import get_db
from models.user import User
from schemas.schemas import UserCreate, UserUpdate, UserOut

router = APIRouter()


@router.post("/", response_model=UserOut, status_code=201)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email already registered.")
    user = User(user_id=str(uuid.uuid4()), **body.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found.")
    return user


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(user_id: str, body: UserUpdate, db: AsyncSession = Depends(get_db)):
    values = {k: v for k, v in body.model_dump().items() if v is not None}
    if not values:
        raise HTTPException(400, "No fields to update.")
    await db.execute(update(User).where(User.user_id == user_id).values(**values))
    await db.commit()
    result = await db.execute(select(User).where(User.user_id == user_id))
    return result.scalar_one_or_none()

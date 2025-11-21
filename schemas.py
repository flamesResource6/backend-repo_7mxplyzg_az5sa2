"""
Database Schemas for BetterMann (India-first online therapy platform)

Each Pydantic model maps to a MongoDB collection using the class name in lowercase.
Example: class User -> "user" collection
"""

from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

# -------- Core Auth & Profiles --------
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password_hash: str = Field(..., description="Hashed password")
    phone: Optional[str] = Field(None, description="Phone number (optional)")
    language: Optional[str] = Field("en", description="Preferred language code: en, hi, ta, bn")
    city: Optional[str] = Field(None, description="City of residence")
    is_active: bool = Field(True)
    role: str = Field("user", description="user | therapist | admin")

class Therapist(BaseModel):
    name: str
    email: EmailStr
    bio: Optional[str] = None
    education: Optional[str] = None
    specialties: List[str] = Field(default_factory=list, description="e.g., anxiety, depression, couples, student stress")
    experience_years: int = Field(0, ge=0)
    languages: List[str] = Field(default_factory=lambda: ["English"])
    gender: Optional[str] = Field(None, description="male | female | non-binary | prefer-not")
    city: Optional[str] = None
    price_per_week_inr: int = Field(0, ge=0)
    rating: float = Field(4.8, ge=0, le=5)
    photo_url: Optional[str] = None
    slots: List[str] = Field(default_factory=list, description="Available slot strings IST, e.g., 'Mon 7pm'")

class Review(BaseModel):
    user_name: str
    rating: int = Field(..., ge=1, le=5)
    comment: str
    city: Optional[str] = None
    created_at: Optional[datetime] = None

class BlogPost(BaseModel):
    title: str
    slug: str
    excerpt: str
    content: str
    tags: List[str] = Field(default_factory=list)
    cover_image: Optional[str] = None
    published_at: Optional[datetime] = None

class FAQ(BaseModel):
    question: str
    answer: str
    category: Optional[str] = None

class Plan(BaseModel):
    name: str
    price_inr: int
    period: str = Field("per week")
    features: List[str] = Field(default_factory=list)

class ContactMessage(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

class MatchRequest(BaseModel):
    age: Optional[int] = None
    concerns: List[str] = Field(default_factory=list)
    language: Optional[str] = None
    gender_preference: Optional[str] = None
    city: Optional[str] = None

class Session(BaseModel):
    user_id: str
    therapist_id: str
    mode: str = Field("chat", description="chat | video | phone")
    scheduled_for: Optional[datetime] = None
    status: str = Field("scheduled", description="scheduled | completed | cancelled")

# Note: The Flames database viewer reads these to help manage data.

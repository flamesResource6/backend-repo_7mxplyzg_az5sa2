import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Therapist, Review, BlogPost, FAQ, Plan, ContactMessage, MatchRequest, Session

app = FastAPI(title="BetterMann API", description="India-first online therapy platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "BetterMann API running"}

# ---------- Auth (simple demo: email-only signup/login with no real password for now) ----------
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    language: Optional[str] = "en"

@app.post("/api/auth/signup")
def signup(req: SignupRequest):
    existing = db["user"].find_one({"email": req.email}) if db else None
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(name=req.name, email=req.email, password_hash=f"hash:{req.password}", language=req.language)
    user_id = create_document("user", user)
    return {"id": user_id, "name": user.name, "email": user.email}

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.post("/api/auth/login")
def login(req: LoginRequest):
    u = db["user"].find_one({"email": req.email}) if db else None
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    # Demo check
    if not str(u.get("password_hash", "")).endswith(req.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"id": str(u.get("_id")), "name": u.get("name"), "email": u.get("email")}

# ---------- Therapist directory ----------
@app.get("/api/therapists")
def list_therapists(language: Optional[str] = None, city: Optional[str] = None, q: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    query = {}
    if language:
        query["languages"] = {"$regex": language, "$options": "i"}
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"specialties": {"$elemMatch": {"$regex": q, "$options": "i"}}},
        ]
    items = get_documents("therapist", query, limit=50)
    for it in items:
        it["id"] = str(it.pop("_id"))
    return {"items": items}

@app.post("/api/therapists")
def add_therapist(data: Therapist):
    tid = create_document("therapist", data)
    return {"id": tid}

# ---------- Matching ----------
@app.post("/api/match")
def match(req: MatchRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    query = {}
    if req.language:
        query["languages"] = {"$regex": req.language, "$options": "i"}
    if req.city:
        query["city"] = {"$regex": req.city, "$options": "i"}
    if req.concerns:
        query["specialties"] = {"$in": req.concerns}
    therapists = list(db["therapist"].find(query).limit(10))
    results = []
    for t in therapists:
        results.append({
            "id": str(t["_id"]),
            "name": t.get("name"),
            "languages": t.get("languages", []),
            "specialties": t.get("specialties", []),
            "city": t.get("city"),
            "rating": t.get("rating", 4.8),
            "price_per_week_inr": t.get("price_per_week_inr", 0),
            "photo_url": t.get("photo_url"),
        })
    return {"matches": results}

# ---------- Plans ----------
@app.get("/api/plans")
def plans():
    data = [
        {"name": "Starter", "price_inr": 799, "period": "per week", "features": ["Unlimited chat", "1 live session"]},
        {"name": "Standard", "price_inr": 1399, "period": "per week", "features": ["Unlimited chat", "2 live sessions", "Priority support"]},
        {"name": "Premium", "price_inr": 2199, "period": "per week", "features": ["Unlimited chat", "4 live sessions", "Dedicated care manager"]},
    ]
    return {"items": data}

# ---------- Reviews ----------
@app.get("/api/reviews")
def reviews():
    items = get_documents("review", {}, limit=50) if db else []
    for it in items:
        it["id"] = str(it.pop("_id"))
    return {"items": items}

@app.post("/api/reviews")
def add_review(data: Review):
    rid = create_document("review", data)
    return {"id": rid}

# ---------- Blog ----------
@app.get("/api/blog")
def blog_list(tag: Optional[str] = None):
    query = {"tags": tag} if tag else {}
    items = get_documents("blogpost", query, limit=50) if db else []
    for it in items:
        it["id"] = str(it.pop("_id"))
    return {"items": items}

@app.post("/api/blog")
def add_blog(post: BlogPost):
    bid = create_document("blogpost", post)
    return {"id": bid}

@app.get("/api/blog/{slug}")
def blog_detail(slug: str):
    post = db["blogpost"].find_one({"slug": slug}) if db else None
    if not post:
        raise HTTPException(status_code=404, detail="Not found")
    post["id"] = str(post.pop("_id"))
    return post

# ---------- FAQ ----------
@app.get("/api/faq")
def faq_list():
    items = get_documents("faq", {}, limit=100) if db else []
    for it in items:
        it["id"] = str(it.pop("_id"))
    return {"items": items}

@app.post("/api/faq")
def add_faq(item: FAQ):
    fid = create_document("faq", item)
    return {"id": fid}

# ---------- Contact ----------
@app.post("/api/contact")
def contact(msg: ContactMessage):
    cid = create_document("contactmessage", msg)
    return {"id": cid, "status": "received"}

# ---------- Sessions (placeholder scheduling) ----------
@app.post("/api/sessions")
def create_session(s: Session):
    sid = create_document("session", s)
    return {"id": sid}

# ---------- Health & Test ----------
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:20]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

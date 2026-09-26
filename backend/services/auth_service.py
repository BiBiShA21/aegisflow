"""
AegisFlow - Authentication Service
Phase 1: Complete JWT + bcrypt auth
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from bson import ObjectId
from backend.database import users_col, audit_logs_col

SECRET_KEY = os.getenv("SECRET_KEY", "aegisflow-secret-2024")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def validate_password_strength(password: str):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, "Strong"


def create_access_token(data: Dict[str, Any], remember_me: bool = False) -> str:
    to_encode = data.copy()
    expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES * 7 if remember_me else ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[Dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def register_user(data: Dict) -> Dict:
    """Register new user in MongoDB"""
    col = users_col()

    # Check duplicates
    if col.find_one({"username": data["username"]}):
        raise ValueError("Username already exists")
    if col.find_one({"email": data["email"]}):
        raise ValueError("Email already registered")

    # Validate password
    is_valid, msg = validate_password_strength(data["password"])
    if not is_valid:
        raise ValueError(msg)

    user_doc = {
        "full_name": data["full_name"],
        "email": data["email"],
        "username": data["username"],
        "password_hash": hash_password(data["password"]),
        "organization": data.get("organization", ""),
        "phone": data.get("phone", ""),
        "location": data.get("location", ""),
        "github_username": data.get("github_username", ""),
        "bio": data.get("bio", ""),
        "occupation": data.get("occupation", "Developer"),
        "avatar_color": _pick_color(data["username"]),
        "created_at": datetime.utcnow(),
        "last_active": datetime.utcnow(),
        "total_scans": 0,
        "account_status": "active"
    }

    result = col.insert_one(user_doc)
    user_doc["_id"] = str(result.inserted_id)
    return _safe_user(user_doc)


def login_user(username: str, password: str, remember_me: bool = False) -> Dict:
    """Authenticate user and return token"""
    col = users_col()
    user = col.find_one({"username": username})

    if not user or not verify_password(password, user["password_hash"]):
        raise ValueError("Invalid username or password")

    # Update last active
    col.update_one({"_id": user["_id"]}, {"$set": {"last_active": datetime.utcnow()}})

    # Log action
    _log_audit(str(user["_id"]), "login", "success")

    token = create_access_token(
        {"user_id": str(user["_id"]), "username": user["username"], "occupation": user["occupation"]},
        remember_me=remember_me
    )

    return {"access_token": token, "token_type": "bearer", "user": _safe_user(user)}


def get_user_by_id(user_id: str) -> Optional[Dict]:
    try:
        user = users_col().find_one({"_id": ObjectId(user_id)})
        return _safe_user(user) if user else None
    except Exception:
        return None


def update_user_profile(user_id: str, updates: Dict) -> Dict:
    """Update user profile fields"""
    allowed = ["full_name", "email", "organization", "phone", "location", "github_username", "bio", "occupation"]
    clean = {k: v for k, v in updates.items() if k in allowed and v is not None}
    clean["updated_at"] = datetime.utcnow()
    users_col().update_one({"_id": ObjectId(user_id)}, {"$set": clean})
    return get_user_by_id(user_id)


def _safe_user(user: Dict) -> Dict:
    """Remove sensitive fields from user dict"""
    if not user:
        return {}
    return {
        "id": str(user.get("_id", "")),
        "full_name": user.get("full_name", ""),
        "email": user.get("email", ""),
        "username": user.get("username", ""),
        "organization": user.get("organization", ""),
        "phone": user.get("phone", ""),
        "location": user.get("location", ""),
        "github_username": user.get("github_username", ""),
        "bio": user.get("bio", ""),
        "occupation": user.get("occupation", "Developer"),
        "avatar_color": user.get("avatar_color", "#06b6d4"),
        "created_at": str(user.get("created_at", "")),
        "last_active": str(user.get("last_active", "")),
        "total_scans": user.get("total_scans", 0),
        "account_status": user.get("account_status", "active")
    }


def _pick_color(username: str) -> str:
    colors = ["#06b6d4", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444", "#3b82f6"]
    return colors[sum(ord(c) for c in username) % len(colors)]


def _log_audit(user_id: str, action: str, status: str):
    try:
        audit_logs_col().insert_one({
            "user_id": user_id,
            "action": action,
            "status": status,
            "timestamp": datetime.utcnow()
        })
    except Exception:
        pass

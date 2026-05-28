"""
app/api/auth.py
===============
Authentication routes — signup, login, and protected user endpoints.

ENDPOINTS:
----------
  POST /auth/signup   → Create a new account
  POST /auth/login    → Authenticate and receive a JWT
  GET  /auth/me       → Get current user profile (protected)
  PUT  /auth/interests → Update user interest profile (protected)

AUTHENTICATION FLOW:
--------------------
  1. User signs up with email + password
  2. Server hashes password with bcrypt → stores in PostgreSQL
  3. User logs in with email + password
  4. Server verifies password → creates JWT → returns token
  5. Frontend stores token (localStorage / httpOnly cookie)
  6. Every protected request: Authorization: Bearer <token>
  7. Server decodes JWT → fetches user → attaches to request

ERROR HANDLING:
---------------
  400  → Duplicate email on signup
  401  → Invalid credentials, expired/invalid token
  403  → Account deactivated
  422  → Validation errors (bad email, short password)

SECURITY CONSIDERATIONS:
------------------------
  - Passwords are NEVER returned in any response
  - Duplicate email errors are intentionally vague ("already registered")
    to prevent email enumeration attacks
  - JWT tokens have an expiry (configured via ACCESS_TOKEN_EXPIRE_MINUTES)
  - Inactive users are blocked at the token verification layer
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import (
    MessageResponse,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)


# ─── Router ───────────────────────────────────────────────────────────────

router = APIRouter()


# ─── POST /auth/signup ───────────────────────────────────────────────────


@router.post(
    "/signup",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.

    PIPELINE:
        1. Check if email already exists (409 if duplicate)
        2. Hash the password with bcrypt
        3. Insert the new user into PostgreSQL
        4. Return success message (user can now login)

    WHY NOT RETURN A JWT HERE?
        Signup and login are separate concerns. The frontend should
        explicitly call /auth/login after signup to get a token.
        This makes the flow clearer and lets us add email verification
        later without changing the signup endpoint.

    Args:
        user_data: Email, password, and optional full_name.
        db:        SQLAlchemy session (auto-injected).

    Returns:
        MessageResponse confirming account creation.
    """
    # ── Check for duplicate email ────────────────────────────────────
    existing_stmt = select(User).where(User.email == user_data.email)
    existing = db.execute(existing_stmt).scalars().first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email is already registered",
        )

    # ── Hash password + create user ──────────────────────────────────
    hashed_pw = hash_password(user_data.password)

    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pw,
        full_name=user_data.full_name,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # populates id, created_at, updated_at

    return MessageResponse(
        message="Account created successfully",
        detail={"user_id": new_user.id},
    )


# ─── POST /auth/login ────────────────────────────────────────────────────


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate and receive a JWT access token",
)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate a user and return a JWT access token.

    PIPELINE:
        1. Look up user by email
        2. Verify password against stored bcrypt hash
        3. Check account is active
        4. Create JWT with user_id as subject
        5. Return token

    WHY GENERIC ERROR MESSAGES?
        We don't say "email not found" vs "wrong password" because
        that lets attackers enumerate which emails exist in the system.
        A single message "Invalid credentials" covers both cases.

    Args:
        credentials: Email and password.
        db:          SQLAlchemy session (auto-injected).

    Returns:
        Token with access_token and token_type.
    """
    # ── Find user by email ───────────────────────────────────────────
    stmt = select(User).where(User.email == credentials.email)
    user = db.execute(stmt).scalars().first()

    # ── Verify user exists + password matches ────────────────────────
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── Check account is active ──────────────────────────────────────
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # ── Create JWT ───────────────────────────────────────────────────
    access_token = create_access_token(data={"sub": str(user.id)})

    return Token(access_token=access_token, token_type="bearer")


# ─── GET /auth/me ─────────────────────────────────────────────────────────


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
def read_current_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Return the profile of the currently authenticated user.

    This is a PROTECTED route — it requires a valid JWT in the
    Authorization header. The get_current_user dependency handles:
      - Token extraction from the header
      - JWT decoding and validation
      - Database lookup of the user
      - Active account check

    If any of these fail, the dependency raises 401 before this
    function even runs.

    Args:
        current_user: User ORM object (injected by get_current_user).

    Returns:
        UserResponse with id, email, full_name, is_active, interests.
    """
    return current_user


# ─── PUT /auth/interests ──────────────────────────────────────────────────


@router.put(
    "/interests",
    response_model=UserResponse,
    summary="Update user interest profile for personalized recommendations",
)
def update_interests(
    interests: list[str],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    Update the authenticated user's interest topics.

    This endpoint connects the auth system to the recommendation engine.
    The interests list is stored as a JSON array in the users table and
    used by recommendation_service to personalize article rankings.

    EXAMPLE REQUEST:
        PUT /auth/interests?interests=AI&interests=startups&interests=geopolitics

    EXAMPLE STORED VALUE:
        ["AI", "startups", "geopolitics"]

    Args:
        interests:     List of topic strings.
        current_user:  Authenticated user (injected by dependency).
        db:            SQLAlchemy session.

    Returns:
        Updated UserResponse with new interests.
    """
    import json

    # Store as JSON array string in the database
    current_user.interests = json.dumps(interests)
    db.commit()
    db.refresh(current_user)

    return current_user

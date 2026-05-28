"""
app/schemas/auth.py
===================
Pydantic schemas for authentication — request validation + response shaping.

WHY SEPARATE SCHEMAS INSTEAD OF RETURNING THE ORM MODEL DIRECTLY?
------------------------------------------------------------------
  1. SECURITY:  The User ORM model has hashed_password. If you return it
     directly, the password hash leaks to the frontend. Schemas let you
     explicitly control which fields are visible.

  2. VALIDATION: Schemas enforce input rules (email format, min password
     length) BEFORE your code touches the database.

  3. DOCUMENTATION: FastAPI auto-generates Swagger docs from schemas.
     Clean schemas = clean API docs.

  4. VERSIONING:  When the API changes, you update schemas without
     touching the database model.

SCHEMA HIERARCHY:
-----------------
  UserCreate   → POST /auth/signup   (email + password + name)
  UserLogin    → POST /auth/login    (email + password)
  UserResponse → GET /auth/me        (id, email, name — NO password)
  Token        → POST /auth/login    (access_token + token_type)
  TokenData    → Internal JWT decode (user_id)

DESIGN PHILOSOPHY:
------------------
  - Every field has a Field() with description for Swagger docs
  - Password has min_length=8 — anything shorter is insecure
  - Email uses Pydantic's EmailStr for format validation
  - Optional fields use None defaults so the API is flexible
"""

from typing import Any

from pydantic import BaseModel, EmailStr, Field


# ─── Request Schemas ──────────────────────────────────────────────────────


class UserCreate(BaseModel):
    """
    Payload for creating a new user account.

    Sent to: POST /auth/signup

    Validation rules:
        - email:    Must be a valid email format (Pydantic EmailStr)
        - password: Minimum 8 characters (enforced before hashing)
        - full_name: Optional display name
    """

    email: EmailStr = Field(
        ...,
        description="User's email address — used as login identifier",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=72,
        description="Plaintext password (min 8 chars) — hashed before storage",
    )
    full_name: str | None = Field(
        default=None,
        max_length=150,
        description="Display name — optional at signup",
    )


class UserLogin(BaseModel):
    """
    Payload for authenticating an existing user.

    Sent to: POST /auth/login

    Returns: Token (access_token + token_type) on success.
    """

    email: EmailStr = Field(
        ...,
        description="Registered email address",
    )
    password: str = Field(
        ...,
        min_length=1,
        description="Account password",
    )


# ─── Response Schemas ─────────────────────────────────────────────────────


class UserResponse(BaseModel):
    """
    User data returned in API responses.

    IMPORTANT: This schema intentionally EXCLUDES hashed_password.
    Never expose password hashes in any API response, even internally.
    If you need to debug auth issues, check the database directly.

    model_config with from_attributes=True lets Pydantic read data
    directly from SQLAlchemy ORM objects (User model instances).
    Without this, you'd have to manually convert ORM → dict.
    """

    id: int = Field(..., description="Unique user ID")
    email: str = Field(..., description="User email address")
    full_name: str | None = Field(None, description="Display name")
    is_active: bool = Field(True, description="Account active status")
    interests: str | None = Field(
        None,
        description='JSON array of interest topics, e.g. ["AI", "startups"]',
    )

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """
    JWT token response returned after successful login.

    This is what the frontend stores and sends in the Authorization header:
        Authorization: Bearer <access_token>
    """

    access_token: str = Field(
        ..., description="JWT access token for authenticated requests"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type — always 'bearer' for JWT",
    )


class TokenData(BaseModel):
    """
    Internal schema for decoded JWT payload.

    Used by get_current_user() to extract the user_id from a token.
    Not returned in any API response — purely internal.
    """

    user_id: int | None = Field(
        None, description="User ID extracted from JWT subject claim"
    )


# ─── Utility Schemas ──────────────────────────────────────────────────────


class MessageResponse(BaseModel):
    """
    Generic message response for simple endpoints.

    Used for signup confirmation, logout, and other non-data responses.
    """

    message: str = Field(..., description="Human-readable status message")
    detail: dict[str, Any] | None = Field(
        None, description="Optional extra data"
    )
"""
app/core/security.py
====================
Security utilities — password hashing, JWT creation, and token verification.

THIS FILE IS THE CRYPTOGRAPHIC CORE OF YOUR AUTH SYSTEM.
It handles three concerns:

  1. PASSWORD HASHING
     Why: Storing plain-text passwords means a database leak exposes every
     user's credentials. bcrypt is the industry standard — it's slow by
     design (makes brute-force attacks impractical) and auto-salts each hash.

  2. JWT TOKEN CREATION
     Why: After login, the frontend needs a credential to send with every
     request. A JWT encodes {user_id, expiry} into a tamper-proof string
     signed with your SECRET_KEY. The server can verify it without a
     database lookup — stateless authentication.

  3. TOKEN VERIFICATION + USER RESOLUTION
     Why: Protected routes need to know WHO is making the request. The
     get_current_user dependency extracts the token from the Authorization
     header, decodes it, and fetches the user from the database.

SECURITY NOTES:
---------------
  - SECRET_KEY must be a long, random string. Never commit it to git.
  - ACCESS_TOKEN_EXPIRE_MINUTES controls how long a login lasts.
    Shorter = more secure, longer = better UX. 60 min is a good balance.
  - bcrypt rounds are set to 12 (passlib default). Higher = slower hashes
    = more secure but longer login times.
  - The JWT algorithm is HS256 (HMAC-SHA256). This is the most widely
    supported and recommended for symmetric-key JWTs.

IMPORT CONTRACT:
----------------
  Route handlers import:
      get_current_user    — FastAPI dependency for protected routes
      create_access_token — used by login endpoint only
  Config import:
      from app.core.config import settings
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import TokenData


# ─── Password Hashing ─────────────────────────────────────────────────────
# CryptContext wraps passlib's bcrypt implementation.
#
# deprecated="auto" means passlib will automatically upgrade hashes
# to the latest scheme when a user logs in. If you ever switch from
# bcrypt to argon2, existing users get upgraded transparently.

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    The hash includes an auto-generated salt, so the same password
    produces a different hash every time. This prevents rainbow-table
    attacks and makes duplicate-password detection impossible.

    Args:
        plain_password: The user's chosen password (already validated by schema).

    Returns:
        bcrypt hash string, e.g. "$2b$12$N9qo8uLOickgx2ZMRZoMye..."
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain-text password matches the stored bcrypt hash.

    This is the function called during login. It runs the same bcrypt
    computation on the input and compares it to the stored hash.

    WHY NOT just compare strings?
        bcrypt hashes include a salt. The same password "hello123" hashes
        to a different string each time. You MUST use verify_password()
        — string equality will always fail.

    Args:
        plain_password:  The password the user typed in the login form.
        hashed_password: The bcrypt hash stored in the database.

    Returns:
        True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ─── JWT Token ─────────────────────────────────────────────────────────────
# JSON Web Tokens are the standard for stateless API authentication.
#
# STRUCTURE: header.payload.signature
#   header:    {"alg": "HS256", "typ": "JWT"}
#   payload:   {"sub": "42", "exp": 1700000000}
#   signature: HMAC-SHA256(header + "." + payload, SECRET_KEY)
#
# The signature ensures the token hasn't been tampered with.
# Anyone can DECODE a JWT (it's just base64), but only the server
# can VERIFY it (requires the SECRET_KEY).

# OAuth2 scheme tells FastAPI to look for a Bearer token in the
# Authorization header. The tokenUrl points to the login endpoint
# so Swagger UI can show a "Try it out" login form.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=True,
)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a signed JWT access token.

    The token encodes the user's ID in the "sub" (subject) claim and
    an expiration timestamp in the "exp" claim. After encoding, the
    token is signed with your SECRET_KEY using HS256.

    WHY "sub" FOR USER ID?
        "sub" (subject) is the standard JWT claim for identifying
        the principal (the user). Following the spec means your tokens
        work with any JWT library in any language.

    WHY NOT STORE ROLES/PERMISSIONS IN THE TOKEN?
        Tokens can't be revoked — they're valid until expiry. If you
        store "role: admin" in the token and later demote the user,
        their old token still says admin. Always look up current
        permissions from the database.

    Args:
        data:          Dict to encode. Must include {"sub": str(user_id)}.
        expires_delta: Custom expiry duration. Falls back to settings.

    Returns:
        Encoded JWT string, e.g. "eyJhbGciOiJIUzI1NiIs..."
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """
    Decode and validate a JWT access token.

    This function:
      1. Decodes the JWT using the SECRET_KEY
      2. Verifies the signature (tamper detection)
      3. Checks the "exp" claim (expiry)
      4. Extracts the user_id from the "sub" claim

    If the token is expired, tampered with, or malformed, this raises
    an appropriate exception that get_current_user() converts to 401.

    Args:
        token: The JWT string from the Authorization header.

    Returns:
        TokenData with user_id extracted from the token.

    Raises:
        InvalidTokenError: Token is malformed or signature doesn't match.
        ExpiredSignatureError: Token has passed its "exp" timestamp.
    """
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    user_id_raw = payload.get("sub")
    if user_id_raw is None:
        raise InvalidTokenError("Token missing 'sub' claim")

    try:
        user_id = int(user_id_raw)
    except (ValueError, TypeError):
        raise InvalidTokenError("Token 'sub' claim is not a valid user ID")

    return TokenData(user_id=user_id)


# ─── Current User Dependency ──────────────────────────────────────────────
# This is the function you inject into protected routes with Depends().

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    FastAPI dependency that resolves the authenticated user from a JWT.

    HOW IT WORKS:
        1. FastAPI extracts the Bearer token from the Authorization header
           (via oauth2_scheme)
        2. Decodes the JWT → gets user_id
        3. Fetches the user from PostgreSQL
        4. Checks is_active (soft-deleted accounts can't authenticate)
        5. Returns the User ORM object for the route handler to use

    USAGE IN ROUTE HANDLERS:
        @router.get("/me")
        def read_current_user(current_user: User = Depends(get_current_user)):
            return current_user

    ERROR RESPONSES:
        401 Unauthorized — missing token, expired token, invalid signature,
                           user not found, or account deactivated

    Args:
        token: JWT string (injected by oauth2_scheme).
        db:    SQLAlchemy session (injected by get_db).

    Returns:
        The authenticated User ORM object.

    Raises:
        HTTPException 401: On any authentication failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token_data = decode_access_token(token)
    except InvalidTokenError:
        raise credentials_exception

    if token_data.user_id is None:
        raise credentials_exception

    # Fetch user from database
    stmt = select(User).where(User.id == token_data.user_id)
    result = db.execute(stmt)
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    return user

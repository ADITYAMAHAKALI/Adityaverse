from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from jose import JWTError
import uuid

from backend.db.session import get_db
from backend.db.models.user import User
from backend.schemas.auth import UserCreate, Token
from backend.utils.security import hash_password, verify_password
from backend.utils.jwt import create_access_token, decode_access_token
from backend.core.oauth import oauth
from backend.core.config import settings
from backend.core.logger import logger  # ← import your logger

router = APIRouter()

# ───────────────────────── Local credentials ──────────────────────────
@router.post("/register", response_model=Token)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Register attempt for email={user_in.email}")
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        logger.warning(f"Registration failed: email already registered: {user_in.email}")
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        id=str(uuid.uuid4()),
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"New user created id={new_user.id}")

    token = create_access_token({"sub": new_user.id})
    logger.debug(f"Issued JWT for user_id={new_user.id}")
    return {"access_token": token}


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    logger.info(f"Login attempt for email={form_data.username}")
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        logger.warning(f"Login failed: no such user {form_data.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login failed: wrong password for {form_data.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": user.id})
    logger.debug(f"Login success: user_id={user.id}, issued JWT")
    return {"access_token": token}


# ───────────────────────── Google OAuth flow ───────────────────────────
@router.get("/google/login")
async def google_login(request: Request):
    logger.info("Starting Google OAuth flow")
    redirect_uri = request.url_for("google_callback")
    logger.debug(f"Redirecting to Google with callback={redirect_uri}")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    logger.info("Google OAuth callback received")
    token_data = await oauth.google.authorize_access_token(request)
    logger.debug(f"Token data from Google: {token_data}")
    user_info = await oauth.google.parse_id_token(request, token_data)
    email = user_info.get("email")
    logger.info(f"Google user info parsed email={email}")

    # Upsert user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            hashed_password=None,
            role="researcher",
            full_name=user_info.get("name"),
            avatar_url=user_info.get("picture"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created new OAuth user id={user.id}")

    else:
        logger.info(f"Existing OAuth user id={user.id}")

    jwt_token = create_access_token({"sub": user.id})
    logger.debug(f"Issued JWT for OAuth user_id={user.id}")
    return RedirectResponse(url=f"/oauth-success?token={jwt_token}")


# ───────────────────────── Dependency for protected APIs ───────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    logger.debug("Authenticating request with JWT")
    credentials_exception = HTTPException(
        status_code=401, detail="Could not validate credentials"
    )
    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        logger.debug(f"JWT payload sub={user_id}")
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"JWT valid but no user found id={user_id}")
        raise credentials_exception

    logger.debug(f"Authenticated user id={user.id}, email={user.email}")
    return user

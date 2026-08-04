from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.core.logging_config import logger

# ── bcrypt / passlib compatibility fix ────────────────────────────────────
# passlib 1.7.4 tries to read bcrypt.__about__.__version__ but bcrypt >= 4.x
# removed the __about__ module.  The error is caught internally by passlib
# ("(trapped) error reading bcrypt version") so hashing still works, but it
# spams the logs.  Inject a shim so passlib finds the version it expects.
import bcrypt as _bcrypt_module  # noqa: E402

if not hasattr(_bcrypt_module, "__about__"):
    class _BcryptAbout:
        __version__ = _bcrypt_module.__version__

    _bcrypt_module.__about__ = _BcryptAbout()
# ──────────────────────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    result = pwd_context.verify(plain_password, hashed_password)
    if not result:
        logger.warning("Password verification failed")
    return result


def create_access_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    logger.debug("Access token created for sub=%s", data.get("sub"))
    return token


def create_refresh_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    logger.debug("Refresh token created for sub=%s", data.get("sub"))
    return token


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning("Token decode failed: %s", e)
        return None

from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.services.settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, AUTH_REQUIRED
from fastapi import Request

# OAuth2
# auto_error=False permet de ne pas lever une erreur automatique si l'entête Authorization est absent
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Fake user (MVP only)
fake_user = {
    "username": "admin",
    "hashed_password": pwd_context.hash("admin123")
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str) -> bool:
    return (
        username == fake_user["username"]
        and verify_password(password, fake_user["hashed_password"])
    )

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_user_if_required(token: str | None = Depends(oauth2_scheme)) -> str:
    """Retourne un user si AUTH_REQUIRED=true, sinon bypass.
    Quand AUTH_REQUIRED=false, cette dépendance n'impose pas de token.
    """
    if not AUTH_REQUIRED:
        return "anonymous"
    if not token:
        raise HTTPException(status_code=401, detail="Token requis")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

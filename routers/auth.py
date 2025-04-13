from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from config.database import get_db
from models.users import User
from utils.face_auth import compare_faces
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import io
from pydantic import BaseModel, EmailStr
import imghdr
from schemas.auth import UserResponse, Token
from config.settings import settings
from utils.logger import logger

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str, db: Session) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(
    current_user: User = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    return get_current_user(current_user, db)

@router.post("/signup", response_model=UserResponse)
async def signup(
    email: str = Form(..., description="User email"),
    password: str = Form(..., description="User password"),
    image: UploadFile = File(..., description="User face image (JPEG/PNG)"),
    db: Session = Depends(get_db)
):
    """
    Register a new user with email, password and face image.
    """
    # Validate content type first
    if not image.content_type in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG and PNG are supported"
        )

    # Basic validations
    if not "@" in email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )
    
    # Check if user exists
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    try:
        # Read image data once
        image_data = await image.read()
        if not image_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty image file"
            )
        
        # Hash password
        hashed_password = pwd_context.hash(password)
        
        # Create new user
        db_user = User(
            email=email,
            password=hashed_password,
            image=image_data
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return UserResponse(
            id=db_user.id,
            email=email,
            message="User registered successfully"
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login/password", response_model=Token)
async def login_password(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Login with email and password using form data
    """
    user = db.query(User).filter(User.email == email).first()
    if not user or not pwd_context.verify(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return Token(
        access_token=access_token, 
        token_type="bearer",
        id=user.id  # Changed from user_id to id
    )

@router.post("/login/face", response_model=Token)
async def login_face(
    image: UploadFile = File(..., description="Live captured face image"),
    db: Session = Depends(get_db)
):
    """Login with face recognition"""
    try:
        # Validate image type
        if not image.content_type in ["image/jpeg", "image/png"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format. Only JPEG and PNG are supported."
            )

        image_data = await image.read()
        if not image_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty image file"
            )

        # Check against all users
        best_match = None
        best_confidence = 0
        comparison_errors = []
        
        users = db.query(User).all()
        logger.info(f"Comparing face against {len(users)} users")
        
        for user in users:
            if not user.image:
                logger.warning(f"User {user.email} has no stored face image")
                continue
                
            match, result = compare_faces(user.image, image_data)
            
            if isinstance(result, dict):
                confidence = result.get("confidence", 0)
                logger.info(f"Face comparison with {user.email}: confidence={confidence}")
                if match and confidence > best_confidence:
                    best_confidence = confidence
                    best_match = user
            else:
                comparison_errors.append(result)
        
        if best_match:
            logger.info(f"Face login successful for {best_match.email} with confidence {best_confidence}")
            access_token = create_access_token(data={"sub": best_match.email})
            return Token(
                access_token=access_token,
                token_type="bearer",
                id=best_match.id
            )

        if comparison_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Face detection errors: {'; '.join(comparison_errors)}"
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Face not recognized"
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Face authentication error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Face authentication failed: {str(e)}"
        )

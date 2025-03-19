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

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "your-secret-key"  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

class UserResponse(BaseModel):
    email: str
    message: str

@router.post("/register", response_model=UserResponse)
async def register(
    email: str = Form(...),
    password: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validate email format
    if not "@" in email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Validate password length
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
    
    # Read and validate image
    image_data = await image.read()
    if not image_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty image file"
        )
    
    # Validate image format
    image_type = imghdr.what(None, h=image_data)
    if image_type not in ['jpeg', 'png']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Only JPEG and PNG are supported"
        )
    
    try:
        # Detect face in the image
        face_encoding = face_recognition.face_encodings(
            face_recognition.load_image_file(io.BytesIO(image_data))
        )
        if not face_encoding:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No face detected in the image"
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
        
        return {
            "email": email,
            "message": "User registered successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login/password")
async def login_password(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/face")
async def login_face(
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    image_data = await image.read()
    
    # Check against all users (in production, you might want to optimize this)
    for user in db.query(User).all():
        if compare_faces(user.image, image_data):
            access_token = create_access_token(data={"sub": user.email})
            return {"access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Face not recognized"
    )

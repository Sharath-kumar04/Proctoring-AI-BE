from sqlalchemy import create_engine
from config.database import SQLALCHEMY_DATABASE_URL
from models.base import Base
from models.users import User
from models.logs import Log
from models.sessions import ExamSession

def init_db():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Creating database tables...")
    init_db()
    print("Tables created successfully!")

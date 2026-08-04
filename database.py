import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from models import Base

# Assuming get_secret is imported from a utility file somewhere.
# If it is in app.py, you may need to move it to a utils.py file or adapt this block.
try:
    from utils import get_secret  # Adjust this import based on your project structure
except ImportError:
    def get_secret(secret_name):
        return None

def get_database_url():
    # 1. Try Secret Manager
    try:
        url = get_secret("TACTICAL_DATABASE_URL")
        if url: return url
    except Exception:
        pass

    # 2. Try Environment variables / .env
    load_dotenv()
    url = os.getenv("TACTICAL_DATABASE_URL")
    if url: return url

    # 3. Fallback to local development proxy
    print("⚠️ Using hardcoded local development database URL")
    return "postgresql://postgres:password@127.0.0.1:5432/tactical_portfolio_db"

# Create engine and session
engine = create_engine(get_database_url(), pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

if __name__ == "__main__":
    # This block ONLY runs if you execute database.py directly.
    # It will not run when imported by app.py.
    print("Connecting to the database to build tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Schema created successfully! You can check pgAdmin.")
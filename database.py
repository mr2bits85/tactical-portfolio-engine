import os
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from models import Base, Users

# Assuming get_secret is imported from a utility file somewhere.
# If it is in app.py, you may need to move it to a utils.py file or adapt this block.
try:
    from utils import get_secret  # Adjust this import based on your project structure
except ImportError:
    def get_secret(secret_name):
        return None

# Try to import streamlit for secrets access
try:
    import streamlit as st
    _streamlit_available = True
except ImportError:
    _streamlit_available = False
    st = None  # type: ignore

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

    # 3. Try Streamlit secrets (for local development and Cloud Run)
    if _streamlit_available and hasattr(st, 'secrets'):
        # First check for complete DATABASE_URL
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
        
        # Then check for individual components
        required_keys = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
        if all(key in st.secrets for key in required_keys):
            user = st.secrets["DB_USER"]
            password = urllib.parse.quote_plus(st.secrets["DB_PASSWORD"])
            host = st.secrets["DB_HOST"]
            port = st.secrets["DB_PORT"]
            name = st.secrets["DB_NAME"]
            return f"postgresql://{user}:{password}@{host}:{port}/{name}"

    # 4. Fallback to local development proxy
    print("⚠️ Using hardcoded local development database URL")
    return "postgresql://postgres:password@127.0.0.1:5432/tactical_portfolio_db"

# Create engine and session
engine = create_engine(get_database_url(), pool_pre_ping=True, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def ensure_admin_user():
    """
    Ensure the admin user exists with role='admin'.
    Reads admin email from st.secrets (ADMIN_EMAIL or DEV_USER_EMAIL fallback).
    Call this during app startup.
    """
    if not _streamlit_available or not hasattr(st, 'secrets'):
        return
    
    admin_email = st.secrets.get("ADMIN_EMAIL") or st.secrets.get("DEV_USER_EMAIL")
    if not admin_email:
        return
    
    admin_email = admin_email.strip().lower()
    if not admin_email:
        return
    
    from sqlalchemy import select
    session = SessionLocal()
    try:
        stmt = select(Users).where(Users.email == admin_email)
        user = session.execute(stmt).scalar_one_or_none()
        
        if user:
            if user.role != 'admin':
                user.role = 'admin'
                session.commit()
                print(f"✅ Updated existing user '{admin_email}' to admin role")
            else:
                print(f"✅ Admin user '{admin_email}' already has admin role")
        else:
            new_user = Users(email=admin_email, role='admin')
            session.add(new_user)
            session.commit()
            print(f"✅ Created new admin user: '{admin_email}'")
    except Exception as e:
        session.rollback()
        print(f"⚠️ Failed to ensure admin user: {e}")
    finally:
        session.close()

# Run admin seeding on module import (when app starts)
ensure_admin_user()

if __name__ == "__main__":
    # This block ONLY runs if you execute database.py directly.
    # It will not run when imported by app.py.
    print("Connecting to the database to build tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Schema created successfully! You can check pgAdmin.")

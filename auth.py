"""
Module to get the current user's email and role from Cloud Run IAP headers
with a fallback to DEV_USER_EMAIL environment variable for local development.
"""
import os
import logging
from typing import Optional, Dict, Any

try:
    import streamlit as st
    _streamlit_available = True
except ImportError:
    _streamlit_available = False
    st = None  # type: ignore

logger = logging.getLogger(__name__)


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get the current user's info from Cloud Run IAP headers.
    Falls back to the DEV_USER_EMAIL environment variable/secret if the header is not present
    (e.g., during local development).

    Returns:
        A dict with 'email' and 'role' keys, or None if not available.
    """
    email = None

    # Try to get the header from Streamlit request context if available
    if _streamlit_available:
        try:
            # Streamlit provides access to request headers via st.context.headers
            # This works when running in a server context (e.g., Streamlit app)
            if hasattr(st, 'context') and hasattr(st.context, 'headers'):
                headers = st.context.headers
                # The IAP header is 'x-goog-authenticated-user-email'
                user_email = headers.get("x-goog-authenticated-user-email")
                if user_email:
                    # Optionally, you can strip any whitespace
                    user_email = user_email.strip()
                    if user_email.startswith("accounts.google.com:"):
                        user_email = user_email.replace("accounts.google.com:", "")
                    if user_email:
                        logger.debug(
                            f"Retrieved user email from IAP header: {user_email}"
                        )
                        email = user_email
                    else:
                        logger.warning(
                            "IAP header 'x-goog-authenticated-user-email' is empty."
                        )
                else:
                    logger.debug(
                        "IAP header 'x-goog-authenticated-user-email' not found in request headers."
                    )
            else:
                logger.debug(
                    "Streamlit context or headers not available; falling back to secrets/env."
                )
        except Exception as e:
            logger.warning(
                f"Failed to retrieve user email from Streamlit context: {e}. "
                f"Falling back to secrets/env."
            )

    # Fallback to Streamlit secrets (for local development via .streamlit/secrets.toml)
    if not email and _streamlit_available and hasattr(st, 'secrets'):
        dev_user_email = st.secrets.get("DEV_USER_EMAIL")
        if dev_user_email:
            dev_user_email = dev_user_email.strip()
            if dev_user_email:
                logger.debug(
                    f"Retrieved user email from Streamlit secrets: {dev_user_email}"
                )
                email = dev_user_email
            else:
                logger.warning("DEV_USER_EMAIL in Streamlit secrets is set but empty.")

    # Fallback to environment variable
    if not email:
        dev_user_email = os.getenv("DEV_USER_EMAIL")
        if dev_user_email:
            dev_user_email = dev_user_email.strip()
            if dev_user_email:
                logger.debug(
                    f"Retrieved user email from DEV_USER_EMAIL environment variable: {dev_user_email}"
                )
                email = dev_user_email
            else:
                logger.warning("DEV_USER_EMAIL environment variable is set but empty.")
        else:
            logger.debug("DEV_USER_EMAIL environment variable not set.")

    # If we get here, no user email could be determined
    if not email:
        logger.warning(
            "Could not determine current user: no IAP header, no Streamlit secrets, and DEV_USER_EMAIL not set."
        )
        return None

    # Now fetch the user's role from the database
    role = "user"  # default
    try:
        from database import SessionLocal
        from models import Users
        from sqlalchemy import select
        
        session = SessionLocal()
        try:
            stmt = select(Users).where(Users.email == email)
            user = session.execute(stmt).scalar_one_or_none()
            if user:
                role = user.role
                logger.debug(f"Retrieved role '{role}' for user '{email}' from database")
            else:
                logger.debug(f"User '{email}' not found in database, defaulting to role='user'")
        finally:
            session.close()
    except Exception as e:
        logger.warning(f"Failed to fetch user role from database: {e}. Defaulting to 'user'.")

    return {"email": email, "role": role}

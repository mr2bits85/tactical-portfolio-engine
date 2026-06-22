"""
Just-In-Time (JIT) user provisioning service for automatically creating user records
on first successful authentication from whitelisted emails.
"""
import os
import logging
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import select

from models import Users

logger = logging.getLogger(__name__)


def _get_whitelist() -> Optional[list[str]]:
    """
    Get the whitelist of allowed user emails from environment variable.

    Returns:
        A list of email strings (lowercased, stripped) if the environment variable
        is set and non-empty; otherwise None (indicating no whitelist restriction).
    """
    whitelist_env = os.getenv("USER_WHITELIST")
    if not whitelist_env:
        return None
    # Split by commas, strip whitespace, convert to lowercase, filter empty strings
    whitelist = [
        email.strip().lower()
        for email in whitelist_env.split(",")
        if email.strip()
    ]
    return whitelist if whitelist else None


def is_email_whitelisted(email: str) -> bool:
    """
    Check if an email is in the whitelist (if a whitelist is defined).

    Args:
        email: The email address to check.

    Returns:
        True if the email is allowed (either no whitelist defined or email in whitelist),
        False otherwise.
    """
    email_lower = email.strip().lower()
    whitelist = _get_whitelist()
    if whitelist is None:
        # No whitelist defined: allow all (but log a warning in production?)
        logger.debug(
            "USER_WHITELIST environment variable not set; allowing any email."
        )
        return True
    return email_lower in whitelist


def provision_user_if_needed(
    db_session: Session,
    email: str,
    default_role: str = "user",
) -> Optional[Users]:
    """
    Provision a user record in the database if it does not already exist,
    provided the email is whitelisted.

    Args:
        db_session: SQLAlchemy session to use for database operations.
        email: The user's email address (from IAP header or DEV_USER_EMAIL).
        default_role: The role to assign to newly created users (default: "user").

    Returns:
        The Users object (either existing or newly created), or None if
        the email is not whitelisted or provisioning failed.
    """
    # Validate email input
    if not email or not isinstance(email, str):
        logger.error("Invalid email provided for user provisioning.")
        return None

    email = email.strip()
    if not email:
        logger.error("Empty email provided for user provisioning.")
        return None

    # Check whitelist
    if not is_email_whitelisted(email):
        logger.warning(
            f"Email '{email}' is not in the whitelist. User provisioning skipped."
        )
        return None

    # Check if user already exists
    stmt = select(Users).where(Users.email == email)
    existing_user = db_session.execute(stmt).scalar_one_or_none()

    if existing_user:
        logger.debug(f"User '{email}' already exists in database.")
        return existing_user

    # Create new user
    try:
        new_user = Users(email=email, role=default_role)
        db_session.add(new_user)
        db_session.commit()
        db_session.refresh(new_user)
        logger.info(
            f"Just-In-Time provisioned new user: '{email}' with role '{default_role}'."
        )
        return new_user
    except Exception as e:
        db_session.rollback()
        logger.error(
            f"Failed to create user '{email}' during JIT provisioning: {e}",
            exc_info=True,
        )
        return None


# Convenience function that uses a context-managed session (if you have a session factory)
# This is optional and can be adapted based on how sessions are managed in your app.
def provision_user_with_session_factory(
    session_factory,
    email: str,
    default_role: str = "user",
) -> Optional[Users]:
    """
    Provision a user using a session factory (e.g., sessionmaker).

    Args:
        session_factory: A callable that returns a new SQLAlchemy Session.
        email: The user's email address.
        default_role: The role to assign to newly created users.

    Returns:
        The Users object (existing or newly created) or None.
    """
    with session_factory() as session:
        return provision_user_if_needed(session, email, default_role)
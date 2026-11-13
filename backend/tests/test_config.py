import pytest
import os


def test_settings_load():
    """Test that settings can be loaded from environment."""
    # Set required env vars
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-32chars"
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"

    from app.core.config import settings

    assert settings.APP_ENV == "development"
    assert settings.SECRET_KEY == "test-secret-key-for-testing-only-32chars"
    assert settings.DATABASE_URL == "sqlite+aiosqlite:///:memory:"


def test_jwt_algorithm():
    from app.core.config import settings

    assert settings.JWT_ALGORITHM == "HS256"
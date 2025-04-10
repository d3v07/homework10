import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_settings
from settings.config import Settings

@pytest.mark.asyncio
async def test_get_db():
    """
    Test that get_db correctly yields a session from get_async_db.
    This covers lines 10-11 of dependencies.py.
    """
    # Create a mock session
    mock_session = AsyncMock(spec=AsyncSession)
    
    # Create a mock async generator that will yield our session
    async def mock_get_async_db():
        yield mock_session
    
    # Patch get_async_db to return our mock generator
    with patch('app.dependencies.get_async_db', return_value=mock_get_async_db()):
        # Call get_db and get the yielded session
        db_gen = get_db()
        session = await anext(db_gen)
        
        # Verify we got the mock session
        assert session is mock_session

def test_get_settings():
    """Test that get_settings returns a Settings instance"""
    settings = get_settings()
    assert isinstance(settings, Settings)
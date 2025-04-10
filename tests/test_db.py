import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db, initialize_async_db, Base, async_engine

class TestDatabase:
    @pytest.fixture
    def mock_engine(self):
        return MagicMock()
    
    @pytest.fixture
    def mock_session_maker(self):
        return MagicMock()
    
    def test_initialize_async_db(self, mock_engine, mock_session_maker):
        """Test the initialization of the async database"""
        with patch('app.database.create_async_engine', return_value=mock_engine) as mock_create_engine:
            with patch('app.database.sessionmaker', return_value=mock_session_maker) as mock_make_session:
                # Call the function
                initialize_async_db("sqlite+aiosqlite:///./test.db")
                
                # Verify engine was created with correct params
                mock_create_engine.assert_called_once_with(
                    "sqlite+aiosqlite:///./test.db", 
                    echo=True, 
                    future=True
                )
                
                # Verify sessionmaker was called with correct params
                mock_make_session.assert_called_once_with(
                    bind=mock_engine, 
                    class_=AsyncSession, 
                    expire_on_commit=False, 
                    future=True
                )
    
    @pytest.mark.asyncio
    async def test_get_async_db_successful_yield(self):
        """
        Test that get_async_db correctly yields a session and closes it.
        This covers the normal execution path of lines 60-66.
        """
        # Create mock session and context manager
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_cm = MagicMock()
        mock_session_cm.__aenter__.return_value = mock_session
        
        # Patch AsyncSessionLocal to return our context manager
        with patch('app.database.AsyncSessionLocal', return_value=mock_session_cm):
            # Get the generator
            db_gen = get_async_db()
            
            # Get the session from the generator
            session = await anext(db_gen)
            
            # Verify we got our mock session
            assert session == mock_session
            
            # Session should not be closed yet
            mock_session.close.assert_not_called()
            
            # When generator completes, session should be closed
            try:
                await anext(db_gen)  # This should raise StopAsyncIteration
                pytest.fail("Generator didn't stop after first yield")
            except StopAsyncIteration:
                pass
            
            # Verify session was closed
            mock_session.close.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_get_async_db_with_exception(self):
        """
        Test that get_async_db closes the session even when an exception occurs.
        This ensures coverage of the try/finally block in lines 60-66.
        """
        # Create mock session and context manager
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session_cm = MagicMock()
        mock_session_cm.__aenter__.return_value = mock_session
        
        # Patch AsyncSessionLocal to return our context manager
        with patch('app.database.AsyncSessionLocal', return_value=mock_session_cm):
            # Get the generator
            db_gen = get_async_db()
            
            # Get the session from the generator
            session = await anext(db_gen)
            
            # Verify we got our mock session
            assert session == mock_session
            
            # Simulate exception in the code using the session
            with pytest.raises(ValueError, match="Test exception"):
                await db_gen.athrow(ValueError("Test exception"))
            
            # Even with an exception, session should be closed
            mock_session.close.assert_awaited_once()

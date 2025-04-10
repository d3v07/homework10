import uuid
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
from app.services.user_service import UserService
from app.routers.user_routes import register, login
from app.schemas.user_schemas import UserCreate, LoginRequest, UserResponse

# Tests for register endpoint (lines 130-138)
@pytest.mark.asyncio
async def test_register_success():
    # Mock dependencies
    mock_session = AsyncMock()
    
    # Create test data
    user_data = UserCreate(
        username="newuser",
        email="new@example.com",
        password="Password123!"
    )
    
    # Mock the register_user method to return a user object
    mock_user = MagicMock()
    mock_user.id = uuid.uuid4()
    mock_user.username = user_data.username
    mock_user.email = user_data.email
    
    # Patch the service method
    with patch.object(UserService, 'register_user', return_value=mock_user) as mock_register:
        # Call the endpoint
        response = await register(user_data, mock_session)
        
        # Verify response
        assert response == mock_user
        mock_register.assert_awaited_once_with(mock_session, user_data.dict())

@pytest.mark.asyncio
async def test_register_duplicate_username():
    # Mock dependencies
    mock_session = AsyncMock()
    
    # Create test data
    user_data = UserCreate(
        username="existinguser",
        email="existing@example.com",
        password="Password123!"
    )
    
    # Mock register_user to return None (username exists)
    with patch.object(UserService, 'register_user', return_value=None) as mock_register:
        # Call the endpoint and expect exception
        with pytest.raises(HTTPException) as excinfo:
            await register(user_data, mock_session)
        
        # Verify exception details
        assert excinfo.value.status_code == 400
        assert "Username already exists" in excinfo.value.detail
        mock_register.assert_awaited_once_with(mock_session, user_data.dict())

# Tests for login endpoint (lines 154-179)
@pytest.mark.asyncio
async def test_login_account_locked():
    # Mock dependencies
    mock_session = AsyncMock()
    
    # Create login request
    login_req = LoginRequest(
        username="lockeduser",
        password="Password123!"
    )
    
    # Mock is_account_locked to return True
    with patch.object(UserService, 'is_account_locked', return_value=True) as mock_locked:
        # Call endpoint and expect exception
        with pytest.raises(HTTPException) as excinfo:
            await login(login_req, mock_session)
        
        # Verify exception details
        assert excinfo.value.status_code == 400
        assert "Account locked" in excinfo.value.detail
        mock_locked.assert_awaited_once_with(mock_session, login_req.username)

@pytest.mark.asyncio
async def test_login_successful():
    # Mock dependencies
    mock_session = AsyncMock()
    
    # Create login request
    login_req = LoginRequest(
        username="testuser",
        password="Password123!"
    )
    
    # Mock the user object
    mock_user = MagicMock()
    mock_user.username = login_req.username
    
    # Mock service methods
    with patch.object(UserService, 'is_account_locked', return_value=False) as mock_locked:
        with patch.object(UserService, 'login_user', return_value=mock_user) as mock_login:
            with patch('app.routers.user_routes.create_access_token', return_value="test_token") as mock_token:
                # Call the endpoint
                response = await login(login_req, mock_session)
                
                # Verify response and method calls
                assert response["access_token"] == "test_token"
                assert response["token_type"] == "bearer"
                mock_locked.assert_awaited_once_with(mock_session, login_req.username)
                mock_login.assert_awaited_once_with(mock_session, login_req.username, login_req.password)

@pytest.mark.asyncio
async def test_login_incorrect_credentials():
    # Mock dependencies
    mock_session = AsyncMock()
    
    # Create login request
    login_req = LoginRequest(
        username="testuser",
        password="wrongpassword"
    )
    
    # Mock service methods
    with patch.object(UserService, 'is_account_locked', return_value=False) as mock_locked:
        with patch.object(UserService, 'login_user', return_value=None) as mock_login:
            # Call endpoint and expect exception
            with pytest.raises(HTTPException) as excinfo:
                await login(login_req, mock_session)
            
            # Verify exception details
            assert excinfo.value.status_code == 401
            assert "Incorrect username or password" in excinfo.value.detail
            mock_locked.assert_awaited_once_with(mock_session, login_req.username)
            mock_login.assert_awaited_once_with(mock_session, login_req.username, login_req.password)
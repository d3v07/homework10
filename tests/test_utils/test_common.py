import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import timedelta, datetime
from jose import jwt
from app.utils.common import (
    setup_logging,
    authenticate_user,
    create_access_token,
    validate_and_sanitize_url,
    verify_refresh_token,
    encode_url_to_filename,
    decode_filename_to_url,
    generate_links
)
from app.dependencies import get_settings
from fastapi import HTTPException

# Setup fixtures
@pytest.fixture
def settings():
    return get_settings()

# Test setup_logging
@patch('logging.config.fileConfig')
@patch('os.path.normpath')
def test_setup_logging(mock_normpath, mock_file_config):
    mock_normpath.return_value = '/mocked/path/logging.conf'
    setup_logging()
    mock_file_config.assert_called_once_with('/mocked/path/logging.conf', disable_existing_loggers=False)

# Test authenticate_user
@patch('logging.warning')
def test_authenticate_user_success(mock_warning, settings):
    user = authenticate_user(settings.admin_user, settings.admin_password)
    assert user == {"username": settings.admin_user}
    mock_warning.assert_not_called()

@patch('logging.warning')
def test_authenticate_user_failure(mock_warning, settings):
    user = authenticate_user("wrong_user", "wrong_password")
    assert user is None
    mock_warning.assert_called_once()

# Test create_access_token
def test_create_access_token(settings):
    data = {"sub": "test_user"}
    expires_delta = timedelta(minutes=15)
    token = create_access_token(data, expires_delta)
    
    # Verify token
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert payload["sub"] == "test_user"
    assert "exp" in payload

# Test validate_and_sanitize_url
@patch('validators.url')
@patch('logging.error')
def test_validate_and_sanitize_url_valid(mock_error, mock_validators):
    mock_validators.return_value = True
    result = validate_and_sanitize_url("https://example.com")
    assert result == "https://example.com"
    mock_error.assert_not_called()

@patch('validators.url')
@patch('logging.error')
def test_validate_and_sanitize_url_invalid(mock_error, mock_validators):
    mock_validators.return_value = False
    result = validate_and_sanitize_url("invalid-url")
    assert result is None
    mock_error.assert_called_once()

# Test verify_refresh_token
def test_verify_refresh_token_success(settings):
    # Create a valid token first
    test_data = {"sub": "test_user"}
    expire = datetime.utcnow() + timedelta(minutes=15)
    test_data.update({"exp": expire})
    token = jwt.encode(test_data, settings.secret_key, algorithm=settings.algorithm)
    
    # Verify the token
    result = verify_refresh_token(token)
    assert result == {"username": "test_user"}

def test_verify_refresh_token_invalid():
    with pytest.raises(HTTPException) as excinfo:
        verify_refresh_token("invalid-token")
    assert excinfo.value.status_code == 401
    assert "Invalid refresh token" in excinfo.value.detail

# Test encode_url_to_filename and decode_filename_to_url
@patch('app.utils.common.validate_and_sanitize_url')
def test_encode_url_to_filename(mock_validate):
    mock_validate.return_value = "https://example.com"
    result = encode_url_to_filename("https://example.com")
    assert isinstance(result, str)
    assert "=" not in result  # Padding should be removed

@patch('app.utils.common.validate_and_sanitize_url')
def test_encode_url_to_filename_invalid_url(mock_validate):
    mock_validate.return_value = None
    with pytest.raises(ValueError) as excinfo:
        encode_url_to_filename("invalid-url")
    assert "Provided URL is invalid" in str(excinfo.value)

def test_decode_filename_to_url():
    # Create an encoded filename
    encoded = "aHR0cHM6Ly9leGFtcGxlLmNvbQ"  # Without padding
    result = decode_filename_to_url(encoded)
    assert result == "https://example.com"

# Test generate_links
def test_generate_links_list_action():
    links = generate_links("list", "test.png", "http://api.example.com", "http://download.example.com/test.png")
    assert len(links) == 2
    assert links[0].rel == "view"
    assert links[1].rel == "delete"

def test_generate_links_create_action():
    links = generate_links("create", "test.png", "http://api.example.com", "http://download.example.com/test.png")
    assert len(links) == 2
    assert links[0].rel == "view"
    assert links[1].rel == "delete"

def test_generate_links_delete_action():
    links = generate_links("delete", "test.png", "http://api.example.com", "http://download.example.com/test.png")
    assert len(links) == 1
    assert links[0].rel == "delete"
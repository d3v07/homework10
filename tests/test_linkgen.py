import pytest
from unittest.mock import MagicMock
import uuid
from fastapi import Request
from app.utils.link_generation import create_user_links, generate_pagination_links
from app.schemas.link_schema import Link
from app.schemas.pagination_schema import PaginationLink

# Test last page
def test_generate_pagination_links_last_page():
    mock_request = MagicMock(spec=Request)
    mock_request.url = "http://testserver/users"
    
    # Last page
    links = generate_pagination_links(mock_request, 20, 10, 30)
    
    # Should have all types except next
    assert len(links) == 4  # self, first, last, prev
    
    # Verify links
    link_types = {link.rel for link in links}
    assert "self" in link_types
    assert "first" in link_types
    assert "last" in link_types
    assert "prev" in link_types
    assert "next" not in link_types

# Test single page (total_items < limit)
def test_generate_pagination_links_single_page():
    mock_request = MagicMock(spec=Request)
    mock_request.url = "http://testserver/users"
    
    # One page only
    links = generate_pagination_links(mock_request, 0, 10, 5)
    
    # Should still have self, first, last
    assert len(links) == 3  # self, first, last
    
    # Verify links - no prev or next needed
    link_types = {link.rel for link in links}
    assert "self" in link_types
    assert "first" in link_types
    assert "last" in link_types
    assert "next" not in link_types
    assert "prev" not in link_types
    
    # First and last should be the same
    first_link = next(link for link in links if link.rel == "first")
    last_link = next(link for link in links if link.rel == "last")
    assert first_link.href == last_link.href
"""Pytest configuration."""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_token_address():
    """Sample token address."""
    return '0x1234567890abcdef1234567890abcdef12345678'


@pytest.fixture
def mock_goplus_response():
    """Mock GoPlus API response."""
    return {
        'is_honeypot': False,
        'buy_tax': 5.0,
        'sell_tax': 5.0,
        'tax_modifiable': False,
        'owner_address': '0x0000000000000000000000000000000000000000',
        'is_mintable': False,
        'is_proxy': False,
        'hidden_owner': False,
        'is_blacklisted': False,
    }

"""Test API clients."""
import pytest
from src.core.apis import APIFactory, GoPlusAPI, DEXScreenerAPI, GeckoTerminalAPI


def test_api_factory():
    """Test API factory creates instances."""
    goplus = APIFactory.get_goplus()
    assert goplus is not None
    assert isinstance(goplus, GoPlusAPI)
    
    dex = APIFactory.get_dexscreener()
    assert dex is not None
    assert isinstance(dex, DEXScreenerAPI)
    
    gecko = APIFactory.get_geckoterminal()
    assert gecko is not None
    assert isinstance(gecko, GeckoTerminalAPI)


def test_goplus_chain_ids():
    """Test GoPlus chain ID mapping."""
    goplus = GoPlusAPI()
    assert goplus.CHAIN_IDS['eth'] == 1
    assert goplus.CHAIN_IDS['bsc'] == 56
    assert goplus.CHAIN_IDS['polygon'] == 137


def test_dexscreener_normalize_pair():
    """Test DEXScreener pair normalization."""
    dex = DEXScreenerAPI()
    
    pair = {
        'chainId': 'bsc',
        'pairAddress': '0x123',
        'baseToken': {'address': '0xabc', 'name': 'Test', 'symbol': 'TST'},
        'priceUsd': '0.001',
        'liquidity': {'usd': 10000},
    }
    
    result = dex._normalize_pair(pair)
    
    assert result['chain'] == 'bsc'
    assert result['pair_address'] == '0x123'
    assert result['base_token']['symbol'] == 'TST'
    assert result['liquidity_usd'] == 10000

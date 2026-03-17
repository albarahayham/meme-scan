"""
Simple API clients for Meme Token Scanner.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    """API configuration."""
    base_url: str
    api_key: str = ""
    rate_limit: int = 10
    timeout: int = 30


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""
    
    def __init__(self, rate: float):
        self.rate = rate
        self.min_interval = 1.0 / rate
        self.last_request = 0.0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make request."""
        async with self._lock:
            now = time.monotonic()
            wait_time = self.min_interval - (now - self.last_request)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self.last_request = time.monotonic()


class BaseAPIClient:
    """Base class for API clients."""
    
    def __init__(self, config: APIConfig):
        self.config = config
        self.rate_limiter = RateLimiter(config.rate_limit)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(aiohttp.ClientError),
    )
    async def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        await self.rate_limiter.acquire()
        session = await self._get_session()
        
        headers = kwargs.pop('headers', {})
        headers.setdefault('Accept', 'application/json')
        
        async with session.request(method, url, headers=headers, **kwargs) as response:
            response.raise_for_status()
            return await response.json()
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


class GoPlusAPI(BaseAPIClient):
    """GoPlus Security API client."""
    
    CHAIN_IDS = {
        'eth': 1, 'bsc': 56, 'polygon': 137, 'base': 8453,
        'arbitrum': 42161, 'avalanche': 43114, 'optimism': 10,
    }
    
    def __init__(self, api_key: str = ""):
        config = APIConfig(
            base_url="https://api.gopluslabs.io/api/v1",
            api_key=api_key,
            rate_limit=10,
        )
        super().__init__(config)
    
    async def get_token_security(self, chain: str, token_address: str) -> Dict[str, Any]:
        """Get token security data."""
        chain_id = self.CHAIN_IDS.get(chain.lower())
        if not chain_id:
            try:
                chain_id = int(chain)
            except ValueError:
                return {}
        
        url = f"{self.config.base_url}/token_security/{chain_id}"
        params = {"contract_addresses": token_address}
        
        try:
            result = await self._request('GET', url, params=params)
            if result.get('code') == 1:
                return result.get('result', {}).get(token_address.lower(), {})
            return {}
        except Exception as e:
            logger.error(f"GoPlus API error: {e}")
            return {}


class DEXScreenerAPI(BaseAPIClient):
    """DEXScreener API client."""
    
    def __init__(self):
        config = APIConfig(
            base_url="https://api.dexscreener.com",
            rate_limit=30,
        )
        super().__init__(config)
    
    async def get_token_pairs(self, token_address: str) -> List[Dict[str, Any]]:
        """Get trading pairs for a token."""
        url = f"{self.config.base_url}/latest/dex/tokens/{token_address}"
        
        try:
            result = await self._request('GET', url)
            return self._normalize_pairs(result.get('pairs', []))
        except Exception as e:
            logger.error(f"DEXScreener API error: {e}")
            return []
    
    async def get_pair_info(self, chain: str, pair_address: str) -> Optional[Dict[str, Any]]:
        """Get specific pair info."""
        url = f"{self.config.base_url}/latest/dex/pairs/{chain}/{pair_address}"
        
        try:
            result = await self._request('GET', url)
            pair = result.get('pair')
            return self._normalize_pair(pair) if pair else None
        except Exception as e:
            logger.error(f"DEXScreener pair error: {e}")
            return None
    
    async def search_pairs(self, query: str) -> List[Dict[str, Any]]:
        """Search for pairs."""
        url = f"{self.config.base_url}/latest/dex/search"
        params = {'q': query}
        
        try:
            result = await self._request('GET', url, params=params)
            return self._normalize_pairs(result.get('pairs', []))
        except Exception as e:
            logger.error(f"DEXScreener search error: {e}")
            return []
    
    async def get_token_boosts(self) -> List[Dict[str, Any]]:
        """Get boosted tokens."""
        url = f"{self.config.base_url}/token-boosts/latest/v1"
        
        try:
            result = await self._request('GET', url)
            return result.get('data', [])
        except Exception as e:
            logger.error(f"DEXScreener boosts error: {e}")
            return []
    
    def _normalize_pairs(self, pairs: List[Dict]) -> List[Dict[str, Any]]:
        return [self._normalize_pair(p) for p in pairs]
    
    def _normalize_pair(self, pair: Dict) -> Dict[str, Any]:
        base = pair.get('baseToken', {})
        quote = pair.get('quoteToken', {})
        liq = pair.get('liquidity', {})
        vol = pair.get('volume', {})
        txns = pair.get('txns', {})
        change = pair.get('priceChange', {})
        
        return {
            'chain': pair.get('chainId', ''),
            'dex': pair.get('dexId', ''),
            'pair_address': pair.get('pairAddress', ''),
            'pair_url': f"https://dexscreener.com/{pair.get('chainId', '')}/{pair.get('pairAddress', '')}",
            'base_token': {
                'address': base.get('address', ''),
                'name': base.get('name', ''),
                'symbol': base.get('symbol', ''),
            },
            'quote_token': {
                'address': quote.get('address', ''),
                'name': quote.get('name', ''),
                'symbol': quote.get('symbol', ''),
            },
            'price_usd': self._parse_float(pair.get('priceUsd')),
            'price_native': self._parse_float(pair.get('priceNative')),
            'liquidity_usd': liq.get('usd', 0),
            'volume_24h': vol.get('h24', 0),
            'txns_24h': txns.get('h24', {}).get('buys', 0) + txns.get('h24', {}).get('sells', 0),
            'price_change_24h': change.get('h24', 0),
            'market_cap': pair.get('marketCap', 0),
            'fdv': pair.get('fdv', 0),
            'pair_created_at': pair.get('pairCreatedAt'),
            '_raw': pair,
        }
    
    @staticmethod
    def _parse_float(value: Any) -> float:
        if value is None:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0


class GeckoTerminalAPI(BaseAPIClient):
    """GeckoTerminal API client."""
    
    def __init__(self):
        config = APIConfig(
            base_url="https://api.geckoterminal.com/api/v2",
            rate_limit=20,
        )
        super().__init__(config)
    
    async def get_new_pools(self, network: str) -> List[Dict[str, Any]]:
        """Get new pools for a network."""
        url = f"{self.config.base_url}/networks/{network}/new_pools"
        
        try:
            result = await self._request('GET', url)
            return self._normalize_pools(result.get('data', []))
        except Exception as e:
            logger.error(f"GeckoTerminal new pools error: {e}")
            return []
    
    async def get_network_trending_pools(self, network: str, page: int = 1) -> List[Dict[str, Any]]:
        """Get trending pools for a network."""
        url = f"{self.config.base_url}/networks/{network}/trending_pools"
        params = {'page': page}
        
        try:
            result = await self._request('GET', url, params=params)
            return self._normalize_pools(result.get('data', []))
        except Exception as e:
            logger.error(f"GeckoTerminal trending error: {e}")
            return []
    
    async def get_token_pools(self, network: str, token_address: str) -> List[Dict[str, Any]]:
        """Get pools for a token."""
        url = f"{self.config.base_url}/networks/{network}/tokens/{token_address}/pools"
        
        try:
            result = await self._request('GET', url)
            return self._normalize_pools(result.get('data', []))
        except Exception as e:
            logger.error(f"GeckoTerminal token pools error: {e}")
            return []
    
    def _normalize_pools(self, pools: List[Dict]) -> List[Dict[str, Any]]:
        return [self._normalize_pool(p) for p in pools]
    
    def _normalize_pool(self, pool: Dict) -> Dict[str, Any]:
        attrs = pool.get('attributes', {})
        rels = pool.get('relationships', {})
        base = rels.get('base_token', {}).get('data', {})
        
        return {
            'network': pool.get('id', '').split('_')[0] if pool.get('id') else '',
            'pool_address': attrs.get('address', ''),
            'pool_url': f"https://www.geckoterminal.com/{pool.get('id', '').split('_')[0]}/pools/{attrs.get('address', '')}",
            'base_token': {
                'address': base.get('id', '').split('_')[-1] if base.get('id') else '',
                'name': base.get('name', ''),
                'symbol': base.get('symbol', ''),
            },
            'price_usd': self._parse_float(attrs.get('base_token_price_usd')),
            'liquidity_usd': self._parse_float(attrs.get('reserve_in_usd')),
            'volume_24h': self._parse_float(attrs.get('volume_usd', {}).get('h24')),
            'market_cap': self._parse_float(attrs.get('market_cap_usd')),
            'fdv': self._parse_float(attrs.get('fdv')),
            'pool_created_at': attrs.get('pool_created_at'),
            '_raw': pool,
        }
    
    @staticmethod
    def _parse_float(value: Any) -> float:
        if value is None:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0


class APIFactory:
    """Factory for API clients."""
    
    _goplus: Optional[GoPlusAPI] = None
    _dexscreener: Optional[DEXScreenerAPI] = None
    _geckoterminal: Optional[GeckoTerminalAPI] = None
    
    @classmethod
    def get_goplus(cls) -> GoPlusAPI:
        if cls._goplus is None:
            cls._goplus = GoPlusAPI()
        return cls._goplus
    
    @classmethod
    def get_dexscreener(cls) -> DEXScreenerAPI:
        if cls._dexscreener is None:
            cls._dexscreener = DEXScreenerAPI()
        return cls._dexscreener
    
    @classmethod
    def get_geckoterminal(cls) -> GeckoTerminalAPI:
        if cls._geckoterminal is None:
            cls._geckoterminal = GeckoTerminalAPI()
        return cls._geckoterminal
    
    @classmethod
    async def close_all(cls):
        for client in [cls._goplus, cls._dexscreener, cls._geckoterminal]:
            if client:
                await client.close()
        cls._goplus = None
        cls._dexscreener = None
        cls._geckoterminal = None

"""
Token scanner for Meme Token Scanner.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from .apis import APIFactory
from .detectors import SecurityAnalyzer, SecurityReport, RiskLevel
from ..config import get_config

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class TokenInfo:
    """Token basic information."""
    address: str
    chain: str
    name: str = ""
    symbol: str = ""
    decimals: int = 18
    total_supply: int = 0
    liquidity_usd: float = 0.0
    market_cap: float = 0.0
    price_usd: float = 0.0
    volume_24h: float = 0.0
    price_change_24h: float = 0.0
    dex_url: str = ""
    pair_address: str = ""
    discovered_at: datetime = field(default_factory=datetime.now)
    source: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'address': self.address,
            'chain': self.chain,
            'name': self.name,
            'symbol': self.symbol,
            'decimals': self.decimals,
            'total_supply': str(self.total_supply),
            'liquidity_usd': self.liquidity_usd,
            'market_cap': self.market_cap,
            'price_usd': self.price_usd,
            'volume_24h': self.volume_24h,
            'price_change_24h': self.price_change_24h,
            'dex_url': self.dex_url,
            'pair_address': self.pair_address,
            'discovered_at': self.discovered_at.isoformat(),
            'source': self.source,
        }


@dataclass
class ScanResult:
    """Scan result for a single token."""
    token: TokenInfo
    report: Optional[SecurityReport] = None
    market_data: Dict[str, Any] = field(default_factory=dict)
    scanned_at: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'token': self.token.to_dict(),
            'report': self.report.to_dict() if self.report else None,
            'market_data': self.market_data,
            'scanned_at': self.scanned_at.isoformat(),
            'error': self.error,
        }


@dataclass
class ScanStats:
    """Scanner statistics."""
    total_scanned: int = 0
    safe_tokens: int = 0
    high_risk_tokens: int = 0
    honeypots_found: int = 0
    errors: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        duration = (datetime.now() - self.start_time).total_seconds()
        return {
            'total_scanned': self.total_scanned,
            'safe_tokens': self.safe_tokens,
            'high_risk_tokens': self.high_risk_tokens,
            'honeypots_found': self.honeypots_found,
            'errors': self.errors,
            'start_time': self.start_time.isoformat(),
            'duration_seconds': duration,
        }


# ============================================================================
# Token Scanner
# ============================================================================

class TokenScanner:
    """Main token scanner class."""
    
    def __init__(self):
        self.config = get_config()
        self.analyzer = SecurityAnalyzer()
        self.stats = ScanStats()
        self._callbacks: List[Callable] = []
    
    def on_result(self, callback: Callable[[ScanResult], None]) -> None:
        """Register callback for results."""
        self._callbacks.append(callback)
    
    async def _notify(self, result: ScanResult) -> None:
        """Notify callbacks."""
        for cb in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(result)
                else:
                    cb(result)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    async def discover_tokens(self, chain: str, limit: int = 50) -> List[TokenInfo]:
        """Discover new tokens for a chain."""
        tokens = []
        seen: Set[str] = set()
        
        try:
            # Get new pools from GeckoTerminal
            gecko = APIFactory.get_geckoterminal()
            pools = await gecko.get_new_pools(chain)
            
            for pool in pools[:limit]:
                base = pool.get('base_token', {})
                addr = base.get('address', '')
                
                if not addr or addr.lower() in seen:
                    continue
                
                seen.add(addr.lower())
                
                token = TokenInfo(
                    address=addr,
                    chain=chain,
                    name=base.get('name', ''),
                    symbol=base.get('symbol', ''),
                    liquidity_usd=pool.get('liquidity_usd', 0),
                    market_cap=pool.get('market_cap', 0),
                    price_usd=pool.get('price_usd', 0),
                    volume_24h=pool.get('volume_24h', 0),
                    dex_url=pool.get('pool_url', ''),
                    pair_address=pool.get('pool_address', ''),
                    source='geckoterminal_new',
                )
                tokens.append(token)
            
            # Also get trending
            if len(tokens) < limit:
                trending = await gecko.get_network_trending_pools(chain)
                for pool in trending:
                    if len(tokens) >= limit:
                        break
                    
                    base = pool.get('base_token', {})
                    addr = base.get('address', '')
                    
                    if not addr or addr.lower() in seen:
                        continue
                    
                    seen.add(addr.lower())
                    
                    token = TokenInfo(
                        address=addr,
                        chain=chain,
                        name=base.get('name', ''),
                        symbol=base.get('symbol', ''),
                        liquidity_usd=pool.get('liquidity_usd', 0),
                        market_cap=pool.get('market_cap', 0),
                        price_usd=pool.get('price_usd', 0),
                        volume_24h=pool.get('volume_24h', 0),
                        dex_url=pool.get('pool_url', ''),
                        pair_address=pool.get('pool_address', ''),
                        source='geckoterminal_trending',
                    )
                    tokens.append(token)
            
            logger.info(f"Discovered {len(tokens)} tokens on {chain}")
            return tokens
            
        except Exception as e:
            logger.error(f"Discovery error: {e}")
            return tokens
    
    async def scan_token(self, chain: str, address: str) -> ScanResult:
        """Scan a single token."""
        token = TokenInfo(address=address, chain=chain)
        result = ScanResult(token=token)
        
        try:
            # Get token data from DEXScreener
            dex = APIFactory.get_dexscreener()
            pairs = await dex.get_token_pairs(address)
            
            # Filter to chain
            chain_pairs = [p for p in pairs if p.get('chain', '').lower() == chain.lower()]
            
            if chain_pairs:
                best = max(chain_pairs, key=lambda p: p.get('liquidity_usd', 0))
                base = best.get('base_token', {})
                
                token.name = base.get('name', '')
                token.symbol = base.get('symbol', '')
                token.liquidity_usd = best.get('liquidity_usd', 0)
                token.market_cap = best.get('market_cap', 0)
                token.price_usd = best.get('price_usd', 0)
                token.volume_24h = best.get('volume_24h', 0)
                token.dex_url = best.get('pair_url', '')
                token.pair_address = best.get('pair_address', '')
                
                result.market_data = {
                    'price_usd': best.get('price_usd'),
                    'volume_24h': best.get('volume_24h'),
                    'price_change_24h': best.get('price_change_24h'),
                    'txns_24h': best.get('txns_24h'),
                }
            
            # Run security analysis
            result.report = await self.analyzer.analyze(chain, address)
            
            # Update stats
            self.stats.total_scanned += 1
            if result.report:
                if result.report.overall_risk == RiskLevel.SAFE:
                    self.stats.safe_tokens += 1
                elif result.report.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                    self.stats.high_risk_tokens += 1
                if result.report.is_honeypot:
                    self.stats.honeypots_found += 1
            
            await self._notify(result)
            
        except Exception as e:
            logger.error(f"Scan error for {address}: {e}")
            result.error = str(e)
            self.stats.errors += 1
        
        return result
    
    async def scan_chain(self, chain: str, limit: int = 50) -> List[ScanResult]:
        """Scan multiple tokens on a chain."""
        logger.info(f"Starting scan on {chain} (limit: {limit})")
        
        # Discover tokens
        tokens = await self.discover_tokens(chain, limit)
        
        if not tokens:
            logger.warning(f"No tokens found on {chain}")
            return []
        
        # Scan in parallel with concurrency limit
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent
        
        async def limited_scan(token: TokenInfo) -> ScanResult:
            async with semaphore:
                return await self.scan_token(token.chain, token.address)
        
        tasks = [limited_scan(t) for t in tokens]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter valid results
        valid = []
        for r in results:
            if isinstance(r, ScanResult):
                valid.append(r)
            elif isinstance(r, Exception):
                logger.error(f"Task error: {r}")
                self.stats.errors += 1
        
        logger.info(
            f"Scan complete on {chain}: {len(valid)} tokens, "
            f"{self.stats.safe_tokens} safe, {self.stats.honeypots_found} honeypots"
        )
        
        return valid
    
    async def monitor(self, chains: List[str], interval: int = 60) -> None:
        """Monitor chains continuously."""
        logger.info(f"Starting monitor on {chains}")
        seen: Set[str] = set()
        
        while True:
            try:
                for chain in chains:
                    tokens = await self.discover_tokens(chain, limit=20)
                    
                    for token in tokens:
                        key = f"{chain}:{token.address.lower()}"
                        if key not in seen:
                            seen.add(key)
                            logger.info(f"New token on {chain}: {token.symbol} ({token.address[:10]}...)")
                            
                            result = await self.scan_token(chain, token.address)
                            
                            if result.report:
                                if result.report.overall_risk == RiskLevel.SAFE:
                                    logger.warning(
                                        f"SAFE TOKEN: {token.symbol} on {chain} - Score: {result.report.risk_score}"
                                    )
                                elif result.report.is_honeypot:
                                    logger.warning(
                                        f"HONEYPOT: {token.symbol} on {chain}"
                                    )
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                logger.info("Monitor stopped")
                break
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(interval)


# ============================================================================
# Result Exporter
# ============================================================================

class ResultExporter:
    """Export scan results."""
    
    def __init__(self, output_dir: str = "./results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_json(self, results: List[ScanResult], filename: str) -> str:
        """Export to JSON."""
        filepath = self.output_dir / filename
        
        data = {
            'exported_at': datetime.now().isoformat(),
            'total': len(results),
            'results': [r.to_dict() for r in results],
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Exported JSON to {filepath}")
        return str(filepath)
    
    def export_csv(self, results: List[ScanResult], filename: str) -> str:
        """Export to CSV."""
        import csv
        
        filepath = self.output_dir / filename
        
        columns = [
            'address', 'chain', 'name', 'symbol', 'liquidity_usd', 'market_cap',
            'risk_level', 'risk_score', 'is_honeypot', 'is_mintable',
            'owner_renounced', 'buy_tax', 'sell_tax', 'lp_locked', 'safe_to_trade',
            'dex_url', 'scanned_at',
        ]
        
        rows = []
        for r in results:
            t, rp = r.token, r.report
            rows.append({
                'address': t.address,
                'chain': t.chain,
                'name': t.name,
                'symbol': t.symbol,
                'liquidity_usd': t.liquidity_usd,
                'market_cap': t.market_cap,
                'risk_level': rp.overall_risk.value if rp else 'unknown',
                'risk_score': rp.risk_score if rp else 0,
                'is_honeypot': rp.is_honeypot if rp else False,
                'is_mintable': rp.is_mintable if rp else False,
                'owner_renounced': rp.is_owner_renounced if rp else False,
                'buy_tax': rp.buy_tax if rp else 0,
                'sell_tax': rp.sell_tax if rp else 0,
                'lp_locked': rp.lp_locked if rp else False,
                'safe_to_trade': rp.safe_to_trade if rp else False,
                'dex_url': t.dex_url,
                'scanned_at': r.scanned_at.isoformat(),
            })
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        
        logger.info(f"Exported CSV to {filepath}")
        return str(filepath)
    
    def export_summary(self, results: List[ScanResult], stats: ScanStats, filename: str = None) -> str:
        """Export summary."""
        if not filename:
            filename = f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.output_dir / filename
        
        safe = [r for r in results if r.report and r.report.overall_risk == RiskLevel.SAFE]
        risky = [r for r in results if r.report and r.report.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]]
        
        summary = {
            'stats': stats.to_dict(),
            'safe_tokens': [{'address': r.token.address, 'symbol': r.token.symbol} for r in safe],
            'high_risk_tokens': [{'address': r.token.address, 'symbol': r.token.symbol} for r in risky],
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, default=str)
        
        return str(filepath)

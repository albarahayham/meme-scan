"""
Result exporter for scan results.
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .scanner import ScanResult, ScanStats
from .detectors import RiskLevel


class ResultExporter:
    """Exports scan results to various formats."""
    
    def __init__(self, output_dir: Optional[str] = None):
        """Initialize exporter."""
        self.output_dir = Path(output_dir or "./results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_json(
        self,
        results: List[ScanResult],
        filename: Optional[str] = None,
    ) -> str:
        """Export results to JSON."""
        if not filename:
            filename = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.output_dir / filename
        
        data = {
            'exported_at': datetime.now().isoformat(),
            'total_results': len(results),
            'results': [r.to_dict() for r in results],
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        return str(filepath)
    
    def export_csv(
        self,
        results: List[ScanResult],
        filename: Optional[str] = None,
    ) -> str:
        """Export results to CSV."""
        if not filename:
            filename = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        filepath = self.output_dir / filename
        
        columns = [
            'token_address', 'chain', 'name', 'symbol',
            'liquidity_usd', 'market_cap', 'risk_level',
            'risk_score', 'is_honeypot', 'is_mintable',
            'owner_renounced', 'buy_tax', 'sell_tax',
            'lp_locked', 'top_holders_pct', 'safe_to_trade',
        ]
        
        rows = []
        for r in results:
            t = r.token
            rp = r.report
            rows.append({
                'token_address': t.address,
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
                'top_holders_pct': rp.top_holders_concentration if rp else 0,
                'safe_to_trade': rp.safe_to_trade if rp else False,
            })
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        
        return str(filepath)
    
    def export_summary(
        self,
        results: List[ScanResult],
        stats: ScanStats,
        filename: Optional[str] = None,
    ) -> str:
        """Export summary report."""
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

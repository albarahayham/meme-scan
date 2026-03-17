"""
Utility functions for Meme Token Scanner.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Setup logging configuration."""
    log_format = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format,
        handlers=handlers,
    )


def format_usd(value: float) -> str:
    """Format USD value."""
    if value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value/1_000:.2f}K"
    else:
        return f"${value:.2f}"


def shorten_address(address: str, chars: int = 6) -> str:
    """Shorten address for display."""
    if not address or len(address) < chars * 2 + 3:
        return address or ""
    return f"{address[:chars+2]}...{address[-chars:]}"


def create_results_table(results: List[Dict], title: str) -> Any:
    """Create results table."""
    try:
        from rich.console import Console
        from rich.table import Table
        
        table = Table(title=title)
        table.add_column("Symbol", style="cyan")
        table.add_column("Chain", style="green")
        table.add_column("Risk", style="yellow")
        table.add_column("Score", style="magenta")
        table.add_column("Liquidity", style="blue")
        table.add_column("Honeypot", style="red")
        table.add_column("LP", style="green")
        
        for r in results:
            token = r.get('token', {})
            report = r.get('report', {})
            detect = report.get('detect_summary', {})
            
            risk = report.get('overall_risk', 'unknown')
            risk_style = {
                'safe': 'green', 'low': 'blue', 'medium': 'yellow',
                'high': 'orange1', 'critical': 'red',
            }.get(risk, 'white')
            
            table.add_row(
                token.get('symbol', '?')[:10],
                token.get('chain', '?').upper(),
                f"[{risk_style}]{risk.upper()}[/{risk_style}]",
                str(report.get('risk_score', 0)),
                format_usd(token.get('liquidity_usd', 0)),
                "🚨" if detect.get('honeypot') else "✓",
                "🔒" if detect.get('lp_locked') else "⚠",
            )
        
        return table
    except ImportError:
        return _create_plain_table(results, title)


def _create_plain_table(results: List[Dict], title: str) -> str:
    """Create plain text table."""
    lines = [f"\n{title}", "=" * 70]
    
    for r in results:
        token = r.get('token', {})
        report = r.get('report', {})
        detect = report.get('detect_summary', {})
        
        lines.append(
            f"\n{token.get('symbol', '?')} ({token.get('chain', '?').upper()})"
        )
        lines.append(f"  Risk: {report.get('overall_risk', '?').upper()}")
        lines.append(f"  Score: {report.get('risk_score', 0)}")
        lines.append(f"  Liquidity: {format_usd(token.get('liquidity_usd', 0))}")
        lines.append(f"  Honeypot: {'YES' if detect.get('honeypot') else 'No'}")
    
    return "\n".join(lines)


def print_summary(stats: Dict[str, Any]) -> None:
    """Print scan summary."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        
        console = Console()
        console.print(Panel(
            f"""
[bold]Scan Summary[/bold]

Total Scanned: {stats.get('total_scanned', 0)}
Safe Tokens: [green]{stats.get('safe_tokens', 0)}[/green]
High Risk: [red]{stats.get('high_risk_tokens', 0)}[/red]
Honeypots: [red bold]{stats.get('honeypots_found', 0)}[/red bold]
Errors: {stats.get('errors', 0)}
Duration: {stats.get('duration_seconds', 0):.1f}s
            """,
            title="[bold blue]Statistics[/bold blue]",
            border_style="blue",
        ))
    except ImportError:
        print("\n" + "=" * 50)
        print("SCAN SUMMARY")
        print("=" * 50)
        print(f"Total: {stats.get('total_scanned', 0)}")
        print(f"Safe: {stats.get('safe_tokens', 0)}")
        print(f"High Risk: {stats.get('high_risk_tokens', 0)}")
        print(f"Honeypots: {stats.get('honeypots_found', 0)}")
        print("=" * 50 + "\n")

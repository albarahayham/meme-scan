#!/usr/bin/env python3
"""
Meme Token Scanner - CLI Interface

A comprehensive tool for analyzing and detecting risks in new meme tokens.
Designed to run on Termux/Android with full async support.

Usage:
    python cli.py scan --chain bsc --limit 50
    python cli.py analyze --chain eth --address 0x...
    python cli.py monitor --chains bsc,eth,polygon

Security Notice:
    This tool is READ-ONLY by default. No on-chain transactions are ever
    executed without explicit user consent and the --execute-tx flag.
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config, reset_config
from src.core.scanner import TokenScanner, ScanResult, ResultExporter
from src.core.detectors import SecurityAnalyzer, RiskLevel
from src.core.notifier import AlertManager, ConsoleAlerter
from src.core.utils import (
    setup_logging,
    create_results_table,
    print_summary,
    format_usd,
    shorten_address,
    ensure_output_dir,
)

# Setup logger
logger = logging.getLogger(__name__)

# Try importing rich for better CLI
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.table import Table
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# ============================================================================
# Argument Parser
# ============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        prog='meme-scan',
        description='Meme Token Security Scanner - Analyze and detect risks in new tokens',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan BSC for new tokens
  python cli.py scan --chain bsc --limit 50
  
  # Analyze a specific token
  python cli.py analyze --chain eth --address 0x1234...
  
  # Monitor multiple chains continuously
  python cli.py monitor --chains bsc,eth,polygon --interval 60
  
  # Export results to specific format
  python cli.py scan --chain bsc --output results.json --format json

For more information, visit: https://github.com/albarahayham/meme-scan
        """
    )
    
    # Global options
    parser.add_argument(
        '-c', '--config',
        type=str,
        help='Path to configuration file'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='count',
        default=0,
        help='Increase verbosity (use -v, -vv, -vvv)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # === SCAN COMMAND ===
    scan_parser = subparsers.add_parser(
        'scan',
        help='Scan chain(s) for new tokens and analyze them'
    )
    scan_parser.add_argument(
        '--chain', '-ch',
        type=str,
        default='bsc',
        help='Chain to scan (default: bsc)'
    )
    scan_parser.add_argument(
        '--limit', '-l',
        type=int,
        default=50,
        help='Maximum tokens to scan (default: 50)'
    )
    scan_parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output file path'
    )
    scan_parser.add_argument(
        '--format', '-f',
        type=str,
        choices=['json', 'csv', 'both'],
        default='json',
        help='Output format (default: json)'
    )
    scan_parser.add_argument(
        '--include-trending',
        action='store_true',
        help='Also scan trending tokens'
    )
    scan_parser.add_argument(
        '--min-liquidity',
        type=float,
        default=0,
        help='Minimum liquidity filter (USD)'
    )
    scan_parser.add_argument(
        '--min-score',
        type=int,
        default=0,
        help='Minimum security score to include in output (0-100)'
    )
    scan_parser.add_argument(
        '--only-safe',
        action='store_true',
        help='Only show tokens marked as safe'
    )
    scan_parser.add_argument(
        '--notify',
        action='store_true',
        help='Enable Termux notifications'
    )
    
    # === ANALYZE COMMAND ===
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='Analyze a specific token'
    )
    analyze_parser.add_argument(
        '--chain', '-ch',
        type=str,
        required=True,
        help='Chain identifier (eth, bsc, polygon, base, etc.)'
    )
    analyze_parser.add_argument(
        '--address', '-a',
        type=str,
        required=True,
        help='Token contract address'
    )
    analyze_parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output file path'
    )
    analyze_parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed analysis'
    )
    
    # === MONITOR COMMAND ===
    monitor_parser = subparsers.add_parser(
        'monitor',
        help='Monitor chains continuously for new tokens'
    )
    monitor_parser.add_argument(
        '--chains',
        type=str,
        default='bsc',
        help='Comma-separated list of chains to monitor'
    )
    monitor_parser.add_argument(
        '--interval', '-i',
        type=int,
        default=60,
        help='Scan interval in seconds (default: 60)'
    )
    monitor_parser.add_argument(
        '--output-dir',
        type=str,
        default='./results',
        help='Directory for output files'
    )
    monitor_parser.add_argument(
        '--notify',
        action='store_true',
        default=True,
        help='Enable notifications (default: True)'
    )
    
    # === SEARCH COMMAND ===
    search_parser = subparsers.add_parser(
        'search',
        help='Search for tokens by name, symbol, or address'
    )
    search_parser.add_argument(
        'query',
        type=str,
        help='Search query'
    )
    search_parser.add_argument(
        '--chain',
        type=str,
        help='Filter by chain'
    )
    search_parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='Maximum results'
    )
    
    # === CONFIG COMMAND ===
    config_parser = subparsers.add_parser(
        'config',
        help='Show or manage configuration'
    )
    config_parser.add_argument(
        '--show',
        action='store_true',
        help='Show current configuration'
    )
    config_parser.add_argument(
        '--init',
        action='store_true',
        help='Initialize configuration file'
    )
    
    return parser


# ============================================================================
# Command Handlers
# ============================================================================

async def cmd_scan(args: argparse.Namespace) -> int:
    """Handle the scan command."""
    console = Console() if RICH_AVAILABLE else None
    
    # Log start
    if console:
        console.print(Panel(
            f"[bold]Starting scan on {args.chain.upper()}[/bold]\n"
            f"Limit: {args.limit} tokens\n"
            f"Min Liquidity: ${args.min_liquidity:,.0f}",
            title="🔍 Meme Token Scanner",
            border_style="blue",
        ))
    else:
        print(f"\nStarting scan on {args.chain.upper()} (limit: {args.limit})")
        print("=" * 50)
    
    # Initialize scanner
    scanner = TokenScanner()
    exporter = ResultExporter()
    alert_manager = AlertManager() if args.notify else None
    
    # Run scan
    try:
        results = await scanner.scan_chain(
            args.chain,
            limit=args.limit,
        )
        
        # Filter results
        if args.min_score > 0:
            results = [
                r for r in results
                if r.report and r.report.risk_score >= args.min_score
            ]
        
        if args.only_safe:
            results = [
                r for r in results
                if r.report and r.report.safe_to_trade
            ]
        
        # Send alerts
        if alert_manager:
            for result in results:
                if result.report and result.report.overall_risk in [
                    RiskLevel.SAFE, RiskLevel.CRITICAL
                ]:
                    await alert_manager.alert_scan_result(result)
        
        # Display results
        if results:
            table_data = [r.to_dict() for r in results]
            table = create_results_table(table_data, f"Scan Results ({len(results)} tokens)")
            
            if RICH_AVAILABLE and console:
                console.print(table)
            else:
                print(table)
        else:
            if console:
                console.print("[yellow]No tokens found matching criteria[/yellow]")
            else:
                print("No tokens found matching criteria")
        
        # Print summary
        print_summary(scanner.stats.to_dict())
        
        # Export results
        if args.output or args.format:
            output_path = args.output
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if args.format in ['json', 'both']:
                json_path = output_path or f"scan_{args.chain}_{timestamp}.json"
                exporter.export_json(results, json_path)
                if console:
                    console.print(f"[green]JSON saved to: {json_path}[/green]")
            
            if args.format in ['csv', 'both']:
                csv_path = output_path.replace('.json', '.csv') if output_path else f"scan_{args.chain}_{timestamp}.csv"
                exporter.export_csv(results, csv_path)
                if console:
                    console.print(f"[green]CSV saved to: {csv_path}[/green]")
        
        return 0
        
    except KeyboardInterrupt:
        if console:
            console.print("\n[yellow]Scan interrupted by user[/yellow]")
        else:
            print("\nScan interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Scan error: {e}")
        if console:
            console.print(f"[red]Error: {e}[/red]")
        else:
            print(f"Error: {e}")
        return 1
    finally:
        # Cleanup
        from src.core.apis import APIFactory
        await APIFactory.close_all()


async def cmd_analyze(args: argparse.Namespace) -> int:
    """Handle the analyze command for a specific token."""
    console = Console() if RICH_AVAILABLE else None
    
    if console:
        console.print(Panel(
            f"[bold]Analyzing token on {args.chain.upper()}[/bold]\n"
            f"Address: {args.address}",
            title="🔬 Token Analysis",
            border_style="blue",
        ))
    
    # Initialize analyzer
    scanner = TokenScanner()
    
    try:
        # Run analysis
        result = await scanner.scan_token(args.chain, args.address)
        
        if result.error:
            if console:
                console.print(f"[red]Error: {result.error}[/red]")
            else:
                print(f"Error: {result.error}")
            return 1
        
        report = result.report
        token = result.token
        
        if not report:
            if console:
                console.print("[red]Could not analyze token[/red]")
            else:
                print("Could not analyze token")
            return 1
        
        # Display results
        if RICH_AVAILABLE and console:
            # Main info panel
            risk_color = {
                RiskLevel.SAFE: "green",
                RiskLevel.LOW: "blue",
                RiskLevel.MEDIUM: "yellow",
                RiskLevel.HIGH: "orange1",
                RiskLevel.CRITICAL: "red",
            }.get(report.overall_risk, "white")
            
            console.print(Panel(
                f"""
[bold]Token Information[/bold]
  Name: {token.name or 'Unknown'}
  Symbol: {token.symbol or 'Unknown'}
  Chain: {token.chain.upper()}
  Address: {token.address}

[bold]Market Data[/bold]
  Liquidity: {format_usd(token.liquidity_usd)}
  Market Cap: {format_usd(token.market_cap)}

[bold]Security Assessment[/bold]
  Risk Level: [{risk_color}]{report.overall_risk.value.upper()}[/{risk_color}]
  Risk Score: {report.risk_score}/100
  Safe to Trade: {'✅ Yes' if report.safe_to_trade else '❌ No'}

[bold]Detection Summary[/bold]
  Honeypot: {'🚨 YES' if report.is_honeypot else '✅ No'}
  Mintable: {'⚠️ Yes' if report.is_mintable else '✅ No'}
  Owner Renounced: {'✅ Yes' if report.is_owner_renounced else '⚠️ No'}
  Buy Tax: {report.buy_tax:.1f}%
  Sell Tax: {report.sell_tax:.1f}%
  LP Locked: {'🔒 Yes' if report.lp_locked else '⚠️ No'}
  Top 10 Holders: {report.top_holders_concentration:.1f}%

[bold]Summary[/bold]
  {report.summary}

[bold]Links[/bold]
  DEXScreener: {token.dex_url}
  GeckoTerminal: https://www.geckoterminal.com/{token.chain}/pools/{token.address}
                """,
                title=f"[bold]{token.symbol or 'Token'}[/bold] Analysis",
                border_style=risk_color,
            ))
        else:
            # Plain text output
            print(f"\n{'='*60}")
            print(f"TOKEN: {token.symbol or 'Unknown'} ({token.name or 'Unknown'})")
            print(f"Chain: {token.chain.upper()}")
            print(f"Address: {token.address}")
            print(f"{'='*60}")
            print(f"\nRisk Level: {report.overall_risk.value.upper()}")
            print(f"Risk Score: {report.risk_score}/100")
            print(f"Safe to Trade: {'Yes' if report.safe_to_trade else 'No'}")
            print(f"\nHoneypot: {'YES' if report.is_honeypot else 'No'}")
            print(f"Mintable: {'Yes' if report.is_mintable else 'No'}")
            print(f"Owner Renounced: {'Yes' if report.is_owner_renounced else 'No'}")
            print(f"Buy Tax: {report.buy_tax:.1f}%")
            print(f"Sell Tax: {report.sell_tax:.1f}%")
            print(f"LP Locked: {'Yes' if report.lp_locked else 'No'}")
            print(f"Top 10 Holders: {report.top_holders_concentration:.1f}%")
            print(f"\n{report.summary}")
            print(f"\nDEX: {token.dex_url}")
            print(f"{'='*60}\n")
        
        # Export if requested
        if args.output:
            exporter = ResultExporter()
            exporter.export_json([result], args.output)
            if console:
                console.print(f"[green]Results saved to: {args.output}[/green]")
        
        return 0
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        if console:
            console.print(f"[red]Error: {e}[/red]")
        else:
            print(f"Error: {e}")
        return 1


async def cmd_monitor(args: argparse.Namespace) -> int:
    """Handle the monitor command for continuous scanning."""
    console = Console() if RICH_AVAILABLE else None
    
    chains = [c.strip().lower() for c in args.chains.split(',')]
    
    if console:
        console.print(Panel(
            f"[bold]Starting continuous monitoring[/bold]\n"
            f"Chains: {', '.join(c.upper() for c in chains)}\n"
            f"Interval: {args.interval}s\n"
            f"Notifications: {'Enabled' if args.notify else 'Disabled'}",
            title="📡 Token Monitor",
            border_style="blue",
        ))
    
    scanner = TokenScanner()
    exporter = ResultExporter(args.output_dir)
    alert_manager = AlertManager() if args.notify else None
    
    # Callback for handling results
    async def on_result(result: ScanResult):
        if alert_manager and result.report:
            await alert_manager.alert_scan_result(result)
    
    scanner.on_result(on_result)
    
    try:
        await scanner.monitor(
            chains=chains,
            interval=args.interval,
        )
        return 0
        
    except KeyboardInterrupt:
        if console:
            console.print("\n[yellow]Monitoring stopped by user[/yellow]")
        else:
            print("\nMonitoring stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Monitor error: {e}")
        if console:
            console.print(f"[red]Error: {e}[/red]")
        else:
            print(f"Error: {e}")
        return 1


async def cmd_search(args: argparse.Namespace) -> int:
    """Handle the search command."""
    console = Console() if RICH_AVAILABLE else None
    
    from src.core.apis import APIFactory
    
    try:
        dex = APIFactory.get_dexscreener()
        pairs = await dex.search_pairs(args.query)
        
        if args.chain:
            pairs = [p for p in pairs if p.get('chain', '').lower() == args.chain.lower()]
        
        pairs = pairs[:args.limit]
        
        if not pairs:
            if console:
                console.print("[yellow]No results found[/yellow]")
            else:
                print("No results found")
            return 0
        
        if RICH_AVAILABLE and console:
            table = Table(title=f"Search Results for '{args.query}'")
            table.add_column("Symbol", style="cyan")
            table.add_column("Chain", style="green")
            table.add_column("Price", style="yellow")
            table.add_column("Liquidity", style="blue")
            table.add_column("Address", style="white")
            
            for pair in pairs:
                base = pair.get('base_token', {})
                table.add_row(
                    base.get('symbol', '?'),
                    pair.get('chain', '?').upper(),
                    f"${pair.get('price_usd', 0):.8f}",
                    format_usd(pair.get('liquidity_usd', 0)),
                    shorten_address(base.get('address', '')),
                )
            
            console.print(table)
        else:
            print(f"\nSearch Results for '{args.query}':")
            print("-" * 80)
            for pair in pairs:
                base = pair.get('base_token', {})
                print(f"{base.get('symbol', '?'):10} | {pair.get('chain', '?').upper():8} | "
                      f"${pair.get('price_usd', 0):.8f} | {format_usd(pair.get('liquidity_usd', 0))}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        if console:
            console.print(f"[red]Error: {e}[/red]")
        else:
            print(f"Error: {e}")
        return 1


def cmd_config(args: argparse.Namespace) -> int:
    """Handle the config command."""
    console = Console() if RICH_AVAILABLE else None
    
    if args.init:
        import shutil
        
        config_dir = Path.home() / ".config" / "meme-scan"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        dest = config_dir / "config.yaml"
        
        # Find example config
        example = Path(__file__).parent.parent / "config.example.yaml"
        if example.exists():
            shutil.copy(example, dest)
            if console:
                console.print(f"[green]Config initialized at: {dest}[/green]")
            else:
                print(f"Config initialized at: {dest}")
        else:
            if console:
                console.print("[yellow]Config example not found. Please create config manually.[/yellow]")
            else:
                print("Config example not found.")
        return 0
    
    if args.show:
        config = get_config()
        
        if RICH_AVAILABLE and console:
            console.print(Panel(
                f"""
[bold]APIs Configured:[/bold]
  GoPlus: {'✅' if config.get_api('goplus') else '❌'}
  DEXScreener: {'✅' if config.get_api('dexscreener') else '❌'}
  GeckoTerminal: {'✅' if config.get_api('geckoterminal') else '❌'}

[bold]Chains Enabled:[/bold]
  {', '.join(c.upper() for c in config.get_enabled_chains().keys())}

[bold]Scanner Settings:[/bold]
  Poll Interval: {config.scanner.poll_interval}s
  Max Concurrent: {config.scanner.max_concurrent_scans}
  Batch Size: {config.scanner.batch_size}

[bold]Cache:[/bold]
  Enabled: {config.cache.enabled}
  TTL: {config.cache.ttl}s

[bold]Security:[/bold]
  On-chain TX: {'⚠️ ENABLED' if config.is_onchain_allowed() else '❌ Disabled (safe)'}
  Dry Run: {config.is_dry_run()}
                """,
                title="⚙️ Configuration",
                border_style="blue",
            ))
        else:
            print("\nConfiguration:")
            print(f"  Enabled Chains: {', '.join(config.get_enabled_chains().keys())}")
            print(f"  On-chain TX: {'ENABLED' if config.is_onchain_allowed() else 'Disabled'}")
        
        return 0
    
    return 0


# ============================================================================
# Main Entry Point
# ============================================================================

def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Show help if no command
    if not args.command:
        parser.print_help()
        return 0
    
    # Setup logging
    log_level = 'DEBUG' if args.debug else ('INFO' if args.verbose else 'WARNING')
    setup_logging(level=log_level)
    
    # Initialize config
    if args.config:
        reset_config()
        get_config(args.config)
    
    # Run command
    try:
        if args.command == 'scan':
            return asyncio.run(cmd_scan(args))
        elif args.command == 'analyze':
            return asyncio.run(cmd_analyze(args))
        elif args.command == 'monitor':
            return asyncio.run(cmd_monitor(args))
        elif args.command == 'search':
            return asyncio.run(cmd_search(args))
        elif args.command == 'config':
            return cmd_config(args)
        else:
            parser.print_help()
            return 0
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

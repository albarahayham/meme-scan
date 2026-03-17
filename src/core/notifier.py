"""
Notification system for Meme Token Scanner.
"""

import asyncio
import logging
import shutil
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Alert types."""
    HONEYPOT = "honeypot"
    SAFE = "safe"
    HIGH_RISK = "high_risk"
    ERROR = "error"


@dataclass
class Alert:
    """Alert data."""
    type: AlertType
    title: str
    message: str
    data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}


class TermuxNotifier:
    """Termux notification handler."""
    
    def __init__(self):
        self.available = self._check_available()
    
    def _check_available(self) -> bool:
        """Check if termux-notification is available."""
        return shutil.which('termux-notification') is not None
    
    async def notify(self, alert: Alert) -> bool:
        """Send notification."""
        if not self.available:
            logger.debug("Termux notifications not available")
            return False
        
        try:
            cmd = [
                'termux-notification',
                '--title', alert.title,
                '--content', alert.message[:100],
            ]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            
            await proc.wait()
            return True
            
        except Exception as e:
            logger.error(f"Notification error: {e}")
            return False
    
    async def vibrate(self, duration: int = 500) -> bool:
        """Vibrate device."""
        if not shutil.which('termux-vibrate'):
            return False
        
        try:
            proc = await asyncio.create_subprocess_exec(
                'termux-vibrate', '-d', str(duration),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()
            return True
        except Exception as e:
            logger.error(f"Vibrate error: {e}")
            return False


class AlertManager:
    """Manage alerts and notifications."""
    
    def __init__(self):
        self.notifier = TermuxNotifier()
        self._recent: Dict[str, float] = {}
    
    async def alert_scan_result(self, result: Any) -> None:
        """Send alert for scan result."""
        try:
            report = result.report
            token = result.token
            
            if not report:
                return
            
            key = f"{token.chain}:{token.address}"
            
            if report.is_honeypot:
                await self._send(Alert(
                    type=AlertType.HONEYPOT,
                    title=f"🚨 HONEYPOT: {token.symbol}",
                    message=f"Honeypot detected on {token.chain.upper()}!",
                    data={'address': token.address, 'chain': token.chain},
                ))
            
            elif report.overall_risk.value == 'safe' and report.safe_to_trade:
                await self._send(Alert(
                    type=AlertType.SAFE,
                    title=f"✅ SAFE: {token.symbol}",
                    message=f"Safe token found on {token.chain.upper()}. Score: {report.risk_score}",
                    data={'address': token.address, 'chain': token.chain},
                ))
            
        except Exception as e:
            logger.error(f"Alert error: {e}")
    
    async def _send(self, alert: Alert) -> None:
        """Send alert with cooldown."""
        import time
        
        key = f"{alert.type.value}:{alert.data.get('address', '')}"
        now = time.time()
        
        # 5 minute cooldown
        if key in self._recent and now - self._recent[key] < 300:
            return
        
        self._recent[key] = now
        
        logger.info(f"Alert: {alert.title} - {alert.message}")
        await self.notifier.notify(alert)

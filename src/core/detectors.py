"""
Security detectors for Meme Token Scanner.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .apis import APIFactory

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Data Classes
# ============================================================================

class RiskLevel(Enum):
    """Risk levels."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DetectionType(Enum):
    """Types of security detections."""
    HONEYPOT = "honeypot"
    MINTABLE = "mintable"
    OWNERSHIP = "ownership"
    TAX = "tax"
    LP_LOCK = "lp_lock"
    HOLDERS = "holders"
    BLACKLIST = "blacklist"


@dataclass
class DetectionResult:
    """Result from a detector."""
    detection_type: DetectionType
    risk_level: RiskLevel
    detected: bool
    confidence: float = 1.0
    details: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'detection_type': self.detection_type.value,
            'risk_level': self.risk_level.value,
            'detected': self.detected,
            'confidence': round(self.confidence, 3),
            'details': self.details,
            'warnings': self.warnings,
            'recommendations': self.recommendations,
        }


@dataclass
class SecurityReport:
    """Complete security report."""
    token_address: str
    chain: str
    detections: List[DetectionResult]
    overall_risk: RiskLevel
    risk_score: int
    summary: str
    is_honeypot: bool
    is_mintable: bool
    is_owner_renounced: bool
    buy_tax: float
    sell_tax: float
    lp_locked: bool
    top_holders_concentration: float
    safe_to_trade: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'token_address': self.token_address,
            'chain': self.chain,
            'detections': [d.to_dict() for d in self.detections],
            'overall_risk': self.overall_risk.value,
            'risk_score': self.risk_score,
            'summary': self.summary,
            'detect_summary': {
                'honeypot': self.is_honeypot,
                'mintable': self.is_mintable,
                'owner_renounced': self.is_owner_renounced,
                'buy_tax': self.buy_tax,
                'sell_tax': self.sell_tax,
                'lp_locked': self.lp_locked,
                'top_holders_concentration': self.top_holders_concentration,
            },
            'safe_to_trade': self.safe_to_trade,
        }


# ============================================================================
# Base Detector
# ============================================================================

class BaseDetector(ABC):
    """Base detector class."""
    
    @abstractmethod
    async def detect(self, chain: str, address: str, data: Dict[str, Any]) -> DetectionResult:
        """Run detection."""
        pass
    
    @staticmethod
    def _parse_float(value: Any) -> float:
        if value is None:
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    @staticmethod
    def _parse_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('1', 'true', 'yes')
        return bool(value)


# ============================================================================
# Honeypot Detector
# ============================================================================

class HoneypotDetector(BaseDetector):
    """Detect honeypot tokens."""
    
    async def detect(self, chain: str, address: str, data: Dict[str, Any]) -> DetectionResult:
        result = DetectionResult(
            detection_type=DetectionType.HONEYPOT,
            risk_level=RiskLevel.SAFE,
            detected=False,
        )
        
        try:
            is_honeypot = data.get('is_honeypot', False)
            sell_tax = data.get('sell_tax', 0)
            
            if is_honeypot:
                result.detected = True
                result.risk_level = RiskLevel.CRITICAL
                result.confidence = 0.95
                result.warnings.append("CONFIRMED HONEYPOT: Token cannot be sold")
                result.recommendations.append("DO NOT BUY - This is a honeypot")
                result.details['confirmed'] = True
            elif sell_tax > 90:
                result.detected = True
                result.risk_level = RiskLevel.CRITICAL
                result.confidence = 0.9
                result.warnings.append(f"Extreme sell tax ({sell_tax}%) - likely honeypot")
                result.details['hidden_honeypot'] = True
            
            result.details['sell_tax'] = sell_tax
            result.details['is_honeypot'] = is_honeypot
            
        except Exception as e:
            logger.error(f"Honeypot detection error: {e}")
            result.warnings.append(f"Could not verify honeypot status: {e}")
        
        return result


# ============================================================================
# Mint Detector
# ============================================================================

class MintDetector(BaseDetector):
    """Detect mintable tokens."""
    
    async def detect(self, chain: str, address: str, data: Dict[str, Any]) -> DetectionResult:
        result = DetectionResult(
            detection_type=DetectionType.MINTABLE,
            risk_level=RiskLevel.SAFE,
            detected=False,
        )
        
        try:
            is_mintable = data.get('is_mintable', False)
            is_proxy = data.get('is_proxy', False)
            
            if is_mintable:
                result.detected = True
                result.risk_level = RiskLevel.HIGH
                result.warnings.append("Token is mintable - supply can increase")
                result.recommendations.append("Check for mint restrictions")
            
            if is_proxy:
                result.details['is_proxy'] = True
                if result.detected:
                    result.risk_level = RiskLevel.CRITICAL
                    result.warnings.append("Proxy contract - logic can be changed")
            
            result.details['is_mintable'] = is_mintable
            
        except Exception as e:
            logger.error(f"Mint detection error: {e}")
        
        return result


# ============================================================================
# Tax Detector
# ============================================================================

class TaxDetector(BaseDetector):
    """Analyze token taxes."""
    
    async def detect(self, chain: str, address: str, data: Dict[str, Any]) -> DetectionResult:
        result = DetectionResult(
            detection_type=DetectionType.TAX,
            risk_level=RiskLevel.SAFE,
            detected=False,
        )
        
        try:
            buy_tax = data.get('buy_tax', 0)
            sell_tax = data.get('sell_tax', 0)
            tax_modifiable = data.get('tax_modifiable', False)
            
            result.details['buy_tax'] = buy_tax
            result.details['sell_tax'] = sell_tax
            
            max_tax = max(buy_tax, sell_tax)
            
            if max_tax > 25:
                result.detected = True
                result.risk_level = RiskLevel.CRITICAL
                result.warnings.append(f"Extreme tax: Buy={buy_tax}%, Sell={sell_tax}%")
            elif max_tax > 15:
                result.detected = True
                result.risk_level = RiskLevel.HIGH
                result.warnings.append(f"High tax: Buy={buy_tax}%, Sell={sell_tax}%")
            elif max_tax > 5:
                result.detected = True
                result.risk_level = RiskLevel.MEDIUM
                result.warnings.append(f"Elevated tax: Buy={buy_tax}%, Sell={sell_tax}%")
            
            if tax_modifiable:
                result.details['tax_modifiable'] = True
                result.warnings.append("Taxes can be modified by owner")
                if result.risk_level == RiskLevel.SAFE:
                    result.risk_level = RiskLevel.MEDIUM
            
        except Exception as e:
            logger.error(f"Tax detection error: {e}")
        
        return result


# ============================================================================
# Ownership Detector
# ============================================================================

class OwnershipDetector(BaseDetector):
    """Check ownership status."""
    
    async def detect(self, chain: str, address: str, data: Dict[str, Any]) -> DetectionResult:
        result = DetectionResult(
            detection_type=DetectionType.OWNERSHIP,
            risk_level=RiskLevel.SAFE,
            detected=False,
        )
        
        try:
            owner = data.get('owner_address', '')
            hidden_owner = data.get('hidden_owner', False)
            owner_pct = data.get('owner_percent', 0)
            
            zero = '0x0000000000000000000000000000000000000000'
            is_renounced = owner.lower() == zero
            
            result.details['owner_address'] = owner
            result.details['is_renounced'] = is_renounced
            result.details['hidden_owner'] = hidden_owner
            
            if hidden_owner:
                result.detected = True
                result.risk_level = RiskLevel.CRITICAL
                result.warnings.append("HIDDEN OWNER DETECTED - Major red flag")
            elif not is_renounced:
                result.detected = True
                result.risk_level = RiskLevel.MEDIUM
                result.warnings.append("Ownership not renounced")
                result.details['owner_has_control'] = True
            
            if owner_pct > 5:
                result.details['owner_holdings_pct'] = owner_pct
                result.warnings.append(f"Owner holds {owner_pct}% of supply")
            
        except Exception as e:
            logger.error(f"Ownership detection error: {e}")
        
        return result


# ============================================================================
# LP Lock Detector
# ============================================================================

class LPLockDetector(BaseDetector):
    """Check LP lock status."""
    
    async def detect(self, chain: str, address: str, data: Dict[str, Any]) -> DetectionResult:
        result = DetectionResult(
            detection_type=DetectionType.LP_LOCK,
            risk_level=RiskLevel.SAFE,
            detected=False,
        )
        
        try:
            lp_holders = data.get('lp_holders', [])
            lp_locked_pct = 0
            
            # Known locker addresses
            lockers = [
                '0x4076c9d9d5b08e9eb6e3f1f0e6e8f1d8c8e1b7f5',
                '0x71b5759d367ee0d9d6a45c1e5c5f8c7b1b9e1d2a',
            ]
            
            for holder in lp_holders:
                addr = holder.get('address', '').lower()
                pct = holder.get('percent', 0)
                if any(l in addr for l in lockers):
                    lp_locked_pct += self._parse_float(pct)
            
            result.details['lp_locked_pct'] = lp_locked_pct
            result.details['lp_holders'] = lp_holders
            
            if not lp_holders:
                result.detected = True
                result.risk_level = RiskLevel.HIGH
                result.warnings.append("Could not verify LP status")
                result.details['lp_locked'] = False
            elif lp_locked_pct < 80:
                result.detected = True
                result.risk_level = RiskLevel.HIGH
                result.warnings.append("LP not locked - RUG PULL RISK")
                result.details['lp_locked'] = False
            else:
                result.details['lp_locked'] = True
            
        except Exception as e:
            logger.error(f"LP lock detection error: {e}")
        
        return result


# ============================================================================
# Holder Concentration Detector
# ============================================================================

class HolderConcentrationDetector(BaseDetector):
    """Analyze holder concentration."""
    
    async def detect(self, chain: str, address: str, data: Dict[str, Any]) -> DetectionResult:
        result = DetectionResult(
            detection_type=DetectionType.HOLDERS,
            risk_level=RiskLevel.SAFE,
            detected=False,
        )
        
        try:
            top_holders = data.get('top_holders', [])
            top_10_pct = data.get('top_10_holders_pct', 0)
            
            result.details['top_holders'] = top_holders[:10]
            result.details['top_10_pct'] = top_10_pct
            
            if top_10_pct > 70:
                result.detected = True
                result.risk_level = RiskLevel.CRITICAL
                result.warnings.append(f"Extreme concentration: Top 10 own {top_10_pct:.1f}%")
            elif top_10_pct > 50:
                result.detected = True
                result.risk_level = RiskLevel.HIGH
                result.warnings.append(f"High concentration: Top 10 own {top_10_pct:.1f}%")
            elif top_10_pct > 30:
                result.detected = True
                result.risk_level = RiskLevel.MEDIUM
                result.warnings.append(f"Moderate concentration: Top 10 own {top_10_pct:.1f}%")
            
        except Exception as e:
            logger.error(f"Holder detection error: {e}")
        
        return result


# ============================================================================
# Blacklist Detector
# ============================================================================

class BlacklistDetector(BaseDetector):
    """Detect blacklist functions."""
    
    async def detect(self, chain: str, address: str, data: Dict[str, Any]) -> DetectionResult:
        result = DetectionResult(
            detection_type=DetectionType.BLACKLIST,
            risk_level=RiskLevel.SAFE,
            detected=False,
        )
        
        try:
            is_blacklisted = data.get('is_blacklisted', False)
            
            if is_blacklisted:
                result.detected = True
                result.risk_level = RiskLevel.HIGH
                result.warnings.append("Token has blacklist functionality")
                result.recommendations.append("Check if you are blacklisted")
            
            result.details['has_blacklist'] = is_blacklisted
            
        except Exception as e:
            logger.error(f"Blacklist detection error: {e}")
        
        return result


# ============================================================================
# Security Analyzer
# ============================================================================

class SecurityAnalyzer:
    """Main security analyzer."""
    
    def __init__(self):
        self.detectors = [
            HoneypotDetector(),
            MintDetector(),
            TaxDetector(),
            OwnershipDetector(),
            LPLockDetector(),
            HolderConcentrationDetector(),
            BlacklistDetector(),
        ]
    
    async def analyze(self, chain: str, address: str) -> SecurityReport:
        """Run full security analysis."""
        # Get GoPlus data
        goplus = APIFactory.get_goplus()
        security_data = await goplus.get_token_security(chain, address)
        
        # Run all detectors
        detections = []
        for detector in self.detectors:
            try:
                result = await detector.detect(chain, address, security_data)
                detections.append(result)
            except Exception as e:
                logger.error(f"Detector {detector.__class__.__name__} failed: {e}")
        
        # Calculate overall risk
        risk_level, risk_score = self._calc_risk(detections)
        
        # Extract values
        is_honeypot = self._get_val(detections, DetectionType.HONEYPOT, 'detected', False)
        is_mintable = self._get_val(detections, DetectionType.MINTABLE, 'detected', False)
        is_renounced = self._get_val(detections, DetectionType.OWNERSHIP, 'is_renounced', False)
        buy_tax = self._get_val(detections, DetectionType.TAX, 'buy_tax', 0)
        sell_tax = self._get_val(detections, DetectionType.TAX, 'sell_tax', 0)
        lp_locked = self._get_val(detections, DetectionType.LP_LOCK, 'lp_locked', False)
        top_pct = self._get_val(detections, DetectionType.HOLDERS, 'top_10_pct', 0)
        
        # Determine if safe
        safe = (
            not is_honeypot and
            risk_level not in [RiskLevel.HIGH, RiskLevel.CRITICAL] and
            lp_locked
        )
        
        return SecurityReport(
            token_address=address,
            chain=chain,
            detections=detections,
            overall_risk=risk_level,
            risk_score=risk_score,
            summary=self._gen_summary(risk_level),
            is_honeypot=is_honeypot,
            is_mintable=is_mintable,
            is_owner_renounced=is_renounced,
            buy_tax=buy_tax,
            sell_tax=sell_tax,
            lp_locked=lp_locked,
            top_holders_concentration=top_pct,
            safe_to_trade=safe,
        )
    
    def _calc_risk(self, detections: List[DetectionResult]) -> Tuple[RiskLevel, int]:
        """Calculate overall risk."""
        score = 100
        
        weights = {
            DetectionType.HONEYPOT: 50,
            DetectionType.MINTABLE: 25,
            DetectionType.OWNERSHIP: 15,
            DetectionType.TAX: 10,
            DetectionType.LP_LOCK: 20,
            DetectionType.HOLDERS: 10,
            DetectionType.BLACKLIST: 15,
        }
        
        for d in detections:
            if d.detected:
                w = weights.get(d.detection_type, 10)
                if d.risk_level == RiskLevel.CRITICAL:
                    score -= w * 2
                elif d.risk_level == RiskLevel.HIGH:
                    score -= w
                elif d.risk_level == RiskLevel.MEDIUM:
                    score -= w // 2
        
        score = max(0, min(100, score))
        
        if score >= 80:
            level = RiskLevel.SAFE
        elif score >= 60:
            level = RiskLevel.LOW
        elif score >= 40:
            level = RiskLevel.MEDIUM
        elif score >= 20:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.CRITICAL
        
        # Honeypot override
        for d in detections:
            if d.detection_type == DetectionType.HONEYPOT and d.detected:
                return RiskLevel.CRITICAL, 0
        
        return level, score
    
    def _get_val(self, detections: List[DetectionResult], dtype: DetectionType, key: str, default: Any) -> Any:
        """Get value from detection."""
        for d in detections:
            if d.detection_type == dtype:
                return d.details.get(key, default)
        return default
    
    def _gen_summary(self, level: RiskLevel) -> str:
        """Generate summary text."""
        summaries = {
            RiskLevel.SAFE: "No significant risks detected. Token appears safe.",
            RiskLevel.LOW: "Low risk detected. Minor concerns found.",
            RiskLevel.MEDIUM: "Moderate risk. Some security concerns.",
            RiskLevel.HIGH: "High risk detected. Multiple concerns found.",
            RiskLevel.CRITICAL: "CRITICAL: Do not trade. Major security issues.",
        }
        return summaries.get(level, "Unknown risk level.")

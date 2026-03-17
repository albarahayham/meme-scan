"""Test security detectors."""
import pytest
from src.core.detectors import (
    SecurityAnalyzer,
    HoneypotDetector,
    MintDetector,
    TaxDetector,
    RiskLevel,
    DetectionType,
)


def test_risk_level_enum():
    """Test risk level enum values."""
    assert RiskLevel.SAFE.value == 'safe'
    assert RiskLevel.LOW.value == 'low'
    assert RiskLevel.MEDIUM.value == 'medium'
    assert RiskLevel.HIGH.value == 'high'
    assert RiskLevel.CRITICAL.value == 'critical'


def test_detection_type_enum():
    """Test detection type enum."""
    assert DetectionType.HONEYPOT.value == 'honeypot'
    assert DetectionType.MINTABLE.value == 'mintable'
    assert DetectionType.TAX.value == 'tax'


@pytest.mark.asyncio
async def test_honeypot_detector_safe():
    """Test honeypot detector with safe token."""
    detector = HoneypotDetector()
    
    # Mock data - not honeypot
    data = {'is_honeypot': False, 'sell_tax': 5}
    
    result = await detector.detect('bsc', '0xtest', data)
    
    assert result.detection_type == DetectionType.HONEYPOT
    assert result.detected == False


@pytest.mark.asyncio
async def test_honeypot_detector_dangerous():
    """Test honeypot detector with honeypot token."""
    detector = HoneypotDetector()
    
    # Mock data - is honeypot
    data = {'is_honeypot': True, 'sell_tax': 99}
    
    result = await detector.detect('bsc', '0xtest', data)
    
    assert result.detected == True
    assert result.risk_level == RiskLevel.CRITICAL


@pytest.mark.asyncio
async def test_mint_detector():
    """Test mint detector."""
    detector = MintDetector()
    
    data = {'is_mintable': True, 'is_proxy': False}
    
    result = await detector.detect('bsc', '0xtest', data)
    
    assert result.detected == True
    assert result.risk_level == RiskLevel.HIGH


@pytest.mark.asyncio
async def test_tax_detector_normal():
    """Test tax detector with normal taxes."""
    detector = TaxDetector()
    
    data = {'buy_tax': 5, 'sell_tax': 5, 'tax_modifiable': False}
    
    result = await detector.detect('bsc', '0xtest', data)
    
    assert result.details['buy_tax'] == 5
    assert result.details['sell_tax'] == 5


@pytest.mark.asyncio
async def test_tax_detector_high():
    """Test tax detector with high taxes."""
    detector = TaxDetector()
    
    data = {'buy_tax': 20, 'sell_tax': 25, 'tax_modifiable': False}
    
    result = await detector.detect('bsc', '0xtest', data)
    
    assert result.detected == True
    assert result.risk_level == RiskLevel.HIGH

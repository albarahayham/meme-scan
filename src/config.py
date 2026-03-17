"""
Configuration management for Meme Token Scanner.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass

import yaml


# Default config paths
DEFAULT_CONFIG_PATHS = [
    Path.home() / ".config" / "meme-scan" / "config.yaml",
    Path("./config.yaml"),
    Path("./config.example.yaml"),
]


@dataclass
class APIConfig:
    """API configuration."""
    base_url: str
    api_key: str = ""
    rate_limit: int = 10
    timeout: int = 30


@dataclass
class ChainConfig:
    """Chain configuration."""
    name: str
    chain_id: int
    rpc_url: str
    explorer: str
    enabled: bool = True


@dataclass
class ScannerSettings:
    """Scanner settings."""
    poll_interval: int = 10
    max_concurrent_scans: int = 5
    batch_size: int = 20


@dataclass
class CacheSettings:
    """Cache settings."""
    enabled: bool = True
    ttl: int = 300
    max_size: int = 1000


class Config:
    """Main configuration class."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration."""
        self._raw: Dict[str, Any] = {}
        self.apis: Dict[str, APIConfig] = {}
        self.chains: Dict[str, ChainConfig] = {}
        self.scanner = ScannerSettings()
        self.cache = CacheSettings()
        self.filters: Dict[str, Any] = {}
        self.thresholds: Dict[str, Any] = {}
        self.security: Dict[str, Any] = {}
        
        self._load_config(config_path)
    
    def _load_config(self, config_path: Optional[str] = None) -> None:
        """Load configuration from file."""
        config_file = None
        
        if config_path:
            config_file = Path(config_path)
        else:
            for path in DEFAULT_CONFIG_PATHS:
                if path.exists():
                    config_file = path
                    break
        
        if config_file and config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self._raw = yaml.safe_load(f) or {}
        
        self._parse()
    
    def _parse(self) -> None:
        """Parse configuration."""
        # Parse APIs
        for name, settings in self._raw.get('apis', {}).items():
            self.apis[name] = APIConfig(
                base_url=settings.get('base_url', ''),
                api_key=settings.get('api_key', ''),
                rate_limit=settings.get('rate_limit', 10),
                timeout=settings.get('timeout', 30),
            )
        
        # Parse chains
        for chain_id, settings in self._raw.get('chains', {}).items():
            self.chains[chain_id] = ChainConfig(
                name=settings.get('name', chain_id),
                chain_id=settings.get('chain_id', 0),
                rpc_url=settings.get('rpc_url', ''),
                explorer=settings.get('explorer', ''),
                enabled=settings.get('enabled', True),
            )
        
        # Parse scanner
        scanner = self._raw.get('scanner', {})
        self.scanner = ScannerSettings(
            poll_interval=scanner.get('poll_interval', 10),
            max_concurrent_scans=scanner.get('max_concurrent_scans', 5),
            batch_size=scanner.get('batch_size', 20),
        )
        
        # Parse cache
        cache = self._raw.get('cache', {})
        self.cache = CacheSettings(
            enabled=cache.get('enabled', True),
            ttl=cache.get('ttl', 300),
            max_size=cache.get('max_size', 1000),
        )
        
        # Parse filters
        self.filters = self._raw.get('scanner', {}).get('filters', {})
        self.thresholds = self._raw.get('thresholds', {})
        self.security = self._raw.get('security', {})
    
    def get_api(self, name: str) -> Optional[APIConfig]:
        """Get API configuration."""
        return self.apis.get(name)
    
    def get_chain(self, chain_id: str) -> Optional[ChainConfig]:
        """Get chain configuration."""
        return self.chains.get(chain_id)
    
    def get_enabled_chains(self) -> Dict[str, ChainConfig]:
        """Get all enabled chains."""
        return {k: v for k, v in self.chains.items() if v.enabled}
    
    def is_onchain_allowed(self) -> bool:
        """Check if on-chain operations are allowed."""
        config_allowed = self.security.get('allow_onchain_tx', False)
        env_var = self.security.get('onchain_env_var', 'ALLOW_ONCHAIN')
        env_allowed = os.getenv(env_var, '0') == '1'
        return config_allowed and env_allowed
    
    def is_dry_run(self) -> bool:
        """Check if dry-run mode."""
        return self.security.get('dry_run_default', True)
    
    def get_output_dir(self) -> Path:
        """Get output directory."""
        output = self._raw.get('output', {}).get('directory', './results')
        return Path(output)


# Global config instance
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """Get configuration instance."""
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config


def reset_config() -> None:
    """Reset configuration."""
    global _config
    _config = None

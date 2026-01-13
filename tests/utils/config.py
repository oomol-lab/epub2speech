import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Load .env file from project root (only if dotenv is available)
try:
    from dotenv import load_dotenv

    _project_root = Path(__file__).parent.parent.parent
    _env_path = _project_root / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
        logger.debug("Loaded environment variables from: %s", _env_path)

except ImportError:
    # dotenv not installed, will use system environment variables directly
    pass


@dataclass
class _ProviderConfig:
    """Mirror of cli.py's _ProviderConfig for testing"""

    args: list[str]
    env_vars: list[str]
    display_name: str


# Mirror of cli.py's PROVIDER_CONFIGS
_PROVIDER_CONFIGS: dict[str, _ProviderConfig] = {
    "azure": _ProviderConfig(
        args=["azure_key", "azure_region"],
        env_vars=["AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION"],
        display_name="Azure TTS",
    ),
    "doubao": _ProviderConfig(
        args=["doubao_token", "doubao_url"],
        env_vars=["DOUBAO_ACCESS_TOKEN", "DOUBAO_BASE_URL"],
        display_name="Doubao TTS",
    ),
}


class TTSConfig:
    def __init__(self):
        self._available_providers: dict[str, dict[str, Any]] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from environment variables for all providers"""
        for provider_name, config in _PROVIDER_CONFIGS.items():
            values = {}
            all_present = True

            for arg_name, env_var in zip(config.args, config.env_vars):
                env_value = os.getenv(env_var)
                if env_value:
                    values[arg_name] = env_value
                else:
                    all_present = False
                    break

            if all_present:
                self._available_providers[provider_name] = values
                logger.info("Configuration loaded for %s", config.display_name)
            else:
                logger.debug("Configuration incomplete for %s, skipping", config.display_name)

    def get_available_providers(self) -> list[str]:
        """Get list of providers with complete configuration"""
        return list(self._available_providers.keys())

    def get_provider_config(self, provider_name: str) -> dict[str, Any]:
        """Get configuration for a specific provider"""
        return self._available_providers.get(provider_name, {})

    def has_provider(self, provider_name: str) -> bool:
        """Check if a provider has complete configuration"""
        return provider_name in self._available_providers

    # Legacy methods for backward compatibility
    def get_azure_config(self) -> dict[str, Any]:
        """Get Azure configuration (legacy method)"""
        azure_config = self.get_provider_config("azure")
        if not azure_config:
            return {}
        return {"subscription_key": azure_config.get("azure_key"), "region": azure_config.get("azure_region")}

    def validate_config(self) -> bool:
        """Validate Azure configuration (legacy method)"""
        return self.has_provider("azure")


def load_tts_config() -> TTSConfig:
    return TTSConfig()

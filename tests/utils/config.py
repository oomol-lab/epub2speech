import logging
import os
from pathlib import Path
from typing import Any, Dict

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


class TTSConfig:
    def __init__(self):
        self._config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from environment variables"""
        subscription_key = os.getenv("AZURE_SPEECH_KEY")
        region = os.getenv("AZURE_SPEECH_REGION")

        if subscription_key and region:
            self._config = {"azure_speech": {"subscription_key": subscription_key, "region": region}}
            logger.info("Configuration loaded from environment variables")
        else:
            logger.warning("Azure Speech configuration not found in environment variables")
            self._config = {}

    def get_azure_config(self) -> Dict[str, Any]:
        return self._config.get("azure_speech", {})

    def validate_config(self) -> bool:
        azure_config = self.get_azure_config()

        if not azure_config.get("subscription_key"):
            logger.error("Azure Speech subscription key not configured (AZURE_SPEECH_KEY)")
            return False

        if not azure_config.get("region"):
            logger.error("Azure Speech region not configured (AZURE_SPEECH_REGION)")
            return False

        return True


def load_tts_config() -> TTSConfig:
    return TTSConfig()

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TTSConfig:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).parent.parent / "tts_config.json"
        self._config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            self._config = {}
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            logger.info(f"Configuration loaded from: {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = {}

    def get_azure_config(self) -> Dict[str, Any]:
        return self._config.get("azure_speech", {})

    def validate_config(self) -> bool:
        azure_config = self.get_azure_config()

        if not azure_config.get("subscription_key"):
            logger.error("Azure Speech subscription key not configured")
            return False

        if not azure_config.get("region"):
            logger.error("Azure Speech region not configured")
            return False

        return True


def load_tts_config(config_path: Optional[Path] = None) -> TTSConfig:
    return TTSConfig(config_path)
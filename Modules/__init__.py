"""
Extraction v3 Modules
Multi-Game RPG PDF Processor Components
"""

from .game_configs import GAME_CONFIGS, get_supported_games, get_game_config
from .game_detector import GameDetector
from .categorizer import GameAwareCategorizer
from .pdf_processor import MultiGamePDFProcessor
from .multi_collection_manager import MultiGameCollectionManager

__version__ = "3.0.0"
__author__ = "Dunstan Project Team"

__all__ = [
    "GAME_CONFIGS",
    "get_supported_games", 
    "get_game_config",
    "GameDetector",
    "GameAwareCategorizer", 
    "MultiGamePDFProcessor",
    "MultiGameCollectionManager"
]

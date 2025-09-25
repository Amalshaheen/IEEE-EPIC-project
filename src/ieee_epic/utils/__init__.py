"""
Utilities module for IEEE EPIC STT system.
"""

from .setup import SetupManager
from .audio import AudioTester

__all__ = ["SetupManager", "AudioTester"]
"""
IEEE EPIC Speech-to-Text System
===============================

A comprehensive offline speech-to-text system with AI integration,
designed for Raspberry Pi and other Linux systems.

Features:
- Offline Malayalam and English speech recognition
- AI-powered response generation
- Raspberry Pi optimization
- Modular and extensible architecture
"""

__version__ = "0.2.0"
__author__ = "IEEE EPIC Team"
__email__ = "epic@ieee.org"

from .core.stt import STTEngine
from .core.ai_response import AIResponseSystem
from .core.config import Settings

__all__ = [
    "STTEngine",
    "AIResponseSystem", 
    "Settings",
    "__version__",
]
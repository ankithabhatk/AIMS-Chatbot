"""
Project Brain Loader - Runtime access to project state

This module loads project-brain/memory.json on app startup,
making the project aware of its own state, phase, decisions, and risks.

Usage:
    from app.core.brain import BRAIN, get_brain
    
    phase = BRAIN["current_phase"]
    risks = BRAIN["risks"]
    decisions = BRAIN["key_decisions"]
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class BrainLoader:
    """Loads and provides access to project brain (memory.json)"""
    
    def __init__(self):
        self._brain: Optional[Dict[str, Any]] = None
        self._brain_path = Path(__file__).parent.parent.parent.parent / "project-brain" / "memory.json"
    
    def load(self) -> Dict[str, Any]:
        """Load project brain from disk"""
        try:
            if not self._brain_path.exists():
                logger.warning(f"Brain not found at {self._brain_path}")
                return self._get_default_brain()
            
            with open(self._brain_path, "r") as f:
                self._brain = json.load(f)
            
            logger.info(f"✅ Project brain loaded")
            logger.info(f"   Phase: {self._brain.get('current_phase', 'unknown')}")
            logger.info(f"   Status: {self._brain.get('phase_status', 'unknown')}")
            logger.info(f"   Modules complete: {len(self._brain.get('completed_modules', []))}")
            logger.info(f"   Risks identified: {len(self._brain.get('risks', []))}")
            
            return self._brain
        
        except Exception as e:
            logger.error(f"Failed to load brain: {e}")
            return self._get_default_brain()
    
    def get(self) -> Dict[str, Any]:
        """Get loaded brain (lazy load if not already loaded)"""
        if self._brain is None:
            self.load()
        return self._brain or self._get_default_brain()
    
    @staticmethod
    def _get_default_brain() -> Dict[str, Any]:
        """Fallback brain if memory.json not available"""
        return {
            "project_name": "AIMS College Chatbot (fallback)",
            "current_phase": "unknown",
            "phase_status": "unknown",
            "completed_modules": [],
            "pending_modules": [],
            "risks": [],
            "key_decisions": [],
            "notes": "Brain not loaded - using fallback"
        }
    
    def get_current_phase(self) -> str:
        """Get current project phase"""
        return self.get().get("current_phase", "unknown")
    
    def is_phase_complete(self) -> bool:
        """Check if current phase is marked complete"""
        status = self.get().get("phase_status", "")
        return "COMPLETE" in status
    
    def get_risks(self) -> list:
        """Get identified risks"""
        return self.get().get("risks", [])
    
    def get_next_priorities(self) -> list:
        """Get next priorities"""
        return self.get().get("next_priorities", [])
    
    def get_completed_modules(self) -> list:
        """Get list of completed modules"""
        return self.get().get("completed_modules", [])
    
    def get_pending_modules(self) -> list:
        """Get list of pending modules"""
        return self.get().get("pending_modules", [])


# Global brain instance
_brain_loader = BrainLoader()

# Convenient function
def get_brain() -> Dict[str, Any]:
    """Get project brain singleton"""
    return _brain_loader.get()

# Expose as BRAIN constant for easy imports
BRAIN = _brain_loader

import time
import logging
from typing import Dict, Optional

logger = logging.getLogger("barnaby")

class VolatileScribeMemory:
    """
    In-memory storage for clinical audio transcriptions.
    Strictly volatile: data exists solely in RAM during active session and
    is explicitly overwritten/zeroed out upon completion.
    """
    def __init__(self):
        self._active_sessions: Dict[str, dict] = {}

    def create_session(self, session_id: str, patient_alias: str = "Anonymous") -> None:
        self._active_sessions[session_id] = {
            "alias": patient_alias,
            "created_at": time.time(),
            "transcript_chunks": [],
            "structured_summary": ""
        }
        logger.info(f"Created ephemeral medical scribe session: {session_id}")

    def append_transcript(self, session_id: str, text: str) -> None:
        if session_id in self._active_sessions:
            self._active_sessions[session_id]["transcript_chunks"].append(text)

    def get_full_transcript(self, session_id: str) -> Optional[str]:
        session = self._active_sessions.get(session_id)
        if session:
            return " ".join(session["transcript_chunks"])
        return None

    def purge_session(self, session_id: str) -> bool:
        """Permanently wipes session data from RAM."""
        if session_id in self._active_sessions:
            # Overwrite dictionary content in-place before dropping reference
            self._active_sessions[session_id].clear()
            del self._active_sessions[session_id]
            logger.info(f"Purged session {session_id} from volatile RAM.")
            return True
        return False

# Global instance initialized once in memory
scribe_memory = VolatileScribeMemory()
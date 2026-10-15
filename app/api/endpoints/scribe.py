from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.services.scribe_memory import scribe_memory

router = APIRouter()

class SessionStartRequest(BaseModel):
    session_id: str
    patient_alias: str = "Patient"

class TranscriptChunk(BaseModel):
    session_id: str
    text: str

@router.post("/start")
async def start_session(req: SessionStartRequest):
    scribe_memory.create_session(req.session_id, req.patient_alias)
    return {"status": "Session started in volatile RAM", "session_id": req.session_id}

@router.post("/append")
async def append_chunk(chunk: TranscriptChunk):
    scribe_memory.append_transcript(chunk.session_id, chunk.text)
    return {"status": "Chunk appended"}

@router.get("/transcript/{session_id}")
async def get_transcript(session_id: str):
    transcript = scribe_memory.get_full_transcript(session_id)
    if transcript is None:
        raise HTTPException(status_code=404, detail="Session not found or already purged.")
    return {"session_id": session_id, "transcript": transcript}

@router.delete("/purge/{session_id}")
async def purge_session(session_id: str):
    success = scribe_memory.purge_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"status": "SUCCESS: Session completely zeroed and erased from memory."}
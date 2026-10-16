from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel
from app.services.scribe_memory import scribe_memory
import httpx
from app.services.stt import transcribe_audio_chunk

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

@router.post("/audio-chunk")
async def transcribe_chunk(session_id: str = Form(...), audio_chunk: UploadFile = File(...)):
    audio_bytes: bytes = await audio_chunk.read()

    ext = audio_chunk.filename.split(".")[-1] if audio_chunk.filename and "." in audio_chunk.filename else "wav"

    transcript_chunk = transcribe_audio_chunk(audio_bytes, ext)

    scribe_memory.append_transcript(session_id,transcript_chunk)

    return {'Status': 'Transcribed and appended'}

@router.post("/finalize/{session_id}")
async def summarize_transcript(session_id:str):
    patient_transcript = scribe_memory.get_full_transcript(session_id)
    prompt = f"""You are an expert AI medical scribe. Your task is to generate a professional, accurate, and concise SOAP (Subjective, Objective, Assessment, Plan) note based ONLY on the provided conversation transcript.

CRITICAL INSTRUCTIONS:
1. Do NOT invent, assume, or extrapolate any medical information, symptoms, or vitals not explicitly stated in the transcript.
2. Use professional medical terminology while accurately preserving the clinical facts reported by the patient and provider.
3. If a section of the SOAP note lacks information from the transcript (e.g., no physical exam or lab results were discussed for Objective), write "Not discussed" or "N/A".

FORMAT STRUCTURE:

### SUBJECTIVE
- **Chief Complaint (CC):** Primary reason for visit in patient's/provider's context.
- **History of Present Illness (HPI):** Onset, location, duration, character, aggravating/alleviating factors, radiation, temporal factor, severity (OLDCARTS).
- **Review of Systems (ROS):** Relevant symptoms mentioned by patient.
- **Current Medications / Allergies / Past Medical History:** Only if explicitly mentioned.

### OBJECTIVE
- **Vital Signs:** Mentioned measurements (BP, HR, Temp, SpO2, etc.).
- **Physical Exam Findings:** Observations, exams, or physical maneuvers mentioned by the clinician.
- **Diagnostic / Lab Results:** Any lab or imaging results reviewed during the visit.

### ASSESSMENT
- **Primary Diagnosis / Impression:** Summary of clinical impression based on symptoms discussed.
- **Differential Diagnoses:** Secondary possibilities considered during the encounter.

### PLAN
- **Diagnostic / Labs Ordered:** Tests or imaging requested.
- **Treatment / Interventions:** Medications prescribed/adjusted, therapy, or procedural interventions.
- **Patient Education / Counseling:** Lifestyle advice, warnings, or instructions given.
- **Follow-Up:** Specified return timeline or emergency precautions ("red flags").

TRANSCRIPT:
\"\"\"
{patient_transcript}
\"\"\"
"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5",
                "prompt": prompt,
                "stream": False
            },
            timeout=60.0
        )
        data = response.json()
        summary = data.get("response","")
        scribe_memory.purge_session(session_id)

        return {
            "session_id": session_id,
            "summary": summary,
            "status": "Finalized and purged from volatile RAM"
        }

@router.get("/sessions")
async def get_sessions():
    return scribe_memory.list_active_sessions()

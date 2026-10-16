from faster_whisper import WhisperModel
import io

model = WhisperModel(
        model_size_or_path="base",
        device="cuda",
        compute_type="float16"
)

def transcribe_audio_chunk(audio_bytes: bytes, file_format: str = "wav") -> str:
    audio_buffer = io.BytesIO(audio_bytes)
    audio_buffer.name = f"stream.{file_format}"

    segments, info = model.transcribe(
        audio_buffer,
        beam_size=5,
        vad_filter=True
    )

    full_text = " ".join(segment.text.strip() for segment in segments)

    return full_text
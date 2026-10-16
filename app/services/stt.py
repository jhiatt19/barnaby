import os
import sys
from faster_whisper import WhisperModel
import io
import av
import site

if sys.platform == "win32":
    for site_pkg in site.getsitepackages():
        cublas_dir = os.path.join(site_pkg, "nvidia", "cublas", "bin")
        cudnn_dir = os.path.join(site_pkg, "nvidia", "cudnn", "bin")
        if os.path.exists(cublas_dir):
            os.add_dll_directory(cublas_dir)
        if os.path.exists(cudnn_dir):
            os.add_dll_directory(cudnn_dir)

_original_av_open = av.open

def _patched_av_open(*args, **kwargs):
    # Remove metadata_errors if faster-whisper passes it down
    kwargs.pop("metadata_errors", None)
    return _original_av_open(*args, **kwargs)

av.open = _patched_av_open

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
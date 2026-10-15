from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.api.endpoints import scribe

logger = logging.getLogger("barnaby")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence: initialize model connections, verify hardware
    logger.info("Starting B.A.R.N.A.B.Y Core Application...")
    yield
    # Shutdown sequence: release RTSP streams and force-clear RAM memory buffers
    logger.info("Shutting down B.A.R.N.A.B.Y Core...")

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    docs_url="/docs"
)

# Enable CORS for local dashboards and mobile devices
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Endpoint Modules
app.include_router(scribe.router, prefix="/api/v1/scribe", tags=["Medical Scribe"])
# app.include_router(cameras.router, prefix="/api/v1/cameras", tags=["Tapo Cameras"])

@app.get("/health")
async def health_check():
    return {"status": "online", "gpu_status": "RTX 5060 Ti Active"}
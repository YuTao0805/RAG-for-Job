from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from contextlib import asynccontextmanager
import asyncio

from app.job_sync import WeeklyJobSyncService
from app.rag_matcher import JobMatcherRAG, parse_uploaded_text

BASE_DIR = Path(__file__).resolve().parent.parent
KB_PATH = BASE_DIR / "data" / "job_profiles.json"

matcher = JobMatcherRAG(KB_PATH)
sync_service = WeeklyJobSyncService(KB_PATH)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(sync_service.run_forever())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="RAG Job Matcher", version="1.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/sync-jobs")
def sync_jobs() -> dict[str, int]:
    return sync_service.run_sync()


@app.post("/match-job")
async def match_job(file: UploadFile = File(...), top_k: int = 3) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="上传文件名为空")

    raw_content = await file.read()
    try:
        resume_text = parse_uploaded_text(file.filename, raw_content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="文件内容为空")

    return {
        "filename": file.filename,
        "result": matcher.generate_match_report(resume_text, top_k=top_k),
    }

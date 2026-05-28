from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import json
import redis
from sqlalchemy import create_engine, Column, String, DateTime, JSON, Float, Text, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# ---------- Config ----------
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aetherion:aetherion_secret@postgres:5432/aetherion")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Синхронный движок (не async)
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ---------- Database Models ----------
class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_name = Column(String, nullable=False)
    status = Column(String, default="PENDING")
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=True)
    error_msg = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    total_cost_usd = Column(Float, default=0.0)
    progress = Column(Integer, default=0)


# ---------- Pydantic Schemas ----------
class ExecuteRequest(BaseModel):
    workflow_name: str
    payload: Dict[str, Any] = {}
    async_mode: bool = True


class ExecuteResponse(BaseModel):
    run_id: str
    status: str
    result: Optional[Dict[str, Any]] = None


# ---------- FastAPI App ----------
app = FastAPI(title="Aetherion Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_client = None


# ---------- Lifecycle ----------
@app.on_event("startup")
async def startup():
    global redis_client
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    # Создаем таблицы
    Base.metadata.create_all(bind=engine)
    print("🚀 Aetherion Gateway started")


@app.on_event("shutdown")
async def shutdown():
    if redis_client:
        redis_client.close()


# ---------- API Endpoints ----------
@app.post("/api/v1/execute", response_model=ExecuteResponse)
async def execute_workflow(req: ExecuteRequest):
    run_id = str(uuid.uuid4())

    # Сохраняем в БД
    with SessionLocal() as session:
        run = WorkflowRun(
            id=run_id,
            workflow_name=req.workflow_name,
            input_data=req.payload,
            status="PENDING"
        )
        session.add(run)
        session.commit()

    # Отправляем в Redis
    redis_client.xadd(
        "workflow:queue",
        {
            "run_id": run_id,
            "workflow_name": req.workflow_name,
            "payload": json.dumps(req.payload)
        }
    )

    if not req.async_mode:
        # Ждем результат (простой polling)
        import time
        for _ in range(30):
            time.sleep(1)
            with SessionLocal() as session:
                run = session.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
                if run.status in ["SUCCESS", "FAILED"]:
                    return ExecuteResponse(
                        run_id=run_id,
                        status=run.status,
                        result=run.output_data
                    )
        return ExecuteResponse(run_id=run_id, status="TIMEOUT", result=None)

    return ExecuteResponse(run_id=run_id, status="QUEUED", result=None)


@app.get("/api/v1/result/{run_id}")
async def get_result(run_id: str):
    with SessionLocal() as session:
        run = session.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
        if not run:
            raise HTTPException(404, "Run not found")
        return {
            "run_id": run.id,
            "status": run.status,
            "output": run.output_data,
            "error": run.error_msg,
            "cost": run.total_cost_usd,
            "progress": run.progress
        }


@app.get("/api/v1/metrics")
async def get_metrics():
    with SessionLocal() as session:
        from sqlalchemy import func
        total = session.query(func.count(WorkflowRun.id)).scalar()
        failed = session.query(func.count(WorkflowRun.id)).filter(WorkflowRun.status == "FAILED").scalar()
        total_cost = session.query(func.sum(WorkflowRun.total_cost_usd)).scalar() or 0
        return {
            "total_runs": total or 0,
            "failed_runs": failed or 0,
            "total_cost_usd": float(total_cost)
        }


@app.get("/api/v1/runs")
async def get_runs(limit: int = 10):
    with SessionLocal() as session:
        runs = session.query(WorkflowRun).order_by(WorkflowRun.created_at.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "workflow_name": r.workflow_name,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "result": r.output_data
            }
            for r in runs
        ]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
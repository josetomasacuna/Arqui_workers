import logging
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from celery import Celery
from datetime import datetime
import uuid
from fastapi.responses import JSONResponse


app = FastAPI()
celery_app = Celery('tasks', broker='redis://redis:6379/0', backend='redis://redis:6379/0')
jobs = {}  

# class StockEstimationData(BaseModel):
#     symbol: str
#     price_start: float
#     timestamp_start: str
#     price_end: float
#     timestamp_end: str
#     total_quantity: int

# class JobRequest(BaseModel):
#     user_id: str
#     stocks: Dict[str, StockEstimationData]

@app.get("/heartbeat")
def heartbeat():
    return True

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class AnalysisRequest(BaseModel):
#     symbol: str
#     oldest_price: Optional[float]
#     oldest_timestamp: str
#     recent_price: Optional[float]
#     recent_timestamp: str
#     quantity: int
#     sub: str

# class AnalysisResponse(BaseModel):
#     symbol: str
#     estimated_value: float
#     sub: str

@app.post("/job")
async def recibir_datos(datos: List[dict]):
    print("[JOBMASTER] Recibido POST con datos")
    task = celery_app.send_task("worker.tasks.calcular_estimacion", args=[datos])
    print(f"[JOBMASTER] Tarea enviada con ID: {task.id}")
    return {"status": task.id}

@app.post("/job_result")
def recibir_resultado(result: dict):
    task_id = result["task_id"]
    jobs[task_id] = result["resultado"]
    print(f"[JOBMASTER] Resultado guardado para {task_id}")
    return {"status": "OK"}

@app.get("/job/{job_id}")
def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return jobs[job_id]
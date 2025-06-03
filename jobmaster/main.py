from typing import List
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from celery import Celery
from datetime import datetime
import uuid

app = FastAPI()
celery_app = Celery('tasks', broker='redis://redis:6379/0', backend='redis://redis:6379/0')
jobs = {}  

class JobEstimationPoint(BaseModel):
    symbol: str
    price_start: float
    timestamp_start: str
    price_end: float
    timestamp_end: str
    total_quantity: int

class JobRequest(BaseModel):
    user_id: str
    stocks: List[JobEstimationPoint]
    
@app.get("/heartbeat")
def heartbeat():
    return True

@app.post("/job", response_model=dict)
async def create_job(job: JobRequest, request: Request):
    body = await request.body()
    print("CUERPO RECIBIDO EN JOBMASTER (RAW):")
    print(body.decode("utf-8"))

    # También imprime el objeto ya parseado
    print("OBJETO PARSEADO (Pydantic):")
    print(job)

    request_id = str(uuid.uuid4())
    jobs[request_id] = {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "ACCEPTED",
        "reason": "Tarea encolada",
        "estimations": {},
        "total_estimated_gain": 0.0
    }
    # Encolar tarea en Celery
    celery_app.send_task(
        'tasks.calculate_estimations',
        args=[job.user_id, job.stocks, request_id],
        task_id=request_id
    )
    return jobs[request_id]

@app.get("/job/{job_id}")
def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return jobs[job_id]
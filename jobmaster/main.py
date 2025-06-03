from typing import List, Dict
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from celery import Celery
from datetime import datetime
import uuid
from fastapi.responses import JSONResponse

app = FastAPI()
celery_app = Celery('tasks', broker='redis://redis:6379/0', backend='redis://redis:6379/0')
jobs = {}  

class StockEstimationData(BaseModel):
    symbol: str
    price_start: float
    timestamp_start: str
    price_end: float
    timestamp_end: str
    total_quantity: int

class JobRequest(BaseModel):
    user_id: str
    stocks: Dict[str, StockEstimationData]

@app.get("/heartbeat")
def heartbeat():
    return True

@app.post("/job", response_model=dict)
async def create_job(request: Request):
    body = await request.json()
    print("CUERPO RECIBIDO EN JOBMASTER:")
    print(body)
    # Ahora intenta hacer parse con Pydantic para ver si falla y dónde:
    try:
        job = JobRequest(**body)
    except Exception as e:
        print("Error al parsear JobRequest:", e)
        raise

    # Si llegó hasta acá, sigue como antes
    request_id = str(uuid.uuid4())
    jobs[request_id] = {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "ACCEPTED",
        "reason": "Tarea encolada",
        "estimations": {},
        "total_estimated_gain": 0.0
    }
    # Encolar tarea...

    # Encolar la tarea, con el diccionario de stocks
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
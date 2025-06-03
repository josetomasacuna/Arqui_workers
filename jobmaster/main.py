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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobRequest(BaseModel):
    user_id: str
    stocks: List[StockEstimationData]

@app.post("/job", response_model=dict)
async def create_job(request: Request):
    try:
        body = await request.json()
        logger.info("CUERPO RECIBIDO EN JOBMASTER:\n%s", body)

        job = JobRequest(**body)  # valida los datos y los convierte a objeto Pydantic

        request_id = str(uuid4())
        logger.info(f"Generado request_id: {request_id}")

        jobs[request_id] = {
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "ACCEPTED",
            "reason": "Tarea encolada",
            "estimations": {},
            "total_estimated_gain": 0.0
        }

        # Serializar stocks a dict para enviar por Celery
        stocks_serialized = [stock.dict() for stock in job.stocks]
        logger.info("Datos serializados para Celery:\n%s", stocks_serialized)

        # Enviar tarea a Celery
        celery_app.send_task(
            'tasks.calculate_estimations',
            args=[job.user_id, stocks_serialized, request_id],
            task_id=request_id
        )
        logger.info("Tarea enviada a Celery")

        return jobs[request_id]

    except Exception as e:
        logger.error("Error en create_job: %s", e, exc_info=True)
        return {"error": str(e)}
    
@app.get("/job/{job_id}")
def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return jobs[job_id]
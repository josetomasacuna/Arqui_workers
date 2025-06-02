from celery import Celery
from datetime import datetime
import requests

celery_app = Celery('tasks', broker='redis://redis:6379/0', backend='redis://redis:6379/0')

@celery_app.task
def calculate_estimations(user_id: str, stocks: dict, request_id: str):
    result = {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "OK",
        "reason": "",
        "estimations": {},
        "total_estimated_gain": 0.0
    }

    try:
        for symbol, quantity in stocks.items():
            last_price = get_last_price(symbol)
            month_ago_price = get_month_ago_price(symbol)

            
            m = (last_price - month_ago_price) / 30
            n = last_price
            estimated_price = m * 30 + n  
            estimated_gain = (estimated_price - last_price) * quantity

            result["estimations"][symbol] = {
                "current_price": last_price,
                "estimated_price": estimated_price,
                "quantity": quantity,
                "estimated_gain": estimated_gain
            }
            result["total_estimated_gain"] += estimated_gain

        
        # save_to_db(user_id, result)

        requests.post("http://jobmaster:8000/job", json=result)

    except Exception as e:
        result["status"] = "error"
        result["reason"] = str(e)
        requests.post("http://jobmaster:8000/job", json=result)

    return result

def get_last_price(symbol: str) -> float:
    
    return 100.0

def get_month_ago_price(symbol: str) -> float:
    
    return 90.0

def save_to_db(user_id: str, result: dict):
   
    pass
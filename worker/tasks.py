from celery import Celery
from datetime import datetime
import requests

celery_app = Celery('tasks', broker='redis://redis:6379/0', backend='redis://redis:6379/0')

@celery_app.task
def calculate_estimations(user_id, stocks, request_id):
    results = []
    total_gain = 0.0

    for stock in stocks:
        try:
            # Convert timestamps to seconds since epoch
            t1 = int(datetime.fromisoformat(stock["timestamp_start"]).timestamp())
            t2 = int(datetime.fromisoformat(stock["timestamp_end"]).timestamp())
            p1 = stock["price_start"]
            p2 = stock["price_end"]
            quantity = stock["total_quantity"]

            if t2 == t1:
                gain = 0.0  # Avoid division by zero
            else:
                # Slope
                m = (p2 - p1) / (t2 - t1)
                t_future = t2 + 30 * 24 * 60 * 60
                p_future = p2 + m * (t_future - t2)

                gain = (p_future - p2) * quantity

            results.append({
                "symbol": stock["symbol"],
                "projected_price_30d": round(p_future, 2),
                "estimated_gain": round(gain, 2)
            })

            total_gain += gain

        except Exception as e:
            results.append({
                "symbol": stock.get("symbol", "UNKNOWN"),
                "error": str(e)
            })

    # Guardar resultado en memoria (o DB si estás usando una)
    from jobmaster import jobs  # ← Asegúrate que esto sea posible sin ciclo circular
    if request_id in jobs:
        jobs[request_id]["status"] = "COMPLETED"
        jobs[request_id]["reason"] = "Estimación finalizada"
        jobs[request_id]["estimations"] = results
        jobs[request_id]["total_estimated_gain"] = round(total_gain, 2)

    return results


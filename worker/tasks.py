from celery import Celery
from datetime import datetime
import requests

celery_app = Celery('tasks', broker='redis://redis:6379/0', backend='redis://redis:6379/0')

from datetime import datetime, timedelta

def calcular_estimacion(stock_data):
    print("[CELERY] Recibido stock_data:")
    print(stock_data)

    resumen = []
    total_actual = 0
    total_estimado = 0

    for stock in stock_data:
        print(f"[ESTIMACIÓN] Procesando {stock['symbol']}...")

        fecha1 = datetime.fromisoformat(stock["fecha_antigua"].replace("Z", "+00:00"))
        fecha2 = datetime.fromisoformat(stock["fecha_nueva"].replace("Z", "+00:00"))

        precio1 = stock["precio_antiguo"]
        precio2 = stock["precio_nuevo"]
        cantidad = stock["cantidad"]

        # días entre puntos
        delta_dias = (fecha2 - fecha1).days or 1
        print(f"[ESTIMACIÓN] Días entre fechas: {delta_dias}")

        # pendiente (cambio por día)
        pendiente = (precio2 - precio1) / delta_dias
        print(f"[ESTIMACIÓN] Pendiente: {pendiente}")

        # estimación a 30 días desde fecha2
        fecha_objetivo = fecha2 + timedelta(days=30)
        dias_hacia_futuro = (fecha_objetivo - fecha2).days
        estimado = precio2 + pendiente * dias_hacia_futuro
        print(f"[ESTIMACIÓN] Precio estimado a 30 días: {estimado}")

        valor_actual = precio2 * cantidad
        valor_estimado = estimado * cantidad

        resumen.append({
            "symbol": stock["symbol"],
            "precio_actual": precio2,
            "cantidad": cantidad,
            "valor_actual": round(valor_actual, 2),
            "precio_estimado_30d": round(estimado, 2),
            "valor_estimado": round(valor_estimado, 2),
            "fecha_objetivo": fecha_objetivo.isoformat()
        })

        total_actual += valor_actual
        total_estimado += valor_estimado

    resultado = {
        "acciones": resumen,
        "total_actual": round(total_actual, 2),
        "total_estimado": round(total_estimado, 2)
    }

    requests.post("http://jobmaster:8000/job_result", json={
        "task_id": calcular_estimacion.request.id,
        "resultado": resultado
    })


    return resultado


# @celery_app.task
# def calcular_estimacion(stock_data):
#     print("[CELERY] Recibido stock_data:")
#     print(stock_data)

#     estimaciones = []

#     for stock in stock_data:
#         print(f"[ESTIMACIÓN] Procesando {stock['symbol']}...")

#         fecha1 = datetime.fromisoformat(stock["fecha_antigua"].replace("Z", "+00:00"))
#         fecha2 = datetime.fromisoformat(stock["fecha_nueva"].replace("Z", "+00:00"))

#         precio1 = stock["precio_antiguo"]
#         precio2 = stock["precio_nuevo"]

#         # días entre puntos
#         delta_dias = (fecha2 - fecha1).days or 1
#         print(f"[ESTIMACIÓN] Días entre fechas: {delta_dias}")

#         # pendiente (cambio por día)
#         pendiente = (precio2 - precio1) / delta_dias
#         print(f"[ESTIMACIÓN] Pendiente: {pendiente}")

#         # estimación a 30 días desde fecha2
#         fecha_objetivo = fecha2 + timedelta(days=30)
#         dias_hacia_futuro = (fecha_objetivo - fecha2).days
#         estimado = precio2 + pendiente * dias_hacia_futuro

#         print(f"[ESTIMACIÓN] Precio estimado a 30 días: {estimado}")
#         estimaciones.append({
#             "symbol": stock["symbol"],
#             "estimado_en_30_dias": estimado,
#             "fecha_objetivo": fecha_objetivo.isoformat()
#         })

#     requests.post("http://jobmaster:8000/job_result", json={
#         "task_id": calcular_estimacion.request.id,
#         "resultado": estimaciones
#     })

#     print("[ESTIMACIÓN] Resultados:")
#     for est in estimaciones:
#         print(est)

#     return estimaciones

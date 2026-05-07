FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000
# uvloop: event loop nativo C ~2x más rápido que asyncio default.
# httptools: parser HTTP escrito en C, más rápido que h11.
# limit-concurrency=80: no rechaza conexiones hasta 80 simultáneas
# (default era 200, lo dejamos generoso pero acotado para no agotar pool DB).
# timeout-keep-alive=30: mantiene conexiones HTTP keep-alive abiertas más
# tiempo para reducir overhead TCP en clientes activos.
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--limit-concurrency", "80", \
     "--timeout-keep-alive", "30"]

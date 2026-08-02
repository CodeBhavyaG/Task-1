FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY requirements.txt .
RUN uv init --no-readme --no-workspace && uv add --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

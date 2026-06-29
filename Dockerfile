FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY rank.py validate_submission.py ./
COPY uploads/A1.txt ./uploads/A1.txt
COPY uploads/sample_candidates.json ./uploads/sample_candidates.json
COPY sandbox ./sandbox

RUN pip install --no-cache-dir -r sandbox/requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "sandbox/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]

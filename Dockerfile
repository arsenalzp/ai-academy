FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV LOG_FILE_PATH=logs/queries.jsonl
ENV POLICY_FILE_PATH=governance/policies
ENV KNOWLEDGE_DIR_PATH=data/knowledge

ENTRYPOINT ["python", "src/pipeline.py"]

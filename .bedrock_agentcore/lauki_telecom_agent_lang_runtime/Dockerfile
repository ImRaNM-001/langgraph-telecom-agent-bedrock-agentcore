FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app

ENV UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1 \
    UV_NO_PROGRESS=1 \
    PYTHONUNBUFFERED=1 \
    DOCKER_CONTAINER=1 \
    AWS_REGION=ap-south-1 \
    AWS_DEFAULT_REGION=ap-south-1

# Build needs only these (README is referenced by pyproject's `readme` field)
COPY pyproject.toml README.md ./
COPY src ./src

RUN uv pip install . \
 && uv pip install aws-opentelemetry-distro==0.12.2

# Only files the agent reads at runtime
COPY params.yml ./
COPY data ./data

# logging.py does os.makedirs(<root>/logs) at runtime — needs write access
RUN useradd -m -u 1000 bedrock_agentcore \
 && chown -R bedrock_agentcore:bedrock_agentcore /app
USER bedrock_agentcore

EXPOSE 8080

CMD ["opentelemetry-instrument", "python", "-m", "src.main"]
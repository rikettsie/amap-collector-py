FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --frozen --no-dev --no-install-project

COPY amap_collector/ ./amap_collector/
COPY main.py ./
COPY tests/ ./tests/
RUN uv sync --frozen

COPY bin/docker-entrypoint.sh ./bin/
RUN chmod +x bin/docker-entrypoint.sh

ENTRYPOINT ["./bin/docker-entrypoint.sh"]

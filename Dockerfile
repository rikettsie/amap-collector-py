FROM python:3.14-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY amap_scraper/ ./amap_scraper/
COPY main.py ./
COPY tests/ ./tests/
RUN uv sync --frozen

COPY bin/docker-entrypoint.sh ./bin/
RUN chmod +x bin/docker-entrypoint.sh

ENTRYPOINT ["./bin/docker-entrypoint.sh"]

FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-noto-cjk && rm -rf /var/lib/apt/lists/*
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --uid 10001 --create-home trust \
    && mkdir /srv/data && chown trust:trust /srv/data
COPY --chown=trust:trust app /srv/app
USER trust
EXPOSE 8000
# Managed hosts assign the port at runtime; default to 8000 for a plain `docker run`.
# TRUST_ENV=demo additionally requires TRUST_ORIGIN (the public https origin) and
# refuses citizen report intake — see docs/RELEASE_GATES.md before changing it.
CMD ["sh","-c","exec python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000} --no-access-log --workers 1"]

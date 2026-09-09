FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --uid 10001 --create-home trust \
    && mkdir /srv/data && chown trust:trust /srv/data
COPY --chown=trust:trust app /srv/app
USER trust
EXPOSE 8000
CMD ["python","-m","uvicorn","app.main:create_app","--factory","--host","0.0.0.0","--port","8000","--no-access-log","--workers","1"]

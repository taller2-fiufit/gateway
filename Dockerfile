# https://fastapi.tiangolo.com/deployment/docker/
FROM python:3.11-alpine as requirements-stage

WORKDIR /tmp

RUN pip install poetry
COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes


FROM python:3.11 as production-stage

WORKDIR /code

COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . .

EXPOSE 80

# main.py : app variable
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]

FROM python:3.10

ENV PYTHONUNBUFFERD=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /code

RUN pip install --upgrade pip \
    && pip install pipenv

COPY ./Pipfile /code/Pipfile
COPY ./Pipfile.lock /code/Pipfile.lock

RUN pipenv install --system --deploy --ignore-pipfile

RUN apt -y update
RUN apt -y install libopencv-dev


COPY ./containers/django/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN chmod +x /usr/local/bin/entrypoint.sh
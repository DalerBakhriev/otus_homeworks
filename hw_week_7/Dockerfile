FROM python:3.8
RUN pip install pipenv
COPY Pipfile* /usr/src/
RUN cd /usr/src && pipenv lock --requirements > requirements.txt
RUN pip install -r /usr/src/requirements.txt
ENV PYTHONPATH /usr/src/

COPY .env /usr/src/
COPY hasker /usr/src/hasker

WORKDIR /usr/src/hasker
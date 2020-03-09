FROM python:3.8
RUN pip install pipenv
RUN mkdir /src
COPY Pipfile* /src/
RUN cd /src && pipenv lock --requirements > requirements.txt
RUN pip install -r /src/requirements.txt
ENV PYTHONPATH /src/

COPY .env /src/
COPY hasker /src/hasker

WORKDIR /src/hasker
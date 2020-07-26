FROM python:3.8-slim
RUN pip install pipenv
RUN mkdir /src

COPY Pipfile* /src/
RUN cd /src && pipenv lock --requirements > requirements.txt
RUN pip install -r /src/requirements.txt

COPY .env /src/
COPY . /src/

EXPOSE 8080
WORKDIR /src/
ENV PYTHONPATH /src/hasker

ENTRYPOINT ["sh", "./entrypoint.sh" ]
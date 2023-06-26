FROM python:3.8.17-slim

WORKDIR /app

RUN apt update

RUN apt-get install -y postgresql-client python3-dev --no-install-recommends && \
    apt-get clean -y

RUN pip install --upgrade pip

COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

ADD https://github.com/ufoscout/docker-compose-wait/releases/download/2.12.0/wait /wait
RUN chmod +x /wait

COPY . /app

CMD /wait && python app.py
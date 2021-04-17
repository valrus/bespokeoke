FROM ubuntu:20.04

LABEL maintainer="Ian McCowan <ian@mccowan.space>"

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Los_Angeles

RUN apt-get update
RUN apt-get install -y \
    python3.8=3.8.5-1~20.04.2 \
    python3.8-dev=3.8.5-1~20.04.2 \
    python3-pip=20.0.2-5ubuntu1.1 \
    nginx=1.18.0-0ubuntu1 \
    git=1:2.25.1-1ubuntu3.1 \
    espeak=1.48.04+dfsg-8build1 \
    espeak-data=1.48.04+dfsg-8build1 \
    libespeak1=1.48.04+dfsg-8build1 \
    libespeak-dev=1.48.04+dfsg-8build1 \
  && pip3 install pipenv==2020.11.15 \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Expose port 5000
EXPOSE 5000
ENV PORT 5000

COPY ./ ./app
WORKDIR ./app

RUN pipenv install --skip-lock

CMD exec gunicorn --bind :$PORT wsgi:application --workers 1 --threads 1 --timeout 60

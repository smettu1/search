FROM python:3.10.0a7-slim-buster
RUN mkdir /backend
WORKDIR /backend
COPY . .
#RUN apk add build-base
RUN apt-get update -y
RUN apt-get install -y python3-regex gcc  python3-dev \
    libffi-dev g++ libev-dev python-gevent python-cffi \
    python3-pip python3-venv python3-wheel 
RUN python3 -m pip install cffi
RUN pip install --upgrade pip && \
    pip install -r requirements.txt
RUN python postinstall.py
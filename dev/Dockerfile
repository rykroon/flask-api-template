FROM python:3.8-slim

WORKDIR /app
COPY src .

RUN apt-get update -y && \ 
	apt-get upgrade -y && \
	python -m pip install --upgrade pip && \
	pip install -r requirements.txt

EXPOSE 8000

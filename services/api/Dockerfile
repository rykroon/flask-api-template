FROM python:3.8-slim

WORKDIR /app
COPY dev dev
COPY src src

RUN pip install -r dev/requirements.txt && \
	python dev/nltk_download.py

	#apt-get update -y && \ 
	#apt-get upgrade -y && \
	
EXPOSE 8000

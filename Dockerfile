FROM python:3.12-slim

WORKDIR /usr/local/src/app
COPY src .

RUN apt-get update && \ 
	apt-get upgrade -y && \
	rm -rf /var/lib/apt/lists/* && \
	python -m pip install --upgrade pip && \
	pip install -r requirements.txt

EXPOSE 8000
CMD [ "gunicorn", "--config", "gunicorn.conf.py", "main:create_app()" ]

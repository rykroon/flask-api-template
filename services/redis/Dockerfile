FROM redis:6

RUN apt-get update -y && apt-get install -y redis-server
COPY dev/redis.conf /usr/local/etc/redis/redis.conf
CMD [ "redis-server", "/usr/local/etc/redis/redis.conf" ]

FROM python:3.9-slim-buster

WORKDIR /app
COPY . /app
RUN apt-get update && \
    apt-get -y install ffmpeg && \
    pip install --no-cache-dir -r requirements.txt


EXPOSE 5000
CMD [ "python", "app.py" ]
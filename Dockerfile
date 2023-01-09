FROM python:3.11.0-slim-buster
ARG srcDir=src
WORKDIR /app
COPY $srcDir .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]

FROM python:3.6-stretch
# copy the rest of the app
COPY . /app

# Workdir
WORKDIR /app
RUN pip install -r requirements.txt
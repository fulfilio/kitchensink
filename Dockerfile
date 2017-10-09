FROM python:2.7

# copy the rest of the app
COPY . /app

# Workdir
WORKDIR /app
RUN pip install -r requirements.txt
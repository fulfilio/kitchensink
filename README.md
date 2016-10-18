## Everything but the kitchensink!

We are usually amazed by what our customers build using our APIs.
Most commonly built things include reports which look at data from
a different persepctive, aggregating across different models (sales,
shipment and purchase back orders).

This kitchensink repo is a collection of scripts and flask blueprints
that are starting points for you to build your own kitchensink.

## Getting started

### Clone the repo

```
git clone git@github.com:fulfilio/kitchensink
```

### Install the dependencies

```
cd kitchensink
pip install -r requirements.txt
```

### Set your environment variables

This controls how the app can access your Fulfil.IO account.
Ensure that the user generating the API key has access to the
models needed by your app features.

```
export FULFIL_SUBDOMAIN=YOUR_SUBDOMAIN
export FULFIL_API_KEY=YourApiKey
```

### Run the app

```
python manage.py server
```

## Current features

### Order Items waiting

This report displays order items that are waiting to be shipped


## Production Deployment

### Heroku Deployment

This repo includes a Procfile that can be used to deploy to heroku.

```
heroku create
heroku config:set FULFIL_SUBDOMAIN=YOUR_SUBDOMAIN FULFIL_API_KEY=YourApiKey
```

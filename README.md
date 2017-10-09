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
export FULFIL_APP_ID=YOUR_APP_ID
export FULFIL_APP_SECRET=YOUR_APP_SECRET
export FULFIL_SUBDOMAIN=YOUR_APP_SECRET
export FULFIL_OFFLINE_ACCESS_TOKEN=YOUR_OFFLINE_ACCESS_TOKEN
```

### Generating offline access token

```
python scripts/generate_offline_token.py
```

### Run the app

```
python manage.py server
```

## Current features

### Order Items waiting

This report displays order items that are waiting to be shipped.

### Order Items waiting by region

Shows item waiting on a map.

### Product availability dates

Shows details on when product will be in stock next.


## Production Deployment

### Heroku Deployment

This repo includes a Procfile that can be used to deploy to heroku.

```
heroku create
heroku config:set FULFIL_SUBDOMAIN=YOUR_SUBDOMAIN FULFIL_APP_ID=YOUR_APP_ID FULFIL_APP_SECRET=YOUR_APP_SECRET FULFIL_OFFLINE_ACCESS_TOKEN=YOUR_OFFLINE_ACCESS_TOKEN
```

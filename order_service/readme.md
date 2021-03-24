# Setup
```
pipenv install
pipenv run pip install 'asyncapi[http,yaml,redis,subscriber,docs]'
```

# Run
```
PYTHONPATH=. FLASK_DEBUG=1 FLASK_APP=order_service/app.py pipenv run flask run

```

or simply 
```
PYTHONPATH=. python order_service/app.py
```


# Rub Celery worker (to listen for saga replies)
```
PYTHONPATH=. pipenv run celery -A order_service.app.create_order_saga_responses_celery_app worker
```

# Run API docs server 
```
PYTHONPATH=. asyncapi-docs --api-module order_service.asyncapi_specification

curl http://127.0.0.1:5000/asyncapi.yaml
```
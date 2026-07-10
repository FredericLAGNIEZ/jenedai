




## Access the MLflow UI

Open your browser at:

```
http://127.0.0.1:5000
```

Only the **Default** experiment will be listed on first launch.

---

## Set the Tracking URI in your code

```python
mlflow.set_tracking_uri("http://127.0.0.1:5000")
```

Call this before any `mlflow.log_*` or `mlflow.start_run()` call. It tells the MLflow client where to send tracking data.

---

## Cloud MLflow Tracking Server

### Start the server with Docker

```bash
# coming soon
```


## 
Adresse de suivi mlflow :
 https://jenedai-mlflow.hf.space/



# TODO: Evidently AI, PREDICTION
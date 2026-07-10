#!/bin/bash
# export MLFLOW_S3_ENDPOINT_URL=http://localhost:3900
export MLFLOW_S3_ENDPOINT_URL=https://garage.learndatascience.cloud
export AWS_ACCESS_KEY_ID="GKc09b7d0b9648439df630263f"
export AWS_SECRET_ACCESS_KEY="12cb8fdb0878dd3abe634e3ec7706022a8a18afc7b3b3283c0070f5272f20988"
export AWS_DEFAULT_REGION=garage

mlflow server \
  --backend-store-uri postgresql://frederic:frederic@localhost:5432/mlflow \
  --default-artifact-root s3://jenedai/ \
  --host 0.0.0.0 \
  --port 5000
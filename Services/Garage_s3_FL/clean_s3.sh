#!/bin/bash
export MLFLOW_S3_ENDPOINT_URL=https://garage.learndatascience.cloud
export AWS_ACCESS_KEY_ID="GKc09b7d0b9648439df630263f"
export AWS_SECRET_ACCESS_KEY="12cb8fdb0878dd3abe634e3ec7706022a8a18afc7b3b3283c0070f5272f20988"
export AWS_DEFAULT_REGION=garage

# Lister et supprimer tous les objets sous 1/models/
aws s3 rm s3://jenedai/1/models/ \
  --recursive \
  --endpoint-url $MLFLOW_S3_ENDPOINT_URL

# Lister et supprimer tous les objets sous 1/models/
aws s3 rm s3://jenedai/2/models/ \
  --recursive \
  --endpoint-url $MLFLOW_S3_ENDPOINT_URL

echo "✅ Nettoyage terminé"
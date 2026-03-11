# Dockerfile for Apache Airflow
# This Dockerfile is used to create a Docker image for running an Apache Airflow server.
# Airflow is a platform to programmatically author, schedule, and monitor workflows.
# The Dockerfile sets up the necessary environment and dependencies for running Airflow, and it includes security best practices by creating a non-root user to run the server.
# The resulting Docker image can be used to deploy Airflow in a containerized environment, such as Kubernetes or Docker Compose.

# Use an official Airflow image as base
FROM apache/airflow:2.10.4
#FROM python:3.10-slim

# Set environment variables stored in Hugging Face
ARG AIRFLOW_ADMIN_USER
ARG AIRFLOW_ADMIN_PASSWORD
#ARG AIRFLOW__WEBSERVER__SECRET_KEY
#ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=$AIRFLOW_POSTGRES_URL?

# Set environment variables
ENV AIRFLOW_HOME=/opt/airflow
ENV AIRFLOW__WEBSERVER__WEB_SERVER_PORT=7860
ENV AIRFLOW__CORE__TEST_CONNECTION=Enabled

# Webserver Configuration
ENV AIRFLOW__WEBSERVER__SECRET_KEY=super-long-random-secret
ENV AIRFLOW__WEBSERVER__BASE_URL=https://sustcoop-airflow.hf.space
ENV AIRFLOW__WEBSERVER__ENABLE_PROXY_FIX=True
ENV AIRFLOW__WEBSERVER__SESSION_COOKIE_SECURE=True
ENV AIRFLOW__WEBSERVER__SESSION_COOKIE_HTTPONLY=True
ENV AIRFLOW__WEBSERVER__SESSION_COOKIE_SAMESITE=Lax

# RAM optimisation
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
ENV AIRFLOW__WEBSERVER__WORKERS=1
ENV AIRFLOW__CORE__EXECUTOR=SequentialExecutor
ENV AIRFLOW__WEBSERVER__WORKER_CLASS=gevent

# Avoid killing process -> useful in slow environment (default value 120)
ENV AIRFLOW__WEBSERVER__WEB_SERVER_MASTER_TIMEOUT=300

# Switch user
USER root

# Change the UID of airflow user to 1000
RUN usermod -u 1000 airflow

# Switch back to airflow user
USER airflow

# Install Python dependencies
# The requirements.txt file should include apache-airflow and any other dependencies needed for Airflow to run properly.
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

# COPY DAGS
COPY ./dags /opt/airflow/dags

# Initialize Airflow database (only needed if using LocalExecutor or SequentialExecutor)
# This step is optional and can be moved to an entrypoint script if needed.
RUN airflow db migrate

# Expose the necessary ports (optional if Hugging Face already handles port exposure)
EXPOSE 7860

# Run Airflow webserver and scheduler
# Note: The command below assumes the use of the LocalExecutor.
# For production, consider using CeleryExecutor or KubernetesExecutor.
# Start Airflow webserver and scheduler within the same container
CMD ["bash", "-c", "airflow users create --username $AIRFLOW_ADMIN_USER --firstname $AIRFLOW_ADMIN_USER --lastname $AIRFLOW_ADMIN_USER --role Admin --email ${AIRFLOW_ADMIN_USER}@sustcoop.fr --password $AIRFLOW_ADMIN_PASSWORD || echo 'User exists' && airflow scheduler & airflow webserver"]

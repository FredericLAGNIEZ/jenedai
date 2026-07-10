# Dockerfile for Apache Airflow
# This Dockerfile is used to create a Docker image for running an Apache Airflow server.
# Airflow is a platform to programmatically author, schedule, and monitor workflows.
# The Dockerfile sets up the necessary environment and dependencies for running Airflow, and it includes security best practices by creating a non-root user to run the server.
# The resulting Docker image can be used to deploy Airflow in a containerized environment, such as Kubernetes or Docker Compose.

# Use an official Airflow image as base
FROM apache/airflow:2.10.4
#FROM python:3.10-slim

ARG AIRFLOW_ADMIN_USER
ARG AIRFLOW_ADMIN_PASSWORD
ARG AIRFLOW_POSTGRES_URL
ARG AIRFLOW__DATABASE__SQL_ALCHEMY_CONN

# Set environment variables
#ENV AIRFLOW_HOME=/opt/airflow
#ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
#ENV AIRFLOW__CORE__EXECUTOR=SequentialExecutor
#ENV AIRFLOW__WEBSERVER__WEB_SERVER_MASTER_TIMEOUT=300
#ENV AIRFLOW__WEBSERVER__WORKER_CLASS=gevent
#ENV AIRFLOW__WEBSERVER__WEB_SERVER_PORT=7860
#ENV AWS_DEFAULT_REGION=eu-west-3
#ENV AIRFLOW__CORE__TEST_CONNECTION: 'Enabled'

# Switch user
USER root

# Change the UID of airflow user to 1000
RUN usermod -u 1000 airflow

# Ensure correct permissions for the .pem file
# RUN chmod 400 /opt/airflow/<YOUR_KEY_PAIR_NAME>.pem \
#    && chown airflow /opt/airflow/<YOUR_KEY_PAIR_NAME>.pem

# Switch back to airflow user
USER airflow

# Install Python dependencies
# The requirements.txt file should include apache-airflow and any other dependencies needed for Airflow to run properly.
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

# COPY DAGS
COPY ./dags /opt/airflow/dags

# COPY PEM key
# COPY secrets/<YOUR_KEY_PAIR_NAME>.pem /opt/airflow/


# Initialize the Airflow database (PostgreSQL in this case)
# IF YOU WANT TO HAVE THAT RUNNING IN HUGGINGFACE, YOU NEED TO HARD CODE THE VALUE HERE UNFORTUNATELY
# DON'T STAGE THAT IN A PRIVATE REPO BECAUSE THE ENV VARIABLE IS HARD CODED IN PLAIN TEXT
# IF YOU STAGE THAT IN HUGGING FACE SPACE, YOU DON'T HAVE A CHOICE THOUGH
# SO MAKE SURE YOUR SPACE IS PRIVATE

# RUN --mount=type=secret,id=AIRFLOW_POSTGRES_URL,mode=0444,required=true \
#    ENV AIRFLOW_POSTGRES_URL=$(cat /run/secrets/AIRFLOW_POSTGRES_URL)

#ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=$AIRFLOW_POSTGRES_URL

# Initialize Airflow database (only needed if using LocalExecutor or SequentialExecutor)
# This step is optional and can be moved to an entrypoint script if needed.
RUN airflow db migrate

# Create default admin user for Airflow (username: $AIRFLOW_ADMIN_USER, password: $AIRFLOW_ADMIN_PASSWORD)
# RUN --mount=type=secret,id=AIRFLOW_ADMIN_USER,mode=0444,required=true \
#    --mount=type=secret,id=AIRFLOW_ADMIN_PASSWORD,mode=0444,required=true \
#    airflow users create \
#       --username $(cat /run/secrets/AIRFLOW_ADMIN_USER) \
#       --firstname Admin \
#       --lastname User \
#       --role Admin \
#       --email admin@example.com \
#       --password $(cat /run/secrets/AIRFLOW_ADMIN_PASSWORD)

# Expose the necessary ports (optional if Hugging Face already handles port exposure)
EXPOSE 7860

# # 2. Crée ou réinitialise l'utilisateur admin
# RUN airflow users create \
#     --username admin \
#     --firstname Admin \
#     --lastname User \
#     --role Admin \
#     --email admin@example.com \
#     --password qv2B6ZV2NQKPgen3 \
#     || airflow users reset-password \
#     --username admin \
#     --password qv2B6ZV2NQKPgen3

# # 3. Configure les cookies de session
# ENV AIRFLOW__WEBSERVER__SESSION_COOKIE_DOMAIN=.sustcoop-airflow.hf.space
# ENV AIRFLOW__WEBSERVER__SESSION_COOKIE_SECURE=True
# ENV AIRFLOW__WEBSERVER__SESSION_COOKIE_HTTPONLY=True
# ENV AIRFLOW__WEBSERVER__SESSION_COOKIE_SAMESITE=Lax

# # 4. Active explicitement RBAC
# ENV AIRFLOW__WEBSERVER__RBAC=True

# 5. Mets à jour les dépendances
#RUN pip install --upgrade pip && \
#    pip install --upgrade apache-airflow && \
#    pip install --upgrade apache-airflow-providers-*

# Run Airflow webserver and scheduler
# Note: The command below assumes the use of the LocalExecutor.
# For production, consider using CeleryExecutor or KubernetesExecutor.
# Start Airflow webserver and scheduler within the same container
CMD ["bash", "-c", "airflow scheduler & airflow webserver"]
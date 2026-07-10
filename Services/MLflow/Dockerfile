# Dockerfile for mlflow server
# This Dockerfile is used to create a Docker image for running an mlflow server.
# The mlflow server is a tool for managing the machine learning lifecycle, including experimentation, reproducibility, and deployment.
# The Dockerfile sets up the necessary environment and dependencies for running the mlflow server, and it also includes security best practices by creating a non-root user to run the server.
# The resulting Docker image can be used to deploy the mlflow server in a containerized environment, such as Hugging Face Spaces or any other container orchestration platform.
# The mlflow server will be configured to use a PostgreSQL database as the backend store for tracking experiments and an S3 bucket for storing artifacts.
# The configuration is done through environment variables, allowing for flexibility and security in managing the connection details for the database and artifact storage.

# Remainning actions to do:
# - Check if a health check can be implemented for the mlflow server to ensure that it is running properly and can respond to requests.
# - Check behavior if  $MLFLOW_POSTGRESS_URI is retrieved directly from the Secrets?

FROM python:3.10-slim

# Set working directory
# The working directory is set to /app, which is where the application code will be copied and executed. This helps to keep the container organized and ensures that all commands are run in the correct context.
# The WORKDIR instruction also creates the directory if it does not exist, so there is no need to create it separately.
# Setting the working directory early in the Dockerfile also allows for better caching of layers, as subsequent instructions will be run in the context of the /app directory.
# This is a common practice in Dockerfiles to ensure that the application code is organized and that all commands are executed in the correct context.
# The choice of /app as the working directory is arbitrary and can be changed to any other directory as needed. However, /app is a common convention for application code in Docker containers.
# Setting the working directory also helps to avoid issues with file paths and permissions, as all commands will be run in the context of the /app directory. This can help to prevent errors and ensure that the application runs smoothly.
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
# The requirements.txt file should be in the same directory as the Dockerfile
# it should list mlflow and any other dependencies needed for the mlflow server to run properly.
COPY requirements.txt .

# Install Python dependencies
# The --no-cache-dir option is used to prevent pip from caching the packages, which can save space in the Docker image.
RUN pip install --no-cache-dir -r requirements.txt

# Create mlflow user for security
# Running the mlflow server as a non-root user is a good security practice, as it limits the permissions of the process and reduces the potential attack surface. By creating a dedicated user for mlflow, we can ensure that the server runs with only the necessary permissions and cannot access sensitive files or directories on the host system.
# The useradd command is used to create a new user named mlflow with a home directory and a specific user ID (1000). This user will be used to run the mlflow server, and it will have limited permissions to ensure the security of the container.
RUN useradd -m -u 1000 mlflow

# Switch to mlflow user
# The USER instruction is used to switch to the mlflow user, which was created in the previous step. This ensures that all subsequent commands and processes will be run as the mlflow user, which has limited permissions for security purposes.
USER mlflow

# Expose port
# The mlflow server will listen on port 7860, so we need to expose this port in the Dockerfile to allow external access to the server. This is done using the EXPOSE instruction, which informs Docker that the container will listen on the specified port at runtime. When running the container, you can map this port to a port on the host machine to access the mlflow server from outside the container.
# The choice of port 7860 seems to be the one to be used on Hugging Face Spaces
EXPOSE 7860

# Health check -> Not sure if it can be useful...
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

#Use environment variable for backend store URI, which should be set when running the container.
#This allows for more flexibility and security, as the URI can be kept secret and not hardcoded in the Dockerfile.
#https://huggingface.co/docs/hub/spaces-sdks-docker#secrets-and-variables-management
#ARG MLFLOW_POSTGRESS_URI -> Seems to be useless $MLFLOW_POSTGRESS_URI retrieve it directly?
ARG AWS_DEFAULT_REGION
ARG AWS_REGION
ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG MLFLOW_S3_ENDPOINT_URL

# Run mlflow server with environment variable for backend store URI
# Note: The backend store URI should point to a PostgreSQL database, and the default artifact root should point to an S3 bucket for storing artifacts.
# The use of the table syntx [mlflow...] was not working, so we switched to the use of environment variable directly in the command.
# --default-artifact-root "s3://mlflow-artifacts/" seems to store i in Huggin Face Spaces, but it is not clear where exactly.
# It is possible that it is stored in a temporary location that is not accessible after the container is stopped, so it may be necessary to configure a persistent storage solution for the artifacts if they need to be retained after the container is stopped.
# As of now it have been persistent after a crash and after a Restart Space, but it is not clear if it will be persistent after a complete stop of the Space.
CMD mlflow server --host 0.0.0.0 --port 7860 --backend-store-uri $MLFLOW_POSTGRESS_URI --default-artifact-root "s3://mlflow-artifacts/"

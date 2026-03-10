#!/usr/bin/env python3
"""
Update secrets in HuggingFace Spaces
Triggers when .github/scripts/secrets/ changes
Distributes AWS credentials + service-specific secrets to each space
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import HfApi

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def get_services():
    """Read service list from .env ServicesNames variable"""
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)
    
    services_str = os.getenv("ServicesNames", "")
    if not services_str:
        print("[ERR] ServicesNames not defined in .env")
        return []
    
    return [s.strip() for s in services_str.split(",") if s.strip()]

def get_shared_secrets():
    """Get AWS shared credentials"""
    return {
        "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID", ""),
        "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
    }

def get_service_secrets(service):
    """Get service-specific secrets from environment (e.g., AIRFLOW_PASSWORD)"""
    # Mapping of service -> environment variables
    service_secrets_map = {
        "Airflow": ["AIRFLOW_ADMIN_PASSWORD", "AIRFLOW_DATABASE_URL"],
        "MLflow": ["MLFLOW_TRACKING_USERNAME", "MLFLOW_TRACKING_PASSWORD"],
        "JupyterLab": ["JUPYTER_TOKEN", "JUPYTER_PASSWORD"],
        "Streamlit": ["STREAMLIT_SERVER_HEADLESS", "STREAMLIT_LOGGER_LEVEL"],
        "n8n": ["N8N_USER_MANAGEMENT_JWT_SECRET", "N8N_ENCRYPTION_KEY"],
    }
    
    secrets = {}
    env_vars = service_secrets_map.get(service, [])
    
    for env_var in env_vars:
        value = os.getenv(env_var)
        if value:
            secrets[env_var] = value
    
    return secrets

def add_space_secret(api, space_id, secret_name, secret_value):
    """Add or update a secret in a HuggingFace Space"""
    try:
        api.add_space_secret(
            repo_id=space_id,
            key=secret_name,
            value=secret_value
        )
        print(f"[OK] Secret '{secret_name}' updated in '{space_id}'")
        return True
    except Exception as e:
        print(f"[ERR] Failed to update secret '{secret_name}': {str(e)}")
        return False

def main():
    """Main function: update secrets in all spaces"""
    token = os.getenv("HF_TOKEN")
    if not token:
        print("[ERR] HF_TOKEN environment variable not set")
        sys.exit(1)
    
    api = HfApi(token=token)
    username = api.whoami()["name"]
    
    services = get_services()
    if not services:
        print("[*] No services configured in .env")
        return
    
    shared_secrets = get_shared_secrets()
    
    print("[*] Updating secrets in spaces...")
    print("=" * 60)
    
    for service in services:
        space_id = f"{username}/{service}"
        print(f"\n[*] Processing space: {space_id}")
        
        # Add shared AWS secrets
        for secret_name, secret_value in shared_secrets.items():
            if secret_value:
                add_space_secret(api, space_id, secret_name, secret_value)
        
        # Add service-specific secrets
        service_secrets = get_service_secrets(service)
        for secret_name, secret_value in service_secrets.items():
            add_space_secret(api, space_id, secret_name, secret_value)
    
    print("\n" + "=" * 60)
    print("[OK] Secrets update completed")

if __name__ == "__main__":
    main()

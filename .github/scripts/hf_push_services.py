#!/usr/bin/env python3
"""
Push service files to HuggingFace Spaces
Triggers when Services/** or .env changes
Only pushes if actual changes exist (git diff check)
Copies .env to each service before pushing
"""

import os
import sys
import subprocess
import shutil
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

def has_changes(path):
    """Check if there are changes between HEAD~1 and HEAD in a path"""
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD~1", "HEAD", "--quiet", path],
            capture_output=True,
            cwd=str(Path(__file__).parent.parent.parent)
        )
        return result.returncode != 0
    except Exception as e:
        print(f"[ERR] Git diff check failed: {str(e)}")
        return False

def push_service_to_hf(api, service, username):
    """Push service directory to HuggingFace Space (includes .env)"""
    service_path = Path(__file__).parent.parent.parent / "Services" / service
    repo_root = Path(__file__).parent.parent.parent
    env_file = repo_root / ".env"
    
    if not service_path.exists():
        print(f"[ERR] Service directory not found: {service_path}")
        return False
    
    try:
        # Copier .env dans le dossier service avant upload
        if env_file.exists():
            service_env_path = service_path / ".env"
            shutil.copy2(env_file, service_env_path)
            print(f"[*] Copied .env to {service}")
        
        space_id = f"{username}/{service}"
        
        # Upload the entire service directory to the space
        api.upload_folder(
            folder_path=str(service_path),
            repo_id=space_id,
            repo_type="space",
            commit_message=f"Update {service} from repository"
        )
        
        # Nettoyer: supprimer le .env copié localement (ne pas le commiter)
        service_env_path = service_path / ".env"
        if service_env_path.exists():
            service_env_path.unlink()
        
        print(f"[OK] '{service}' pushed to HuggingFace Space")
        return True
    except Exception as e:
        print(f"[ERR] Failed to push '{service}': {str(e)}")
        return False

def main():
    """Main function: push only services with changes"""
    token = os.getenv("HF_TOKEN")
    if not token:
        print("[ERR] HF_TOKEN environment variable not set")
        sys.exit(1)
    
    api = HfApi(token=token)
    
    try:
        username = api.whoami()["name"]
    except Exception as e:
        print(f"[ERR] Failed to authenticate with HuggingFace: {str(e)}")
        sys.exit(1)
    
    services = get_services()
    if not services:
        print("[*] No services configured in .env")
        return
    
    # Check for changes in Services directory or .env
    services_dir = Path(__file__).parent.parent.parent / "Services"
    env_file = Path(__file__).parent.parent.parent / ".env"
    
    print("[*] Checking for changes...")
    print("=" * 60)
    
    services_to_push = []
    
    # If .env changed, push all services
    if has_changes(str(env_file)):
        print("[*] .env has changed - will push all services")
        services_to_push = services
    else:
        # Check each service directory for changes
        for service in services:
            service_path = services_dir / service
            if service_path.exists() and has_changes(str(service_path)):
                print(f"[*] Changes detected in '{service}'")
                services_to_push.append(service)
    
    if not services_to_push:
        print("[*] No changes detected, skipping push")
        return
    
    print("=" * 60)
    print(f"[*] Pushing {len(services_to_push)} service(s)...")
    print("=" * 60)
    
    success_count = 0
    for service in services_to_push:
        if push_service_to_hf(api, service, username):
            success_count += 1
    
    print("=" * 60)
    print(f"[*] Pushed {success_count}/{len(services_to_push)} services")

if __name__ == "__main__":
    main()

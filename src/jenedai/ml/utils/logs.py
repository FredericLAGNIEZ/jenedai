
import os
import logging
from rich.logging import RichHandler, Console
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime

import sys
from pathlib import Path

# Chemin absolu vers le dossier contenant vos modules
chemin_module = Path(__file__).resolve().parent
# Ajouter le chemin à sys.path
sys.path.append(str(chemin_module))

from get_console import get_console

def configure_logging(
    path_logs: str,
    name: str,
    profile: str = "basic",  # "basic" ou "production"
    level: int = logging.DEBUG,
) -> logging.Logger:
    """
    Configure un logger avec Rich console et option de rotation des logs.

    Args:
        path_logs: Répertoire pour stocker les logs.
        name: Nom du logger (généralement __name__).
        profile: "basic" (fichier simple) ou "production" (rotation par taille/temps).
        level: Niveau minimal de logging (par défaut: DEBUG).

    Returns:
        Instance configurée du logger.
    """
    logger = logging.getLogger(name)

    # Évite d'ajouter plusieurs fois les handlers
    if logger.handlers:
        return logger

    logger.setLevel(level)
    os.makedirs(path_logs, exist_ok=True)

    # 1. Rich console (toujours activée)
    console = get_console()
    rich_handler = RichHandler(
        console=console,
        show_path=False,
        rich_tracebacks=True,
        markup=True
    )
    rich_handler.setLevel(logging.INFO)
    logger.addHandler(rich_handler)

    # 2. Formatter commun pour les fichiers
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    )

    if profile == "basic":
        # Fichier simple avec timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_filename = os.path.join(path_logs, f"{name}_{timestamp}.log")
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    elif profile == "production":
        # Rotation par taille (10 Mo, 5 sauvegardes)
        size_log_filename = os.path.join(path_logs, f"{name}_size_rotation.log")
        size_handler = RotatingFileHandler(
            filename=size_log_filename,
            maxBytes=10 * 1024 * 1024,  # 10 Mo
            backupCount=5,
        )
        size_handler.setLevel(logging.DEBUG)
        size_handler.setFormatter(file_formatter)
        logger.addHandler(size_handler)

        # Rotation par temps (quotidienne, 7 jours de sauvegarde)
        time_log_filename = os.path.join(path_logs, f"{name}_time_rotation.log")
        time_handler = TimedRotatingFileHandler(
            filename=time_log_filename,
            when="midnight",
            interval=1,
            backupCount=7,
        )
        time_handler.setLevel(logging.INFO)
        time_handler.setFormatter(file_formatter)
        logger.addHandler(time_handler)

    else:
        raise ValueError(f"Profil inconnu: {profile}. Utilisez 'basic' ou 'production'.")

    return logger


from pathlib import Path


def find_project_directory():
    """
    Détermine le répertoire du projet.
    """
    # Récupérer le chemin d'accès du répertoire courant
    current_dir = Path.cwd()
    # Accéder au répertoire parent (équivalent de os.pardir)
    parent_dir = current_dir.parent

    return parent_dir

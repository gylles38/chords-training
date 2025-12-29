# progress_manager.py

import json
import os

PROGRESS_FILE = "user_progress.json"

def load_progress():
    """
    Charge la progression de l'utilisateur depuis le fichier JSON.
    Si le fichier n'existe pas, initialise la progression à la première étape (index 0).
    """
    if not os.path.exists(PROGRESS_FILE):
        return {"current_step": 0}
    try:
        with open(PROGRESS_FILE, 'r') as f:
            progress = json.load(f)
            # Vérifier que la clé 'current_step' existe
            if 'current_step' not in progress:
                return {"current_step": 0}
            return progress
    except (json.JSONDecodeError, IOError):
        # En cas de fichier corrompu ou illisible, on repart de zéro
        return {"current_step": 0}

def save_progress(step_index):
    """
    Sauvegarde la progression de l'utilisateur (l'index de l'étape actuelle) dans le fichier JSON.
    """
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({"current_step": step_index}, f)

def get_current_step():
    """
    Retourne l'index de l'étape actuelle de l'utilisateur.
    """
    progress = load_progress()
    return progress.get("current_step", 0)

def advance_to_next_step():
    """
    Fait avancer l'utilisateur à l'étape suivante et sauvegarde la progression.
    """
    current_step = get_current_step()
    save_progress(current_step + 1)

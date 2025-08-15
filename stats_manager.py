import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# Détermine un chemin stable vers le fichier de stats dans le dossier data/
STATS_FILE_PATH = os.path.join(os.path.dirname(__file__), "data", "stats.json")


def _ensure_stats_dir_exists() -> None:
    stats_dir = os.path.dirname(STATS_FILE_PATH)
    if not os.path.isdir(stats_dir):
        os.makedirs(stats_dir, exist_ok=True)


def load_stats() -> Dict[str, Any]:
    """Charge le fichier de statistiques persistant. Retourne un dict vide si absent/corrompu."""
    try:
        if not os.path.isfile(STATS_FILE_PATH):
            return {}
        with open(STATS_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # En cas de problème de lecture/JSON, repartir d'un dictionnaire vide
        return {}


def save_stats(stats: Dict[str, Any]) -> None:
    """Écrit le dictionnaire de stats complet sur disque, de manière robuste."""
    try:
        _ensure_stats_dir_exists()
        tmp_path = STATS_FILE_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, STATS_FILE_PATH)
    except Exception:
        # Éviter tout crash si l'écriture échoue
        pass


def update_mode_record(mode_key: str, accuracy_percent: float, attempts: int) -> Tuple[bool, Optional[float], float]:
    """
    Met à jour le record de précision pour un mode donné.

    - mode_key: nom du mode (ex: 'CadenceMode')
    - accuracy_percent: précision en pourcentage (0.0 à 100.0)
    - attempts: nombre total de tentatives de la session (utilisé comme bris d'égalité)

    Retourne (is_new_record, previous_best_percent_or_None, new_best_percent)
    """
    stats = load_stats()
    mode_stats = stats.get(mode_key, {})

    prev_best = mode_stats.get("best_accuracy_percent")
    prev_best_attempts = mode_stats.get("best_accuracy_attempts", 0)

    is_better = False
    if prev_best is None:
        is_better = True
    elif accuracy_percent > float(prev_best):
        is_better = True
    elif accuracy_percent == float(prev_best) and attempts > int(prev_best_attempts):
        # Même précision, mais établi sur plus de tentatives → considérer comme meilleure robustesse
        is_better = True

    if is_better:
        mode_stats.update({
            "best_accuracy_percent": float(accuracy_percent),
            "best_accuracy_attempts": int(attempts),
            "best_accuracy_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        })
        stats[mode_key] = mode_stats
        save_stats(stats)
        return True, prev_best, float(accuracy_percent)

    return False, prev_best, float(prev_best) if prev_best is not None else float(accuracy_percent)


def update_stopwatch_record(mode_key: str, elapsed_seconds: float, attempts: int):
    """
    Met à jour le record de temps écoulé (chronomètre) pour un mode donné.
    Amélioration = temps plus court, en comparant aussi le nombre de tentatives.

    Critères d'amélioration:
    - Si aucun record → améliorer
    - Si attempts > prev_attempts et elapsed_seconds <= prev_time → améliorer
    - Si attempts == prev_attempts et elapsed_seconds < prev_time → améliorer

    Retourne (is_new_record, previous_best_seconds_or_None, new_best_seconds)
    """
    stats = load_stats()
    mode_stats = stats.get(mode_key, {})

    prev_best = mode_stats.get("best_stopwatch_time_seconds")
    prev_best_attempts = mode_stats.get("best_stopwatch_attempts", 0)

    is_better = False
    if prev_best is None:
        is_better = True
    else:
        prev_time = float(prev_best)
        prev_attempts = int(prev_best_attempts)
        if attempts > prev_attempts and elapsed_seconds <= prev_time:
            is_better = True
        elif attempts == prev_attempts and elapsed_seconds < prev_time:
            is_better = True

    if is_better:
        mode_stats.update({
            "best_stopwatch_time_seconds": float(elapsed_seconds),
            "best_stopwatch_attempts": int(attempts),
            "best_stopwatch_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        })
        stats[mode_key] = mode_stats
        save_stats(stats)
        return True, prev_best, float(elapsed_seconds)

    return False, prev_best, float(prev_best) if prev_best is not None else float(elapsed_seconds)


def update_timer_remaining_record(mode_key: str, remaining_seconds: float):
    """
    Met à jour le record de temps restant (minuteur) pour un mode donné.
    Amélioration = plus de temps restant.

    Retourne (is_new_record, previous_best_seconds_or_None, new_best_seconds)
    """
    stats = load_stats()
    mode_stats = stats.get(mode_key, {})

    prev_best = mode_stats.get("best_timer_remaining_seconds")

    is_better = False
    if prev_best is None:
        is_better = True
    elif remaining_seconds > float(prev_best):
        is_better = True

    if is_better:
        mode_stats.update({
            "best_timer_remaining_seconds": float(remaining_seconds),
            "best_timer_remaining_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        })
        stats[mode_key] = mode_stats
        save_stats(stats)
        return True, prev_best, float(remaining_seconds)

    return False, prev_best, float(prev_best) if prev_best is not None else float(remaining_seconds)
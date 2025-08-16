# settings.py
class Settings:
    """Classe pour stocker les paramètres de l'application."""
    def __init__(self):
        self.use_timer = False
        self.timer_duration = 30.0
        self.play_progression_before_start = 'SHOW_AND_PLAY' # 'SHOW_AND_PLAY', 'PLAY_ONLY', 'NONE'
        self.chord_set_choice = 'basic' # 'basic' ou 'all'
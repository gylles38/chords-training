import sys

from rich.console import Console
from rich.prompt import Prompt

# Importation des bibliothèques spécifiques à la plateforme pour la saisie non-bloquante
try:
    import msvcrt
except ImportError:
    # Pour les systèmes Unix (Linux, macOS)
    import select
    import tty
    import termios

console = Console()

# ---------- Gestion du mode raw permanent ----------
_fd = sys.stdin.fileno()
_old_settings = None

def enable_raw_mode():
    """Passe le terminal en mode raw permanent (désactive écho et mode ligne)."""
    global _old_settings
    _old_settings = termios.tcgetattr(_fd)
    tty.setraw(_fd)
    new_settings = termios.tcgetattr(_fd)
    new_settings[3] &= ~(termios.ECHO | termios.ICANON)  # pas d'écho, pas de mode ligne
    termios.tcsetattr(_fd, termios.TCSADRAIN, new_settings)

def disable_raw_mode():
    """Restaure le mode normal du terminal."""
    if _old_settings:
        termios.tcsetattr(_fd, termios.TCSADRAIN, _old_settings)

# ---------- Fonctions de lecture clavier ----------
def wait_for_input(timeout=0.05):
    """Saisie de caractère non-bloquante sans affichage et sans saut de ligne."""
    if select.select([sys.stdin], [], [], timeout)[0]:
        ch = sys.stdin.read(1)
        # On ignore retour chariot et newline
        if ch in ('\n', '\r'):
            return None
        return ch
    return None

def wait_for_any_key(inport):
    """Attend n'importe quelle touche du clavier (non bloquant sur le MIDI)."""
    while True:
        char = wait_for_input(timeout=0.05)
        if char:
            return char.lower()
        # Vider le tampon MIDI
        for _ in inport.iter_pending():
            pass
        
def get_single_char_choice(prompt, valid_choices):
    """Demande un choix à un caractère unique avec validation, sans spammer le terminal."""
    while True:
        choice = Prompt.ask(prompt, choices=list(valid_choices), show_choices=False, console=console)
        if choice in valid_choices:
            return choice
        else:
            console.print(f"[bold red]Choix invalide. Veuillez choisir parmi {', '.join(valid_choices)}.[/bold red]")

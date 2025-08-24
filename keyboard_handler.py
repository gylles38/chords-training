import sys
import time

from rich.console import Console
from rich.prompt import Prompt

console = Console()

if sys.platform == 'win32':
    import msvcrt

    # ---------- Gestion du mode raw permanent (Windows) ----------
    def enable_raw_mode():
        """Non applicable sur Windows."""
        pass

    def disable_raw_mode():
        """Non applicable sur Windows."""
        pass

    # ---------- Fonctions de lecture clavier (Windows) ----------
    def wait_for_input(timeout=0.05):
        """Saisie de caractère non-bloquante pour Windows."""
        start_time = time.time()
        while True:
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                # Les caractères spéciaux peuvent être précédés de b'\xe0' ou b'\x00'
                if ch in (b'\xe0', b'\x00'):
                    # Ignorer le préfixe et lire le vrai caractère
                    ch = msvcrt.getch()
                try:
                    decoded_ch = ch.decode('utf-8')
                    if decoded_ch in ('\r', '\n'):
                        return None
                    return decoded_ch
                except UnicodeDecodeError:
                    return None # Ignorer les caractères non décodables

            if time.time() - start_time > timeout:
                return None
            time.sleep(0.01)

else:
    # Pour les systèmes Unix (Linux, macOS)
    import select
    import tty
    import termios

    # ---------- Gestion du mode raw permanent (Unix) ----------
    _fd = sys.stdin.fileno()
    _old_settings = None

    def enable_raw_mode():
        """Passe le terminal en mode raw permanent (désactive écho et mode ligne)."""
        global _old_settings
        try:
            _old_settings = termios.tcgetattr(_fd)
            tty.setraw(_fd)
            new_settings = termios.tcgetattr(_fd)
            new_settings[3] &= ~(termios.ECHO | termios.ICANON)  # pas d'écho, pas de mode ligne
            termios.tcsetattr(_fd, termios.TCSADRAIN, new_settings)
        except termios.error:
            # Échoue silencieusement si pas dans un vrai TTY (ex: exécution dans un IDE)
            _old_settings = None

    def disable_raw_mode():
        """Restaure le mode normal du terminal."""
        if _old_settings:
            termios.tcsetattr(_fd, termios.TCSADRAIN, _old_settings)

    # ---------- Fonctions de lecture clavier (Unix) ----------
    def wait_for_input(timeout=0.05):
        """Saisie de caractère non-bloquante sans affichage et sans saut de ligne."""
        rlist, _, _ = select.select([sys.stdin], [], [], timeout)
        if rlist:
            ch = sys.stdin.read(1)
            if ch in ('\n', '\r'):
                return None
            return ch
        return None

# ---------- Fonctions communes ----------
def wait_for_any_key(inport):
    """Attend qu'une touche soit pressée sur le clavier ou qu'une note MIDI soit jouée."""
    enable_raw_mode()
    try:
        while True:
            # Check for keyboard input
            char = wait_for_input(timeout=0.01)
            if char:
                return

            # Check for MIDI input and clear buffer
            if inport and inport.poll():
                # Read all pending messages to clear buffer and then return
                for _ in inport.iter_pending():
                    pass
                return

            time.sleep(0.01)
    finally:
        disable_raw_mode()

def get_single_char_choice(prompt, valid_choices):
    """Demande un choix à un caractère unique avec validation, sans spammer le terminal."""
    while True:
        choice = Prompt.ask(prompt, choices=list(valid_choices), show_choices=False, console=console)
        if choice in valid_choices:
            return choice
        else:
            console.print(f"[bold red]Choix invalide. Veuillez choisir parmi {', '.join(valid_choices)}.[/bold red]")

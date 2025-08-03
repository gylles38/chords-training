# coding=utf-8
import mido
import time
import random
import os
import sys

# Importation des bibliothèques spécifiques à la plateforme pour la saisie non-bloquante
try:
    import msvcrt
except ImportError:
    # Pour les systèmes Unix (Linux, macOS)
    import select
    import tty
    import termios
    
# Couleurs ANSI pour la sortie du terminal
class Color:
    """Codes de couleur ANSI pour l'affichage dans le terminal."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    END = '\033[0m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'

# Noms des notes pour la conversion MIDI en nom
NOTE_NAMES = ['Do', 'Do#', 'Ré', 'Ré#', 'Mi', 'Fa', 'Fa#', 'Sol', 'Sol#', 'La', 'La#', 'Si']

def midi_to_note_name(midi_note):
    """
    Convertit un numéro de note MIDI en son nom (ex: 60 -> Do4).
    """
    if not 0 <= midi_note <= 127:
        return "Note inconnue"
    note_name = NOTE_NAMES[midi_note % 12]
    octave = (midi_note // 12) - 1
    return f"{note_name}{octave}"

# --- Définition des accords, des cadences et des gammes ---
# Un dictionnaire où la clé est le nom de l'accord et la valeur est un ensemble
# des numéros de notes MIDI pour cet accord. Les notes sont définies pour l'octave 4.
accords = {
    "Do Majeur": {60, 64, 67},
    "Ré Mineur": {62, 65, 69},
    "Mi Mineur": {64, 67, 71},
    "Fa Majeur": {65, 69, 72},
    "Sol Majeur": {67, 71, 74},
    "La Mineur": {69, 72, 76},
    "Si Diminué": {71, 74, 77},
    "Ré Majeur": {62, 66, 69},
    "La Majeur": {69, 73, 76},
    "Si Mineur": {71, 74, 78},
    "Do# Diminué": {61, 64, 67},
    "Fa# Diminué": {66, 69, 72},
    "Mi bémol Majeur": {63, 67, 70}
}

# Définition de suites d'accords (cadences)
cadences = {
    "Cadence Parfaite en Do Majeur": ["Sol Majeur", "Do Majeur"],
    "Cadence Parfaite en Fa Majeur": ["Do Majeur", "Fa Majeur"],
    "Cadence Parfaite en Sol Majeur": ["Ré Mineur", "Sol Majeur"],
    "Cadence Plagale en Do Majeur": ["Fa Majeur", "Do Majeur"],
    "Cadence Parfaite en La Mineur": ["Mi Mineur", "La Mineur"]
}

# Définition de suites d'accords pop/rock
pop_rock_progressions = {
    "I-V-vi-IV en Do Majeur": ["Do Majeur", "Sol Majeur", "La Mineur", "Fa Majeur"],
    "vi-IV-I-V en Do Majeur": ["La Mineur", "Fa Majeur", "Do Majeur", "Sol Majeur"],
    "I-IV-V en Sol Majeur": ["Sol Majeur", "Do Majeur", "Ré Majeur"],
    "I-vi-ii-V en Ré Majeur": ["Ré Majeur", "Si Mineur", "Mi Mineur", "La Majeur"],
    "II-V-I en Do Majeur": ["Ré Mineur", "Sol Majeur", "Do Majeur"]
}

# Définition des degrés d'accords pour différentes gammes
gammes = {
    "Do Majeur": {
        "I": "Do Majeur", "ii": "Ré Mineur", "iii": "Mi Mineur", "IV": "Fa Majeur",
        "V": "Sol Majeur", "vi": "La Mineur", "vii°": "Si Diminué"
    },
    "Sol Majeur": {
        "I": "Sol Majeur", "ii": "La Mineur", "iii": "Si Mineur", "IV": "Do Majeur",
        "V": "Ré Majeur", "vi": "Mi Mineur", "vii°": "Fa# Diminué"
    },
    "Ré Majeur": {
        "I": "Ré Majeur", "ii": "Mi Mineur", "iii": "Fa# Diminué", "IV": "Sol Majeur",
        "V": "La Majeur", "vi": "Si Mineur", "vii°": "Do# Diminué"
    },
    "La Mineur": {
        "i": "La Mineur", "ii°": "Si Diminué", "III": "Do Majeur", "iv": "Ré Mineur",
        "v": "Mi Mineur", "VI": "Fa Majeur", "VII": "Sol Majeur"
    },
    "Mi Mineur": {
        "i": "Mi Mineur", "ii°": "Fa# Diminué", "III": "Sol Majeur", "iv": "La Mineur",
        "v": "Si Mineur", "VI": "Do Majeur", "VII": "Ré Majeur"
    }
}

# --- Fonctions de retour MIDI ---
def play_midi_notes(outport, notes, duration=0.2, velocity=100):
    """
    Joue une ou plusieurs notes via MIDI.
    """
    if not outport: return
    for note in notes:
        outport.send(mido.Message('note_on', note=note, velocity=velocity))
    time.sleep(duration)
    for note in notes:
        outport.send(mido.Message('note_off', note=note))

def play_midi_sequence(outport, notes, note_duration=0.1, velocity=100):
    """
    Joue une séquence de notes une par une.
    """
    if not outport: return
    for note in notes:
        outport.send(mido.Message('note_on', note=note, velocity=velocity))
        time.sleep(note_duration)
        outport.send(mido.Message('note_off', note=note))

def play_success_feedback(outport):
    """
    Joue un retour MIDI pour un succès (séquence de notes).
    """
    play_midi_sequence(outport, [79, 83, 86], note_duration=0.1, velocity=127)

def play_failure_feedback(outport):
    """
    Joue un retour MIDI pour un échec (accord de Do# diminué).
    """
    play_midi_notes(outport, [61, 64, 67, 70], duration=0.5, velocity=127)

def play_waiting_feedback(outport):
    """
    Joue un retour MIDI pour indiquer l'attente (note unique).
    """
    play_midi_notes(outport, [72], duration=0.1, velocity=50)

def play_progression_chords(outport, progression_chords, delay=1.5):
    """
    Joue la suite d'accords via MIDI avec un délai entre chaque accord.
    """
    print(f"{Color.CYAN}🎧 Lecture de la progression...{Color.END}")
    for accord_nom in progression_chords:
        notes = accords.get(accord_nom)
        if notes:
            play_midi_notes(outport, notes, duration=1.0) # Joue l'accord pendant 1 seconde
            time.sleep(delay) # Délai avant l'accord suivant
        else:
            print(f"L'accord '{accord_nom}' n'a pas été trouvé. Passage au suivant.")
    print(f"{Color.CYAN}Progression jouée. A votre tour !{Color.END}")
    time.sleep(1)


class NonBlockingInput:
    """
    Gestionnaire de contexte pour la saisie non-bloquante sous Unix.
    Assure que les paramètres du terminal sont restaurés.
    """
    def __init__(self):
        self.old_settings = None
        self.fd = sys.stdin.fileno()

    def __enter__(self):
        if os.name != 'nt':
            self.old_settings = termios.tcgetattr(self.fd)
            tty.setraw(self.fd)
        return self

    def __exit__(self, type, value, traceback):
        if os.name != 'nt' and self.old_settings:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    def get_key(self, timeout=0):
        if os.name == 'nt':
            if msvcrt.kbhit():
                return msvcrt.getch().decode('utf-8')
            return None
        else:
            if select.select([sys.stdin], [], [], timeout) == ([sys.stdin], [], []):
                return sys.stdin.read(1)
            return None

def display_colored_notes(played_notes, expected_notes):
    """
    Affiche les notes jouées en vert si elles sont correctes et bien placées,
    en jaune si elles sont correctes mais mal placées, et en rouge sinon.
    """
    played_notes_list = sorted(list(played_notes))
    expected_notes_list = sorted(list(expected_notes))
    
    played_notes_str = []
    
    # On convertit les notes attendues en un set pour des recherches rapides
    expected_notes_set = set(expected_notes)
    
    for i, played_note in enumerate(played_notes_list):
        note_name = midi_to_note_name(played_note)
        
        # 1. Vérifier si la note est correcte et bien placée (position et note)
        is_correct_position = (i < len(expected_notes_list) and played_note == expected_notes_list[i])
        
        # 2. Vérifier si la note est correcte, mais mal placée
        is_correct_note = (played_note in expected_notes_set)
        
        if is_correct_position:
            played_notes_str.append(f"{Color.GREEN}{note_name}{Color.END}")
        elif is_correct_note:
            played_notes_str.append(f"{Color.YELLOW}{note_name}{Color.END}")
        else:
            played_notes_str.append(f"{Color.RED}{note_name}{Color.END}")
    
    return ", ".join(played_notes_str)

def clear_screen():
    """
    Efface le terminal pour une meilleure lisibilité.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

def display_mode_header(mode_name):
    """
    Efface l'écran et affiche le nom du mode en haut.
    """
    clear_screen()
    print(f"{Color.CYAN}--- Mode : {mode_name} ---{Color.END}\n")

def get_single_char_choice(prompt, valid_choices):
    """
    Lit une seule touche du clavier de manière non-bloquante et sans écho.
    """
    print(prompt, end='', flush=True)
    with NonBlockingInput() as nbi:
        while True:
            key = nbi.get_key()
            if key and key in valid_choices:
                # Efface la ligne du prompt pour éviter l'écho et la confusion
                print("\r" + " " * len(prompt), end='\r', flush=True)
                return key
            time.sleep(0.01)

def get_number_choice(prompt, default_value, unit):
    """
    Lit une entrée numérique, autorise 'q' pour quitter, et nécessite 'Entrée' pour valider.
    """
    prompt_message = f"Entrez une nouvelle valeur ({unit}) (par défaut: {default_value}) : "
    print(prompt, end='', flush=True)
    new_value_str = ""
    with NonBlockingInput() as nbi:
        while True:
            print(f"\r{prompt_message}{new_value_str} (validez avec 'Entrée' ou 'q' pour annuler)", end='', flush=True)
            key = nbi.get_key(0.1) # Utilise un petit timeout pour ne pas bloquer
            if key:
                if key.isdigit():
                    new_value_str += key
                elif key.lower() == 'q':
                    print("\nAnnulé. La valeur par défaut est conservée.")
                    time.sleep(1)
                    return default_value
                elif key in ('\r', '\n'):
                    print("\n")
                    if new_value_str:
                        try:
                            new_value = int(new_value_str)
                            if new_value > 0:
                                return new_value
                            else:
                                print(f"La valeur doit être un nombre positif. La valeur par défaut est conservée.")
                                time.sleep(2)
                                return default_value
                        except ValueError:
                            print("Entrée invalide. La valeur par défaut est conservée.")
                            time.sleep(2)
                            return default_value
                    else:
                        return default_value

def _wait_for_notes_release_silent(port, previous_notes):
    """
    Attend que l'utilisateur relâche toutes les touches de l'accord précédent, sans rien afficher.
    """
    if previous_notes:
        notes_a_relacher = set(previous_notes)
        while notes_a_relacher:
            msg = port.receive(block=False)
            if msg and (msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0)):
                if msg.note in notes_a_relacher:
                    notes_a_relacher.remove(msg.note)
            time.sleep(0.01)


def wait_for_progression_action(inport):
    """
    Demande à l'utilisateur ce qu'il veut faire après avoir terminé une progression.
    Retourne 'continue', 'back' ou 'quit'.
    """
    print("\n" + "-" * 40)
    print("Appuyez sur :")
    print(" - une touche MIDI pour rejouer cette progression")
    print(" - 'm' pour le menu de sélection des progressions")
    print(" - 'q' pour le menu principal")
    
    with NonBlockingInput() as nbi:
        while True:
            key = nbi.get_key()
            if key:
                if key.lower() == 'm':
                    return "back"
                if key.lower() == 'q':
                    return "quit"

            msg = inport.receive(block=False)
            if msg and msg.type == 'note_on' and msg.velocity > 0:
                return "continue"
            
            time.sleep(0.01)

def print_progression_context(progression_name, progression_chords, current_index, progression_type):
    """
    Affiche la suite d'accords avec l'accord actuel en surbrillance.
    """
    print(f"Suite d'accords choisie ({progression_type}) : {progression_name}\n")
    display_str = []
    for i, chord in enumerate(progression_chords):
        if i == current_index:
            display_str.append(f"{Color.BOLD}{Color.GREEN}➜ {chord}{Color.END}")
        else:
            display_str.append(chord)
    print(" -> ".join(display_str))
    print("-" * 40)

def wait_for_any_key(prompt="Appuyez sur n'importe quelle touche pour continuer..."):
    """
    Bloque l'exécution et attend que l'utilisateur appuie sur une touche.
    """
    print(prompt, end='', flush=True)
    with NonBlockingInput() as nbi:
        while True:
            key = nbi.get_key()
            if key:
                print("\n")
                return
            time.sleep(0.01)

def check_single_chord_with_retry(inport, outport, accord_a_deviner_nom, notes_attendues, degre_a_deviner_nom=None, progression_timer=None):
    """
    Gère la vérification d'un accord, y compris les retours et les tentatives.
    Cette fonction efface l'écran à chaque tentative pour éviter le défilement.
    Retourne le statut (succès/échec/quitter/timeout) et le nombre de tentatives incorrectes.
    """
    incorrect_attempts = 0
    while True:
        clear_screen()
        
        notes_jouees = set()
        
        # Affiche l'en-tête et le contexte si nécessaire
        instruction = f"Jouez l'accord : {accord_a_deviner_nom} (Octave 4)"
        if degre_a_deviner_nom:
            instruction = f"Jouez l'accord du degré {degre_a_deviner_nom} : {accord_a_deviner_nom} (Octave 4)"
        
        print(f"{instruction} (q pour quitter)")
        
        # On attend l'accord de l'utilisateur
        with NonBlockingInput() as nbi:
            while True:
                # Vérifie et affiche le temps de la progression en continu
                prog_time_str = ""
                if progression_timer and progression_timer['enabled']:
                    prog_remaining = int(progression_timer['end_time'] - time.time())
                    if prog_remaining <= 0:
                        clear_screen()
                        print(f"\r{Color.RED}TEMPS ÉCOULÉ !{Color.END}")
                        time.sleep(0.5) 
                        play_failure_feedback(outport)
                        return "timeout_progression", incorrect_attempts
                    prog_time_str = f" [Temps restant: {Color.CYAN}{prog_remaining}{Color.END}s]"
                
                print(f"\r{prog_time_str}", end='', flush=True)

                msg = inport.receive(block=False)
                if msg:
                    if msg.type == 'note_on' and msg.velocity > 0:
                        notes_jouees.add(msg.note)
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        if msg.note in notes_jouees:
                            notes_jouees.remove(msg.note)
                
                key = nbi.get_key()
                if key and key.lower() == 'q':
                    return "quit", incorrect_attempts

                if len(notes_jouees) == len(notes_attendues) and notes_jouees and not any(inport.receive(block=False) for _ in range(5)):
                    break
                
                time.sleep(0.01)

        if notes_jouees == notes_attendues:
            # Succès
            _wait_for_notes_release_silent(inport, notes_jouees)
            time.sleep(0.5)
            play_success_feedback(outport)
            return "success", incorrect_attempts
        else:
            # Échec
            incorrect_attempts += 1
            time.sleep(0.5)
            play_failure_feedback(outport)
            
            # Affiche l'erreur en dessous de l'instruction
            print("\n" + "-"*40)
            print(f"{Color.RED}❌ Incorrect. Mauvais accord.{Color.END}")
            print(f"Les notes jouées sont : {display_colored_notes(notes_jouees, notes_attendues)}")
            
            notes_attendues_noms = [midi_to_note_name(note) for note in sorted(list(notes_attendues))]
            print(f"Les notes attendues étaient : {', '.join(notes_attendues_noms)}")
            
            print("\nRelâchez les touches pour réessayer...")
            _wait_for_notes_release_silent(inport, notes_jouees)
            
            # La boucle continue, effacera l'écran et réaffichera le tout pour une nouvelle tentative.
            continue

def run_progression_mode(inport, outport, progression_name, progression_chords, progression_type, progression_timer, play_progression_before_start, mode_name):
    """
    Fonction générique pour exécuter n'importe quel mode de progression.
    Gère le chronomètre de progression si activé.
    Retourne un dictionnaire avec le résultat et les stats.
    """
    session_stats = {'correct': 0, 'incorrect': 0}
    
    # Boucle principale pour permettre le redémarrage de la progression
    while True:
        # Si l'option est activée, joue la progression avant de commencer
        if play_progression_before_start:
            display_mode_header(mode_name)
            print(f"\n{Color.CYAN}La progression va être jouée dans 2 secondes...{Color.END}")
            time.sleep(2) # Ajout d'un délai pour se préparer
            play_progression_chords(outport, progression_chords)

        progression_start_time = time.time()
        if progression_timer['enabled']:
            progression_timer['end_time'] = progression_start_time + progression_timer['timeout']

        for i, accord_nom in enumerate(progression_chords):
            notes_attendues = accords.get(accord_nom)
            if not notes_attendues:
                print(f"Erreur : L'accord '{accord_nom}' n'est pas défini. Passage au suivant.")
                continue

            # On affiche le contexte une seule fois au début de chaque accord
            display_mode_header(mode_name)
            print_progression_context(progression_name, progression_chords, i, progression_type)
            
            result, num_incorrect = check_single_chord_with_retry(
                inport, outport, accord_nom, notes_attendues, 
                progression_timer=progression_timer
            )
            
            if result == "quit":
                session_stats['incorrect'] += num_incorrect
                return "quit", session_stats
            elif result == "timeout_progression":
                display_mode_header(mode_name)
                print(f"\n{Color.RED}Délai de progression écoulé. Recommençons !{Color.END}")
                session_stats['incorrect'] += 1 + num_incorrect # +1 pour le timeout
                time.sleep(3)
                break  # Recommence la boucle "while True"
            
            if result == "success":
                session_stats['correct'] += 1
                session_stats['incorrect'] += num_incorrect
            else:
                session_stats['incorrect'] += 1 + num_incorrect
        else:
            # Cette partie est exécutée si la boucle "for" s'est terminée sans 'break'
            display_mode_header(mode_name)
            print(f"\n{Color.GREEN}🎉 Félicitations ! Vous avez terminé la suite d'accords : {progression_name}{Color.END}")
            action = wait_for_progression_action(inport)
            return action, session_stats
        
def single_chord_mode(inport, outport):
    """
    Mode de jeu pour un seul accord aléatoire.
    """
    mode_name = "Accord unique (aléatoire)"
    session_stats = {'correct': 0, 'incorrect': 0}
    
    while True:
        accord_a_deviner_nom, notes_attendues = random.choice(list(accords.items()))
        
        display_mode_header(mode_name)
        result, num_incorrect = check_single_chord_with_retry(inport, outport, accord_a_deviner_nom, notes_attendues)
        
        if result == "quit":
            session_stats['incorrect'] += num_incorrect
            break
        elif result == "success":
            session_stats['correct'] += 1
            session_stats['incorrect'] += num_incorrect
        
        time.sleep(0.5)
    
    return "quit", session_stats

def reverse_chord_mode(inport, outport):
    """
    Le système joue un accord, l'utilisateur doit le reproduire.
    """
    mode_name = "Accord à retrouver (le système joue)"
    session_stats = {'correct': 0, 'incorrect': 0}
    
    while True:
        # Choisit un accord aléatoire
        accord_a_jouer_nom, notes_attendues = random.choice(list(accords.items()))
        
        # Initialise un compteur d'essais pour ce nouvel accord
        incorrect_attempts = 0

        while True: # Boucle pour le re-jeu
            display_mode_header(mode_name)
            # Affiche les indices si disponibles
            if incorrect_attempts >= 5:
                tonic_note = midi_to_note_name(min(notes_attendues))
                print(f"{Color.YELLOW}💡 Indice : La tonique est la note '{tonic_note.split(' ')[0]}'.{Color.END}\n")
            elif incorrect_attempts >= 3:
                chord_type = accord_a_jouer_nom.split()[-1]
                print(f"{Color.YELLOW}💡 Indice : C'est un accord de type {chord_type}.{Color.END}\n")

            print("🎧 Écoutez attentivement l'accord...")
            time.sleep(1)
            play_midi_notes(outport, notes_attendues, duration=1.0)
            
            # Attendre que les notes MIDI de l'accord joué par le programme soient relâchées
            time.sleep(0.1) # Petite pause pour laisser les messages note_off être envoyés
            
            # Vider le buffer d'entrée MIDI pour ignorer les notes jouées par l'utilisateur
            # pendant la lecture de l'accord par le programme
            while inport.poll():
                pass
            
            time.sleep(1) # Délai pour que l'utilisateur ait le temps de réfléchir

            notes_jouees = set()
            
            with NonBlockingInput() as nbi:
                while True:
                    print(f"\rJouez l'accord que vous venez d'entendre (q pour quitter, r pour réécouter)...", end='', flush=True)
                    
                    msg = inport.receive(block=False)
                    if msg:
                        if msg.type == 'note_on' and msg.velocity > 0:
                            notes_jouees.add(msg.note)
                        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                            if msg.note in notes_jouees:
                                notes_jouees.remove(msg.note)
                    
                    key = nbi.get_key()
                    if key:
                        if key.lower() == 'q':
                            return "quit", session_stats
                        if key.lower() == 'r':
                            # Rejoue l'accord et attend une nouvelle tentative
                            _wait_for_notes_release_silent(inport, notes_jouees)
                            print(f"{Color.CYAN}Relecture de l'accord...{Color.END}")
                            time.sleep(1)
                            play_midi_notes(outport, notes_attendues, duration=1.0)
                            time.sleep(1)
                            # Réinitialise la boucle de saisie
                            notes_jouees = set()
                            continue 
                    
                    # On ne vérifie l'accord que si l'utilisateur a relâché les touches
                    if len(notes_jouees) == len(notes_attendues) and notes_jouees:
                        break
                    
                    time.sleep(0.01)
            
            if notes_jouees == notes_attendues:
                _wait_for_notes_release_silent(inport, notes_jouees)
                time.sleep(0.5)
                play_success_feedback(outport)
                display_mode_header(mode_name)
                print(f"\n{Color.GREEN}🎉 Correct ! C'était bien un {accord_a_jouer_nom}.{Color.END}")
                session_stats['correct'] += 1
                session_stats['incorrect'] += incorrect_attempts
                break # Sort de la boucle de re-jeu pour passer au prochain accord
            else:
                incorrect_attempts += 1
                time.sleep(0.5)
                play_failure_feedback(outport)
                notes_jouees_noms = [midi_to_note_name(note) for note in sorted(list(notes_jouees))]
                notes_attendues_noms = [midi_to_note_name(note) for note in sorted(list(notes_attendues))]
                display_mode_header(mode_name)
                print(f"\n{Color.RED}❌ Incorrect. Mauvais accord.{Color.END}")
                print(f"Les notes jouées sont : {display_colored_notes(notes_jouees, notes_attendues)}")
                
                if incorrect_attempts < 3:
                    print("\nAppuyez sur une touche MIDI pour continuer, 'r' pour réécouter ou 'q' pour quitter.")
                else:
                    # L'indice sera affiché en haut de l'écran à la prochaine tentative
                    pass
    
    return "quit", session_stats


def progression_mode(inport, outport, progression_timer, progression_selection_mode, play_progression_before_start):
    """
    Mode de jeu pour une suite d'accords classique (cadences).
    """
    mode_name = "Progressions d'accords (cadences classiques)"
    while True:
        display_mode_header(mode_name)
        cadence_nom_choisie = None
        if progression_selection_mode == 'midi_key':
            print("Pour choisir une suite d'accords, jouez la note fondamentale correspondante sur votre clavier MIDI.")
            print("Ou appuyez sur 'q' pour revenir au menu.")

            cadence_map_for_menu = {
                60: "Cadence Parfaite en Do Majeur",
                65: "Cadence Parfaite en Fa Majeur",
                67: "Cadence Parfaite en Sol Majeur",
                69: "Cadence Parfaite en La Mineur"
            }
            
            for midi_note, name in cadence_map_for_menu.items():
                print(f"Note {midi_to_note_name(midi_note)} -> {name}")
            
            with NonBlockingInput() as nbi:
                while cadence_nom_choisie is None:
                    key = nbi.get_key()
                    if key and key.lower() == 'q':
                        return "quit", {'correct': 0, 'incorrect': 0}

                    msg = inport.receive(block=False)
                    if msg and msg.type == 'note_on' and msg.velocity > 0:
                        if msg.note in cadence_map_for_menu:
                            cadence_nom_choisie = cadence_map_for_menu[msg.note]
                    time.sleep(0.01)
        else: # random
            cadence_nom_choisie = random.choice(list(cadences.keys()))
            print(f"Progression aléatoire sélectionnée : {cadence_nom_choisie}")
            time.sleep(2)
        
        accords_progression = cadences[cadence_nom_choisie]
        action, session_stats = run_progression_mode(inport, outport, cadence_nom_choisie, accords_progression, "Cadence", progression_timer, play_progression_before_start, mode_name)
        if action == "quit":
            return "quit", session_stats
        elif action == "back":
            continue
        elif action == "continue":
            run_progression_mode(inport, outport, cadence_nom_choisie, accords_progression, "Cadence", progression_timer, play_progression_before_start, mode_name)
        return "quit", session_stats


def pop_rock_mode(inport, outport, progression_timer, progression_selection_mode, play_progression_before_start):
    """
    Mode de jeu pour les suites d'accords pop/rock.
    """
    mode_name = "Suites d'accords pop/rock"
    while True:
        display_mode_header(mode_name)
        progression_nom_choisie = None
        if progression_selection_mode == 'midi_key':
            print("Pour choisir une suite d'accords pop/rock, jouez la note fondamentale du premier accord sur votre clavier MIDI.")
            print("Ou appuyez sur 'q' pour revenir au menu.")

            pop_rock_map_for_menu = {
                60: "I-V-vi-IV en Do Majeur",
                69: "vi-IV-I-V en Do Majeur",
                67: "I-IV-V en Sol Majeur",
                62: "I-vi-ii-V en Ré Majeur",
                64: "II-V-I en Do Majeur"
            }

            for midi_note, name in pop_rock_map_for_menu.items():
                print(f"Note {midi_to_note_name(midi_note)} -> {name}")

            with NonBlockingInput() as nbi:
                while progression_nom_choisie is None:
                    key = nbi.get_key()
                    if key and key.lower() == 'q':
                        return "quit", {'correct': 0, 'incorrect': 0}

                    msg = inport.receive(block=False)
                    if msg and msg.type == 'note_on' and msg.velocity > 0:
                        if msg.note in pop_rock_map_for_menu:
                            progression_nom_choisie = pop_rock_map_for_menu[msg.note]
                    time.sleep(0.01)
        else: # random
            progression_nom_choisie = random.choice(list(pop_rock_progressions.keys()))
            print(f"Progression aléatoire sélectionnée : {progression_nom_choisie}")
            time.sleep(2)
        
        accords_progression = pop_rock_progressions[progression_nom_choisie]
        
        action, session_stats = run_progression_mode(inport, outport, progression_nom_choisie, accords_progression, "Pop/Rock", progression_timer, play_progression_before_start, mode_name)
        if action == "quit":
            return "quit", session_stats
        elif action == "back":
            continue
        elif action == "continue":
            run_progression_mode(inport, outport, progression_nom_choisie, accords_progression, "Pop/Rock", progression_timer, play_progression_before_start, mode_name)
        return "quit", session_stats


def degrees_mode(inport, outport, progression_timer, progression_selection_mode, play_progression_before_start):
    """
    Mode de jeu pour les degrés d'accords d'une gamme.
    """
    mode_name = "Degrés d'accords"
    session_stats = {'correct': 0, 'incorrect': 0}
    
    while True:
        display_mode_header(mode_name)
        gamme_choisie_nom = None
        if progression_selection_mode == 'midi_key':
            print("Pour choisir une gamme, jouez sa note fondamentale sur votre clavier MIDI.")
            print("Ou appuyez sur 'q' pour revenir au menu.")

            gamme_midi_map = {
                60: "Do Majeur",
                67: "Sol Majeur",
                62: "Ré Majeur",
                69: "La Mineur",
                64: "Mi Mineur"
            }
            
            for midi_note, gamme_name in gamme_midi_map.items():
                print(f"Note {midi_to_note_name(midi_note)} -> Gamme de {gamme_name}")

            with NonBlockingInput() as nbi:
                while gamme_choisie_nom is None:
                    key = nbi.get_key()
                    if key and key.lower() == 'q':
                        return "quit", session_stats
                    
                    msg = inport.receive(block=False)
                    if msg and msg.type == 'note_on' and msg.velocity > 0:
                        if msg.note in gamme_midi_map:
                            gamme_choisie_nom = gamme_midi_map[msg.note]
                            print(f"\nVous avez choisi la gamme de {gamme_choisie_nom}.")
                            
                    time.sleep(0.01)
        else: # random
            gamme_choisie_nom = random.choice(list(gammes.keys()))
            print(f"Gamme aléatoire sélectionnée : {gamme_choisie_nom}")
            time.sleep(2)


        def print_degrees_table(current_degre_nom=None):
            print(f"Gamme choisie : {gamme_choisie_nom}")
            print("-" * 40)
            print(f"| {'Degré':<10} | {'Accord':<25} |")
            print("-" * 40)
            for degre, accord in gammes[gamme_choisie_nom].items():
                if degre == current_degre_nom:
                    print(f"| {Color.BOLD}{Color.GREEN}{degre:<10}{Color.END} | {Color.BOLD}{accord:<25}{Color.END} |")
                else:
                    print(f"| {degre:<10} | {accord:<25} |")
            print("-" * 40)

        last_degre_nom = None
        
        # Boucle principale pour permettre le redémarrage de la progression
        while True:
            progression_start_time = time.time()
            if progression_timer['enabled']:
                progression_timer['end_time'] = progression_start_time + progression_timer['timeout']
            
            accords_progression_tuples = list(gammes[gamme_choisie_nom].items())
            accords_progression_chords = [accord for degre, accord in accords_progression_tuples]

            # Si l'option est activée, joue la progression avant de commencer
            if play_progression_before_start:
                display_mode_header(mode_name)
                print(f"\n{Color.CYAN}La progression va être jouée dans 2 secondes...{Color.END}")
                time.sleep(2) # Ajout d'un délai pour se préparer
                play_progression_chords(outport, accords_progression_chords)

            for i in range(len(accords_progression_tuples)):
                degre_nom, accord_nom = last_degre_nom, None
                while degre_nom == last_degre_nom:
                    degre_nom, accord_nom = random.choice(accords_progression_tuples)
                
                notes_attendues = accords.get(accord_nom)
                if not notes_attendues:
                    print(f"Erreur : L'accord '{accord_nom}' n'est pas défini. Passage au suivant.")
                    continue
                
                display_mode_header(mode_name)
                print_degrees_table(degre_nom)
                
                result, num_incorrect = check_single_chord_with_retry(
                    inport, outport, accord_nom, notes_attendues, degre_nom, 
                    progression_timer=progression_timer
                )
                
                if result == "quit":
                    session_stats['incorrect'] += num_incorrect
                    return "quit", session_stats
                elif result == "timeout_progression":
                    display_mode_header(mode_name)
                    print(f"\n{Color.RED}Délai de progression écoulé. Recommençons !{Color.END}")
                    session_stats['incorrect'] += 1 + num_incorrect # +1 pour le timeout
                    time.sleep(3)
                    break # Recommence la boucle "while True"
                
                if result == "success":
                    last_degre_nom = degre_nom
                    session_stats['correct'] += 1
                    session_stats['incorrect'] += num_incorrect
                else:
                    session_stats['incorrect'] += 1 + num_incorrect
            else:
                # Exécuté si la boucle "for" s'est terminée sans 'break'
                display_mode_header(mode_name)
                print(f"\n{Color.GREEN}🎉 Félicitations ! Vous avez terminé la suite d'accords.{Color.END}")
                action = wait_for_progression_action(inport)
                if action == "quit":
                    return "quit", session_stats
                elif action == "back":
                    break # Revenir au menu de sélection des gammes
                elif action == "continue":
                    continue # Recommence la même progression
    
    return "quit", session_stats

def options_menu(current_progression_timer, current_progression_selection_mode, current_play_progression_before_start):
    """
    Affiche le menu des options et permet à l'utilisateur de modifier les paramètres.
    """
    mode_name = "Options"
    while True:
        clear_screen()
        print(f"{Color.CYAN}--- Menu : Options ---{Color.END}\n")
        
        prog_status = "Activé" if current_progression_timer['enabled'] else "Désactivé"
        print(f"[1] Chronomètre de progression : {prog_status}")
        if current_progression_timer['enabled']:
             print(f"    - Durée du chronomètre : {current_progression_timer['timeout']} secondes")
        
        selection_mode_display = "Touche MIDI" if current_progression_selection_mode == 'midi_key' else "Aléatoire"
        print(f"[2] Mode de sélection des progressions : {selection_mode_display}")

        play_before_display = "Activé" if current_play_progression_before_start else "Désactivé"
        print(f"[3] Jouer la progression avant de demander : {play_before_display}")

        print("[4] Retour au menu principal")
        
        choice = get_single_char_choice("Votre choix : ", ['1', '2', '3', '4'])
        
        if choice == '1':
            current_progression_timer['enabled'] = not current_progression_timer['enabled']
            if current_progression_timer['enabled']:
                print("\nChronomètre de progression activé.")
                new_prog_timeout = get_number_choice("Définir la durée du chronomètre de progression", current_progression_timer['timeout'], "secondes")
                if new_prog_timeout is not None:
                    current_progression_timer['timeout'] = new_prog_timeout
            else:
                print("\nChronomètre de progression désactivé.")
            time.sleep(2)
        elif choice == '2':
            if current_progression_selection_mode == 'midi_key':
                current_progression_selection_mode = 'random'
                print("\nMode de sélection des progressions mis en aléatoire.")
            else:
                current_progression_selection_mode = 'midi_key'
                print("\nMode de sélection des progressions mis en touche MIDI.")
            time.sleep(2)
        elif choice == '3':
            current_play_progression_before_start = not current_play_progression_before_start
            if current_play_progression_before_start:
                print("\nL'option 'Jouer la progression avant de demander' est maintenant activée.")
            else:
                print("\nL'option 'Jouer la progression avant de demander' est maintenant désactivée.")
            time.sleep(2)
        elif choice == '4':
            return current_progression_timer, current_progression_selection_mode, current_play_progression_before_start
    
def display_statistics(stats):
    """
    Affiche les statistiques de la dernière session avant de revenir au menu principal.
    """
    if stats['correct'] == 0 and stats['incorrect'] == 0:
        return
    
    clear_screen()
    print("=" * 40)
    print(f"{'Résultats de votre dernière session':^40}")
    print("=" * 40)
    
    total = stats['correct'] + stats['incorrect']
    if total > 0:
        rate = (stats['correct'] / total) * 100
    else:
        rate = 0
    
    print(f"Réponses correctes   : {Color.GREEN}{stats['correct']}{Color.END}")
    print(f"Réponses incorrectes : {Color.RED}{stats['incorrect']}{Color.END}")
    print("-" * 40)
    print(f"Total des tentatives : {total}")
    print(f"Taux de réussite     : {Color.YELLOW}{rate:.2f}%{Color.END}")
    print("=" * 40)
    wait_for_any_key("Appuyez sur n'importe quelle touche pour continuer au menu principal...")
    
# --- Logique de l'application ---
def main():
    """
    Fonction principale pour l'application de vérification d'accords MIDI.
    """
    inport = None
    outport = None

    try:
        input_ports = mido.get_input_names()
        output_ports = mido.get_output_names()

        if not input_ports:
            print("Aucun périphérique MIDI d'entrée n'a été trouvé.")
            return

        inport_name = None
        outport_name = None
        inport = None
        outport = None

        # Boucle pour la sélection du port d'entrée
        while True:
            print("\nPorts MIDI d'entrée disponibles (clavier MIDI) :")
            for i, name in enumerate(input_ports):
                print(f"[{i}] {name}")
            
            valid_choices = [str(i) for i in range(len(input_ports))] + ['q']
            inport_choice = get_single_char_choice("Entrez le numéro du port d'entrée de votre clavier (ou 'q' pour quitter) : ", valid_choices)
            
            if inport_choice.lower() == 'q':
                print("\nArrêt du programme.")
                return

            try:
                inport_name = input_ports[int(inport_choice)]
                inport = mido.open_input(inport_name)
                print(f"Connecté en entrée à : {inport_name}")
                break
            except (ValueError, IndexError):
                print(f"{Color.RED}Choix invalide. Veuillez entrer un numéro valide ou 'q'.{Color.END}")
            except Exception as e:
                print(f"{Color.RED}Erreur : Impossible d'ouvrir le port '{inport_name}'. Détails : {e}{Color.END}")
                time.sleep(2)
        
        # Boucle pour la sélection du port de sortie
        if output_ports:
            while True:
                print("\nPorts MIDI de sortie disponibles pour le feedback :")
                for i, name in enumerate(output_ports):
                    print(f"[{i}] {name}")

                outport_valid_choices = [str(i) for i in range(len(output_ports))] + ['q', 'n']
                outport_choice = get_single_char_choice("Entrez le numéro du port de sortie pour le feedback (ou 'n' pour ne pas en utiliser, 'q' pour quitter) : ", outport_valid_choices)

                if outport_choice.lower() == 'q':
                    print("\nArrêt du programme.")
                    return
                elif outport_choice.lower() == 'n':
                    print("Fonctionnalité de sortie MIDI désactivée.")
                    break
                
                try:
                    outport_name = output_ports[int(outport_choice)]
                    outport = mido.open_output(outport_name)
                    print(f"Connecté en sortie à : {outport_name}")
                    break
                except (ValueError, IndexError):
                    print(f"{Color.RED}Choix invalide. Veuillez entrer un numéro valide, 'n' ou 'q'.{Color.END}")
                except Exception as e:
                    print(f"{Color.RED}Erreur : Impossible d'ouvrir le port '{outport_name}'. Détails : {e}{Color.END}")
                    time.sleep(2)
        else:
            print("\nAucun périphérique MIDI de sortie n'a été trouvé. Le programme fonctionnera sans retour MIDI.")


        print("\nBienvenue dans le vérificateur d'accords MIDI ! Appuyez sur Ctrl+C pour quitter.")

        progression_timer = {'enabled': False, 'timeout': 60, 'end_time': 0}
        progression_selection_mode = 'midi_key'
        play_progression_before_start = True # Nouvelle option, activée par défaut
        
        # Dictionnaire pour stocker les statistiques de la dernière session
        session_stats = {'correct': 0, 'incorrect': 0}

        while True:
            display_statistics(session_stats)
            clear_screen()
            print("\nSélectionnez un mode de jeu :")
            print("[1] Accord unique (aléatoire)")
            print("[2] Progressions d'accords (cadences classiques)")
            print("[3] Degrés d'accords")
            print("[4] Suites d'accords pop/rock")
            print("[5] Accord à retrouver (le système joue)")
            print("[6] Options")
            print("[7] Quitter")
            
            mode_choice = get_single_char_choice("Votre choix : ", ['1', '2', '3', '4', '5', '6', '7'])
            
            # Réinitialise les statistiques de session avant de commencer un nouveau mode
            correct, incorrect = 0, 0

            if mode_choice == '1':
                action, stats = single_chord_mode(inport, outport)
                session_stats = stats
                if action == "quit": continue
            elif mode_choice == '2':
                action, stats = progression_mode(inport, outport, progression_timer, progression_selection_mode, play_progression_before_start)
                session_stats = stats
                if action == "quit": continue
            elif mode_choice == '3':
                action, stats = degrees_mode(inport, outport, progression_timer, progression_selection_mode, play_progression_before_start)
                session_stats = stats
                if action == "quit": continue
            elif mode_choice == '4':
                action, stats = pop_rock_mode(inport, outport, progression_timer, progression_selection_mode, play_progression_before_start)
                session_stats = stats
                if action == "quit": continue
            elif mode_choice == '5':
                action, stats = reverse_chord_mode(inport, outport)
                session_stats = stats
                if action == "quit": continue
            elif mode_choice == '6':
                progression_timer, progression_selection_mode, play_progression_before_start = options_menu(progression_timer, progression_selection_mode, play_progression_before_start)
                session_stats = {'correct': 0, 'incorrect': 0}
            elif mode_choice == '7':
                print("Arrêt du programme.")
                break
            else:
                print("Choix invalide. Veuillez réessayer.")

    except KeyboardInterrupt:
        print("\nArrêt du programme.")
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")
    finally:
        # Cette section garantit que les ports sont fermés, peu importe comment le programme se termine.
        if inport and not inport.closed:
            print(f"Fermeture du port d'entrée : {inport.name}")
            inport.close()
        if outport and not outport.closed:
            print(f"Fermeture du port de sortie : {outport.name}")
            outport.close()

if __name__ == "__main__":
    main()

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
    ORANGE = '\033[38;5;208m'
    END = '\033[0m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'

def clear_screen():
    """Efface l'écran du terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')

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
    "Do dièse Majeur": {61, 65, 68},
    "Ré dièse Mineur": {63, 66, 70},
    "Fa dièse Majeur": {66, 70, 73},
    "Sol dièse Mineur": {68, 71, 75},
    "La dièse Mineur": {70, 73, 77},
    "Mi bémol Majeur": {63, 67, 70},
    "Sol bémol Majeur": {66, 70, 73},
    "La bémol Majeur": {68, 72, 75},
    "Si bémol Majeur": {70, 74, 77},
    "Ré bémol Majeur": {61, 65, 68},
    
    # Ajout des accords manquants pour le mode "Degrés"
    "Ré Majeur": {62, 66, 69},
    "Si Mineur": {71, 74, 78},
    "Fa dièse Mineur": {66, 69, 73},
    "Do dièse Mineur": {61, 64, 68},
    "Mi dièse Mineur": {65, 68, 72}, # enharmonique de Fa Mineur
    "La Majeur": {69, 73, 76},
    "Mi Majeur": {64, 68, 71},
    "Si Majeur": {71, 75, 78},
    "Sol Mineur": {67, 70, 74},
    "Do Mineur": {60, 63, 67},
    "Fa dièse Diminué": {66, 69, 72},
    "Do dièse Diminué": {61, 64, 67},
    "Sol dièse Diminué": {68, 71, 74},
    "Ré dièse Diminué": {63, 66, 69},
    "Mi dièse Diminué": {65, 68, 71},
    "La dièse Diminué": {70, 73, 76},
    "Do bémol Majeur": {71, 74, 77}, # enharmonique de Si Majeur
    "Fa bémol Majeur": {64, 67, 71}, # enharmonique de Mi Majeur
    "Si bémol Mineur": {70, 73, 77},
    "Mi bémol Mineur": {63, 66, 70},
    
    # Nouveaux accords manquants
    "Sol dièse Majeur": {68, 72, 75}, # Pour Do dièse Majeur
    "Si dièse Diminué": {60, 63, 66}, # Pour Do dièse Majeur (enharmonique de Do Diminué)
    "Ré bémol Mineur": {61, 64, 68}, # enharmonique de Do dièse Mineur
    "La bémol Mineur": {68, 71, 75}, # enharmonique de Sol dièse Mineur
    "Fa Mineur": {65, 68, 72}, # Pour Mi bémol Majeur
    "Mi Diminué": {64, 67, 70}, # Pour Fa Majeur
    "Fa Diminué": {65, 68, 71}, # Pour Sol bémol Majeur
    "Sol Diminué": {67, 70, 73}, # Pour La bémol Majeur
    "Do Diminué": {60, 63, 66}, # Pour Ré bémol Majeur
    "Si bémol Diminué": {70, 73, 76}, # Pour Do bémol Majeur
}

# Gammes majeures pour le mode degrés
gammes_majeures = {
    "Do Majeur": ["Do Majeur", "Ré Mineur", "Mi Mineur", "Fa Majeur", "Sol Majeur", "La Mineur", "Si Diminué"],
    "Sol Majeur": ["Sol Majeur", "La Mineur", "Si Mineur", "Do Majeur", "Ré Majeur", "Mi Mineur", "Fa dièse Diminué"],
    "Ré Majeur": ["Ré Majeur", "Mi Mineur", "Fa dièse Mineur", "Sol Majeur", "La Majeur", "Si Mineur", "Do dièse Diminué"],
    "La Majeur": ["La Majeur", "Si Mineur", "Do dièse Mineur", "Ré Majeur", "Mi Majeur", "Fa dièse Mineur", "Sol dièse Diminué"],
    "Mi Majeur": ["Mi Majeur", "Fa dièse Mineur", "Sol dièse Mineur", "La Majeur", "Si Majeur", "Do dièse Mineur", "Ré dièse Diminué"],
    "Si Majeur": ["Si Majeur", "Do dièse Mineur", "Ré dièse Mineur", "Mi Majeur", "Fa dièse Majeur", "Sol dièse Mineur", "La dièse Diminué"],
    "Fa dièse Majeur": ["Fa dièse Majeur", "Sol dièse Mineur", "La dièse Mineur", "Si Majeur", "Do dièse Majeur", "Ré dièse Mineur", "Mi dièse Diminué"],
    "Do dièse Majeur": ["Do dièse Majeur", "Ré dièse Mineur", "Mi dièse Mineur", "Fa dièse Majeur", "Sol dièse Majeur", "La dièse Mineur", "Si dièse Diminué"],
    "Fa Majeur": ["Fa Majeur", "Sol Mineur", "La Mineur", "Si bémol Majeur", "Do Majeur", "Ré Mineur", "Mi Diminué"],
    "Si bémol Majeur": ["Si bémol Majeur", "Do Mineur", "Ré Mineur", "Mi bémol Majeur", "Fa Majeur", "Sol Mineur", "La Diminué"],
    "Mi bémol Majeur": ["Mi bémol Majeur", "Fa Mineur", "Sol Mineur", "La bémol Majeur", "Si bémol Majeur", "Do Mineur", "Ré Diminué"],
    "La bémol Majeur": ["La bémol Majeur", "Si bémol Mineur", "Do Mineur", "Ré bémol Majeur", "Mi bémol Majeur", "Fa Mineur", "Sol Diminué"],
    "Ré bémol Majeur": ["Ré bémol Majeur", "Mi bémol Mineur", "Fa Mineur", "Sol bémol Majeur", "La bémol Majeur", "Si bémol Mineur", "Do Diminué"],
    "Sol bémol Majeur": ["Sol bémol Majeur", "La bémol Mineur", "Si bémol Mineur", "Do bémol Majeur", "Ré bémol Majeur", "Mi bémol Mineur", "Fa Diminué"],
    "Do bémol Majeur": ["Do bémol Majeur", "Ré bémol Mineur", "Mi bémol Mineur", "Fa bémol Majeur", "Sol bémol Majeur", "La bémol Mineur", "Si bémol Diminué"],
}

# Traduction des degrés pour le mode degrés
traductions_degres = {
    0: "I", 1: "ii", 2: "iii", 3: "IV", 4: "V", 5: "vi", 6: "vii°"
}

# --- Fonctions utilitaires ---
def get_note_name(midi_note):
    """Convertit un numéro de note MIDI en son nom."""
    notes = ["Do", "Do#", "Ré", "Ré#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]
    return notes[midi_note % 12]

def play_chord(outport, chord_notes, velocity=100, duration=0.5):
    """Joue un accord via MIDI."""
    for note in chord_notes:
        msg = mido.Message('note_on', note=note, velocity=velocity)
        outport.send(msg)
    time.sleep(duration)
    for note in chord_notes:
        msg = mido.Message('note_off', note=note, velocity=0)
        outport.send(msg)

def wait_for_input(timeout=0.01):
    """Saisie de caractère non-bloquante."""
    if 'msvcrt' in sys.modules:
        if msvcrt.kbhit():
            return msvcrt.getch().decode('utf-8')
    else:
        # Pour les systèmes Unix
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            if select.select([sys.stdin], [], [], timeout)[0]:
                return sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return None

def wait_for_any_key(inport):
    """Fonction non-bloquante pour attendre n'importe quelle touche du clavier."""
    while True:
        char = wait_for_input(timeout=0.01)
        if char:
            return char.lower()
        # Vider le tampon MIDI
        for _ in inport.iter_pending():
            pass

def get_single_char_choice(prompt, valid_choices):
    """Demande un choix à un caractère unique avec validation, sans spammer le terminal."""
    while True:
        print(prompt, end="", flush=True)
        choice = wait_for_input(timeout=1000)
        if choice and choice in valid_choices:
            print(choice)
            return choice
        else:
            pass

def select_midi_port(port_type):
    """Permet à l'utilisateur de choisir un port MIDI parmi la liste disponible."""
    ports = mido.get_input_names() if port_type == "input" else mido.get_output_names()
    
    if not ports:
        print(f"{Color.RED}Aucun port {port_type} MIDI trouvé. Assurez-vous que votre périphérique est connecté.{Color.END}")
        return None
    
    print(f"\nPorts {port_type} MIDI disponibles:")
    for i, port_name in enumerate(ports):
        print(f"[{i+1}] {port_name}")
    print("[q] Quitter")
    
    while True:
        choice = input(f"Veuillez choisir un port {port_type} (1-{len(ports)}) ou 'q' pour quitter: ")
        if choice.lower() == 'q':
            return None
        try:
            choice_index = int(choice) - 1
            if 0 <= choice_index < len(ports):
                return ports[choice_index]
            else:
                print(f"{Color.RED}Choix invalide. Veuillez entrer un numéro entre 1 et {len(ports)}.{Color.END}")
        except ValueError:
            print(f"{Color.RED}Saisie invalide. Veuillez entrer un numéro.{Color.END}")

def reverse_chord_mode(inport, outport):
    """Mode de reconnaissance d'accords joués par l'utilisateur."""
    clear_screen()
    print("\n--- Mode Reconnaissance d'accords ---")
    print("Jouez un accord sur votre clavier MIDI.")
    print("Appuyez sur 'q' pour quitter.")

    while True:
        # Vider le tampon d'entrée MIDI
        for _ in inport.iter_pending():
            pass
        
        char = wait_for_input(timeout=0.1)
        if char and char.lower() == 'q':
            break

        for msg in inport.iter_pending():
            if msg.type == 'note_on' and msg.velocity > 0:
                pressed_notes = set()
                time.sleep(0.1)
                for pending_msg in inport.iter_pending():
                    if pending_msg.type == 'note_on' and pending_msg.velocity > 0:
                        pressed_notes.add(pending_msg.note)
                
                found_chord = None
                for chord_name, chord_notes in accords.items():
                    if all(note in pressed_notes for note in chord_notes):
                        found_chord = chord_name
                        break

                if found_chord:
                    print(f"Accord reconnu : {Color.GREEN}{found_chord}{Color.END}")
                else:
                    print(f"Accord non reconnu. Notes jouées : {[get_note_name(n) for n in pressed_notes]}")
        

def display_stats(correct_count, total_count, elapsed_time=None):
    """Affiche les statistiques de performance."""
    print(f"\n--- Bilan de la session ---")
    if total_count > 0:
        pourcentage = (correct_count / total_count) * 100
        print(f"Accords corrects : {Color.GREEN}{correct_count}{Color.END}")
        print(f"Accords incorrects : {Color.RED}{total_count - correct_count}{Color.END}")
        print(f"Taux de réussite : {Color.CYAN}{pourcentage:.2f}%{Color.END}")
    else:
        print("Aucun accord n'a été joué.")
    if elapsed_time is not None:
        print(f"Temps écoulé : {Color.CYAN}{elapsed_time:.2f} secondes{Color.END}")
    print("-------------------------")

def get_colored_notes_string(played_notes, correct_notes):
    """Retourne une chaîne de caractères avec les notes jouées, colorées en fonction de leur justesse."""
    output_parts = []
    
    # Créer un dictionnaire pour vérifier les notes correctes dans n'importe quelle octave
    correct_note_names = {get_note_name(n) for n in correct_notes}
    
    for note in sorted(played_notes):
        note_name = get_note_name(note)
        
        if note in correct_notes:
            output_parts.append(f"{Color.GREEN}{note_name}{Color.END}")
        elif note_name in correct_note_names:
            output_parts.append(f"{Color.ORANGE}{note_name}{Color.END}")
        else:
            output_parts.append(f"{Color.RED}{note_name}{Color.END}")
            
    return ", ".join(output_parts)


# --- Modes de jeu ---
def single_chord_mode(inport, outport):
    """Mode d'entraînement sur les accords simples. L'utilisateur doit jouer le bon accord pour passer au suivant."""
    clear_screen()
    print("\n--- Mode Accords Simples ---")
    print("Jouez l'accord affiché. Appuyez sur 'q' pour quitter.")
    
    correct_count = 0
    total_count = 0
    last_chord_name = None
    
    exit_flag = False
    
    while not exit_flag:
        # Vider le tampon MIDI
        for _ in inport.iter_pending():
            pass

        # Choisir un nouvel accord
        chord_name, chord_notes = random.choice(list(accords.items()))
        while chord_name == last_chord_name:
            chord_name, chord_notes = random.choice(list(accords.items()))
        
        last_chord_name = chord_name
        
        # Effacer l'écran pour le nouvel accord
        clear_screen()
        print("\n--- Mode Accords Simples ---")
        print("Jouez l'accord affiché. Appuyez sur 'q' pour quitter.")
        print(f"\nJouez : {Color.YELLOW}{chord_name}{Color.END}")

        notes_currently_on = set()
        attempt_notes = set()
        
        while not exit_flag:
            char = wait_for_input(timeout=0.01)
            if char and char.lower() == 'q':
                exit_flag = True
                break
            
            for msg in inport.iter_pending():
                if msg.type == 'note_on' and msg.velocity > 0:
                    notes_currently_on.add(msg.note)
                    attempt_notes.add(msg.note)
                elif msg.type == 'note_off':
                    notes_currently_on.discard(msg.note)
            
            # Un accord a été joué et toutes les notes ont été relâchées
            if not notes_currently_on and attempt_notes:
                if attempt_notes == chord_notes:
                    colored_notes = get_colored_notes_string(attempt_notes, chord_notes)
                    print(f"Notes jouées : [{colored_notes}]")
                    print(f"{Color.GREEN}Correct !{Color.END}")
                    correct_count += 1
                    total_count += 1
                    time.sleep(1) # Pause avant le prochain accord
                    break # Passer à l'accord suivant
                else:
                    colored_string = get_colored_notes_string(attempt_notes, chord_notes)
                    print(f"{Color.RED}Incorrect. Réessayez. Notes jouées : [{colored_string}]{Color.END}")
                    total_count += 1
                    attempt_notes.clear() # Réinitialiser pour le prochain essai
                    
            time.sleep(0.01)
        
    # Cette partie est exécutée si on quitte le mode
    display_stats(correct_count, total_count)
    print("\nAppuyez sur une touche pour retourner au menu principal.")
    # Vider le tampon MIDI avant d'attendre la touche
    for _ in inport.iter_pending():
        pass
    wait_for_any_key(inport)


def get_progression_choice(progression_selection_mode, inport, last_progression=None):
    """Permet de choisir une progression, soit aléatoirement, soit via MIDI."""
    progressions_pop_rock = {
        "I-V-vi-IV": ["Do Majeur", "Sol Majeur", "La Mineur", "Fa Majeur"],
        "ii-V-I": ["Ré Mineur", "Sol Majeur", "Do Majeur"],
        "I-vi-ii-V": ["Do Majeur", "La Mineur", "Ré Mineur", "Sol Majeur"],
        "IV-I-V-vi": ["Fa Majeur", "Do Majeur", "Sol Majeur", "La Mineur"],
    }
    
    if progression_selection_mode == 'midi':
        print(f"Appuyez sur une note de la 4ème octave pour choisir une progression ({Color.CYAN}Do4 à Fa4{Color.END}) ou 'q' pour revenir au menu.")
        note_map = {
            60: "I-V-vi-IV", 62: "ii-V-I", 64: "I-vi-ii-V", 65: "IV-I-V-vi"
        }
        
        while True:
            char = wait_for_input(timeout=0.01)
            if char and char.lower() == 'q':
                return None, None
                
            for msg in inport.iter_pending():
                if msg.type == 'note_on' and msg.velocity > 0:
                    note = msg.note
                    if note in note_map:
                        prog_name = note_map[note]
                        if not last_progression or prog_name != last_progression:
                            print(f"Progression sélectionnée : {Color.CYAN}{prog_name}{Color.END}")
                            return prog_name, progressions_pop_rock[prog_name]
                        else:
                            print(f"{Color.RED}Progression déjà jouée. Veuillez en choisir une autre.{Color.END}")
    else: # Mode aléatoire par défaut
        prog_name, progression = random.choice(list(progressions_pop_rock.items()))
        while progression == last_progression:
            prog_name, progression = random.choice(list(progressions_pop_rock.items()))
        return prog_name, progression

def pop_rock_mode(inport, outport, progression_timer, progression_selection_mode, play_progression_before_start):
    """Mode d'entraînement sur des progressions Pop/Rock."""
    clear_screen()
    print("\n--- Mode Progressions Pop/Rock ---")
    print("Appuyez sur 'q' pour quitter.")

    correct_count = 0
    total_count = 0
    last_progression = None
    
    exit_flag = False
    
    while not exit_flag:
        # Vider les tampons d'entrée avant chaque progression pour éviter les entrées fantômes
        for _ in inport.iter_pending():
            pass
        
        prog_name, progression = get_progression_choice(progression_selection_mode, inport, last_progression)
        if prog_name is None:
            exit_flag = True
            break
        
        last_progression = progression

        print(f"\nProgression à jouer : {Color.YELLOW}{' -> '.join(progression)}{Color.END}")
        
        if play_progression_before_start:
            print("Lecture de la progression...")
            for chord_name in progression:
                play_chord(outport, accords[chord_name], duration=0.8)
                time.sleep(0.5)

        start_time = None
        if progression_timer:
            print(f"{Color.CYAN}Minuteur activé. Commencez à jouer !{Color.END}")
            start_time = time.time()
        
        for chord_name in progression:
            target_notes = accords[chord_name]
            print(f"Jouez l'accord {Color.YELLOW}{chord_name}{Color.END}")
            
            notes_currently_on = set()
            attempt_notes = set()

            while not exit_flag:
                char = wait_for_input(timeout=0.01)
                if char and char.lower() == 'q':
                    exit_flag = True
                    break
                
                for msg in inport.iter_pending():
                    if msg.type == 'note_on' and msg.velocity > 0:
                        notes_currently_on.add(msg.note)
                        attempt_notes.add(msg.note)
                    elif msg.type == 'note_off':
                        notes_currently_on.discard(msg.note)

                if not notes_currently_on and attempt_notes:
                    total_count += 1
                    if attempt_notes == target_notes:
                        colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                        print(f"Notes jouées : [{colored_notes}]")
                        print(f"{Color.GREEN}Correct !{Color.END}")
                        correct_count += 1
                        break
                    else:
                        colored_string = get_colored_notes_string(attempt_notes, target_notes)
                        print(f"{Color.RED}Incorrect. Réessayez. Notes jouées : [{colored_string}]{Color.END}")
                        attempt_notes.clear()
                
                time.sleep(0.01)
            
            if exit_flag:
                break
            
        if start_time and not exit_flag:
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"Temps pour la progression : {Color.CYAN}{elapsed_time:.2f} secondes{Color.END}")
            
    display_stats(correct_count, total_count)
    print("\nAppuyez sur une touche pour retourner au menu principal.")
    for _ in inport.iter_pending():
        pass
    wait_for_any_key(inport)


def progression_mode(inport, outport, progression_timer, progression_selection_mode, play_progression_before_start):
    """Mode d'entraînement sur les progressions d'accords."""
    clear_screen()
    print("\n--- Mode Progressions d'Accords ---")
    print("Appuyez sur 'q' pour quitter.")

    correct_count = 0
    total_count = 0
    last_progression = []
    
    exit_flag = False
    
    while not exit_flag:
        # Vider les tampons d'entrée avant chaque progression pour éviter les entrées fantômes
        for _ in inport.iter_pending():
            pass

        prog_len = random.randint(3, 5)
        progression = random.sample(list(accords.keys()), prog_len)
        while progression == last_progression:
            progression = random.sample(list(accords.keys()), prog_len)
        
        last_progression = progression
        
        print(f"\nProgression à jouer : {Color.YELLOW}{' -> '.join(progression)}{Color.END}")
        
        if play_progression_before_start:
            print("Lecture de la progression...")
            for chord_name in progression:
                play_chord(outport, accords[chord_name], duration=0.8)
                time.sleep(0.5)

        start_time = None
        if progression_timer:
            print(f"{Color.CYAN}Minuteur activé. Commencez à jouer !{Color.END}")
            start_time = time.time()
        
        for chord_name in progression:
            target_notes = accords[chord_name]
            print(f"Jouez l'accord {Color.YELLOW}{chord_name}{Color.END}")
            
            notes_currently_on = set()
            attempt_notes = set()
            
            while not exit_flag:
                char = wait_for_input(timeout=0.01)
                if char and char.lower() == 'q':
                    exit_flag = True
                    break
                
                for msg in inport.iter_pending():
                    if msg.type == 'note_on' and msg.velocity > 0:
                        notes_currently_on.add(msg.note)
                        attempt_notes.add(msg.note)
                    elif msg.type == 'note_off':
                        notes_currently_on.discard(msg.note)

                if not notes_currently_on and attempt_notes:
                    total_count += 1
                    if attempt_notes == target_notes:
                        colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                        print(f"Notes jouées : [{colored_notes}]")
                        print(f"{Color.GREEN}Correct !{Color.END}")
                        correct_count += 1
                        break
                    else:
                        colored_string = get_colored_notes_string(attempt_notes, target_notes)
                        print(f"{Color.RED}Incorrect. Réessayez. Notes jouées : [{colored_string}]{Color.END}")
                        attempt_notes.clear()
                
                time.sleep(0.01)
            
            if exit_flag:
                break
            
        if start_time and not exit_flag:
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"Temps pour la progression : {Color.CYAN}{elapsed_time:.2f} secondes{Color.END}")
            
    display_stats(correct_count, total_count)
    print("\nAppuyez sur une touche pour retourner au menu principal.")
    for _ in inport.iter_pending():
        pass
    wait_for_any_key(inport)


def degrees_mode(inport, outport, progression_timer, progression_selection_mode, play_progression_before_start):
    """Mode d'entraînement sur les accords par degrés."""
    clear_screen()
    print("\n--- Mode Degrés ---")
    print("Appuyez sur 'q' pour quitter.")

    correct_count = 0
    total_count = 0
    last_progression_accords = []
    
    exit_flag = False
    
    while not exit_flag:
        # Vider les tampons d'entrée avant chaque progression pour éviter les entrées fantômes
        for _ in inport.iter_pending():
            pass

        # Effacer l'écran pour la nouvelle progression
        clear_screen()
        print("\n--- Mode Degrés ---")
        print("Appuyez sur 'q' pour quitter.")
        
        tonalite, gammes = random.choice(list(gammes_majeures.items()))
        prog_len = random.randint(3, 5)
        
        progression_accords = []
        while not progression_accords or progression_accords == last_progression_accords:
            degres_progression = random.sample(range(len(gammes)), prog_len)
            progression_accords = [gammes[d] for d in degres_progression]
            
        last_progression_accords = progression_accords

        print(f"\nDans la tonalité de {Color.YELLOW}{tonalite}{Color.END}, jouez la progression : {Color.YELLOW}{' -> '.join([traductions_degres[d] for d in degres_progression])}{Color.END}")
        
        if play_progression_before_start:
            print("Lecture de la progression...")
            for chord_name in progression_accords:
                play_chord(outport, accords[chord_name], duration=0.8)
                time.sleep(0.5)

        start_time = None
        if progression_timer:
            print(f"{Color.CYAN}Minuteur activé. Commencez à jouer !{Color.END}")
            start_time = time.time()
        
        for chord_name in progression_accords:
            target_notes = accords[chord_name]
            print(f"Jouez l'accord {Color.YELLOW}{chord_name}{Color.END}")
            
            notes_currently_on = set()
            attempt_notes = set()
            
            while not exit_flag:
                char = wait_for_input(timeout=0.01)
                if char and char.lower() == 'q':
                    exit_flag = True
                    break
                
                for msg in inport.iter_pending():
                    if msg.type == 'note_on' and msg.velocity > 0:
                        notes_currently_on.add(msg.note)
                        attempt_notes.add(msg.note)
                    elif msg.type == 'note_off':
                        notes_currently_on.discard(msg.note)

                if not notes_currently_on and attempt_notes:
                    total_count += 1
                    if attempt_notes == target_notes:
                        colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                        print(f"Notes jouées : [{colored_notes}]")
                        print(f"{Color.GREEN}Correct !{Color.END}")
                        correct_count += 1
                        break
                    else:
                        colored_string = get_colored_notes_string(attempt_notes, target_notes)
                        print(f"{Color.RED}Incorrect. Réessayez. Notes jouées : [{colored_string}]{Color.END}")
                        attempt_notes.clear()
                
                time.sleep(0.01)
            
            if exit_flag:
                break
            
        if start_time and not exit_flag:
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"Temps pour la progression : {Color.CYAN}{elapsed_time:.2f} secondes{Color.END}")
            
    display_stats(correct_count, total_count)
    print("\nAppuyez sur une touche pour retourner au menu principal.")
    for _ in inport.iter_pending():
        pass
    wait_for_any_key(inport)

def options_menu(progression_timer, progression_selection_mode, play_progression_before_start):
    """Menu d'options pour configurer le programme."""
    clear_screen()
    print("\n--- Menu Options ---")
    while True:
        print(f"\n[1] Minuteur progression: {Color.GREEN}Activé{Color.END}" if progression_timer else f"[1] Minuteur progression: {Color.RED}Désactivé{Color.END}")
        print(f"[2] Sélection progression: {Color.GREEN}MIDI (touche){Color.END}" if progression_selection_mode == 'midi' else f"[2] Sélection progression: {Color.RED}Aléatoire{Color.END}")
        print(f"[3] Lecture progression: {Color.GREEN}Avant de commencer{Color.END}" if play_progression_before_start else f"[3] Lecture progression: {Color.RED}Non{Color.END}")
        print("[4] Retour au menu principal")
        
        choice = get_single_char_choice("Votre choix : ", ['1', '2', '3', '4'])
        
        if choice == '1':
            progression_timer = not progression_timer
        elif choice == '2':
            progression_selection_mode = 'midi' if progression_selection_mode == 'random' else 'random'
        elif choice == '3':
            play_progression_before_start = not play_progression_before_start
        elif choice == '4':
            return progression_timer, progression_selection_mode, play_progression_before_start
    return progression_timer, progression_selection_mode, play_progression_before_start

def main():
    """Fonction principale du programme."""
    progression_timer = False
    progression_selection_mode = 'random'
    play_progression_before_start = True
    
    clear_screen()
    print(f"--- Bienvenue dans l'Entraîneur d'Accords MIDI ---")

    inport_name = select_midi_port("input")
    if not inport_name:
        print("Annulation de la sélection du port d'entrée. Arrêt du programme.")
        return

    outport_name = select_midi_port("output")
    if not outport_name:
        print("Annulation de la sélection du port de sortie. Arrêt du programme.")
        return

    try:
        with mido.open_input(inport_name) as inport, mido.open_output(outport_name) as outport:
            clear_screen()
            print(f"Port d'entrée MIDI sélectionné : {Color.GREEN}{inport.name}{Color.END}")
            print(f"Port de sortie MIDI sélectionné : {Color.GREEN}{outport.name}{Color.END}")
            time.sleep(2)
            
            while True:
                # Vider le tampon MIDI à chaque retour au menu principal
                for _ in inport.iter_pending():
                    pass

                clear_screen()
                print("\n--- Menu Principal ---")
                print("[1] Mode Accord Simple")
                print("[2] Mode Progressions d'Accords (aléatoires)")
                print("[3] Mode Degrés (par tonalité)")
                print("[4] Mode Pop/Rock (progressions célèbres)")
                print("[5] Mode Reconnaissance d'accords")
                print("[6] Options")
                print("[7] Quitter")
                
                mode_choice = get_single_char_choice("Votre choix : ", ['1', '2', '3', '4', '5', '6', '7'])
                
                if mode_choice == '1':
                    single_chord_mode(inport, outport)
                elif mode_choice == '2':
                    progression_mode(inport, outport, progression_timer, progression_selection_mode, play_progression_before_start)
                elif mode_choice == '3':
                    degrees_mode(inport, outport, progression_timer, progression_selection_mode, play_progression_before_start)
                elif mode_choice == '4':
                    pop_rock_mode(inport, outport, progression_timer, progression_selection_mode, play_progression_before_start)
                elif mode_choice == '5':
                    reverse_chord_mode(inport, outport)
                elif mode_choice == '6':
                    progression_timer, progression_selection_mode, play_progression_before_start = options_menu(progression_timer, progression_selection_mode, play_progression_before_start)
                elif mode_choice == '7':
                    print("Arrêt du programme.")
                    break
                else:
                    pass
    except KeyboardInterrupt:
        print("\nArrêt du programme.")
    except Exception as e:
        print(f"Une erreur s'est produite : {e}")

if __name__ == "__main__":
    main()

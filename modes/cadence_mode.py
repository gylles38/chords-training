# modes/cadence_mode.py
import random
import time
from rich.prompt import Prompt
from rich.live import Live
from rich.table import Table
from rich.panel import Panel

from .chord_mode_base import ChordModeBase
from ui import get_colored_notes_string, display_stats_fixed
from screen_handler import clear_screen, int_to_roman
from keyboard_handler import wait_for_any_key, wait_for_input,enable_raw_mode, disable_raw_mode
from midi_handler import play_progression_sequence

class CadenceMode(ChordModeBase):
    def __init__(self, inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
        super().__init__(inport, outport, chord_set)
        self.use_timer = use_timer
        self.timer_duration = timer_duration    
        self.progression_selection_mode = progression_selection_mode  # Not used in provided code, kept for completeness                    
        self.play_progression_before_start = play_progression_before_start
        self.session_correct_count = 0        
        self.first_display_done = False
        self.current_cadence = None  
        self.session_correct_count = 0
        self.session_total_count = 0
        self.session_total_attempts = 0         
        self.elapsed_time = 0.0                   

    def display_degrees_table(self, tonalite, gammes_filtrees):
        """Affiche le tableau des degrés pour la tonalité donnée"""
        table = Table(title=f"\nTableau des degrés pour \n[bold yellow]{tonalite}[/bold yellow]", border_style="magenta")
        table.add_column("Degré", justify="center", style="bold cyan")
        table.add_column("Accord", justify="center", style="bold yellow")

        for i, chord_name in enumerate(gammes_filtrees, 1):
            roman_degree = int_to_roman(i)
            table.add_row(roman_degree, chord_name)

        self.console.print(table)

    def create_cadence_display(self, nom_cadence, degres_str, progression_str, tonalite, prog_index, progression_accords):
        """Crée l'affichage pour la cadence en cours"""
        if prog_index < len(progression_accords):
            current_chord = progression_accords[prog_index]
            content = (f"Tonalité: [bold yellow]{tonalite}[/bold yellow]\n"
                      f"Cadence: [bold cyan]{nom_cadence}[/bold cyan] ([bold cyan]{degres_str}[/bold cyan])\n"
                      f"Progression: [bold yellow]{progression_str}[/bold yellow]\n\n"
                      f"Jouez l'accord ({prog_index + 1}/{len(progression_accords)}): [bold yellow]{current_chord}[/bold yellow]")
        else:
            content = f"Cadence terminée ! [bold green]{nom_cadence}[/bold green] en {tonalite}"
        
        return Panel(content, title="Cadence à jouer", border_style="magenta")

    def select_valid_cadence(self):
        """Sélectionne une cadence valide avec les accords disponibles"""
        from data.chords import gammes_majeures, cadences, DEGREE_MAP  # Import local pour éviter les dépendances circulaires
        
        while True:
            # 1. Choisir une tonalité au hasard
            tonalite, accords_de_la_gamme = random.choice(list(gammes_majeures.items()))

            # 2. Choisir une cadence au hasard
            nom_cadence, degres_cadence = random.choice(list(cadences.items()))

            # 3. Traduire les degrés en noms d'accords
            try:
                progression_accords = [accords_de_la_gamme[DEGREE_MAP[d]] for d in degres_cadence]
            except (KeyError, IndexError):
                continue  # Si un degré n'est pas dans notre map, recommencer

            # 4. Vérifier si tous les accords de la cadence sont dans le `chord_set` autorisé
            if all(accord in self.chord_set for accord in progression_accords):
                # Filtrer les gammes pour l'affichage
                gammes_filtrees = [g for g in accords_de_la_gamme if g in self.chord_set]
                return tonalite, nom_cadence, degres_cadence, progression_accords, gammes_filtrees

    # La gestion de la lecture du clavier est confiée à la classe mère ChordModBase.handle_keyboard_input (n,r,q)
    # La méthode _handle_custom_input est redéfinie pour gérer 'p' (pause) par exemple
    #def _handle_custom_input(self, char):
    #    if char and char.lower() == 'p':
    #        return 'pause'
    #    return False
    

    def play_single_chord(self, prog_index, progression_accords, tonalite, nom_cadence, degres_str, progression_str):
        """Gère la saisie d'un accord individuel dans la progression"""
        chord_name = progression_accords[prog_index]
        target_notes = self.chord_set[chord_name]
        
        with Live(console=self.console, screen=False, auto_refresh=False) as live:
            if not self.first_display_done:
                live.update(self.create_cadence_display(nom_cadence, degres_str, progression_str, tonalite, prog_index, progression_accords), refresh=True)
                self.first_display_done = True  # Pour éviter de réafficher la cadence à chaque itération                
            
            notes_currently_on = set()
            attempt_notes = set()
            
            try:
                while not self.exit_flag:
                    # Gestion des entrées clavier
                    while self.wait_for_input(timeout=0) is not None:
                        pass

                    char = wait_for_input(timeout=0.05)
                    action = self.handle_keyboard_input(char)
                                   
                    if action == 'quit':
                        return 'quit'
                    elif action == 'repeat':
                        return 'repeat'
                    elif action == 'next':
                        return 'next'
                    
                    # Gestion MIDI
                    for msg in self.inport.iter_pending():
                        if msg.type == 'note_on' and msg.velocity > 0:
                            notes_currently_on.add(msg.note)
                            attempt_notes.add(msg.note)
                        elif msg.type == 'note_off':
                            notes_currently_on.discard(msg.note)

                    # Vérification de l'accord quand toutes les notes sont relâchées
                    if not notes_currently_on and attempt_notes:
                        # Incrémenter le compteur de tentatives à chaque essai
                        self.total_attempts += 1
                        
                        is_correct, recognized_name, recognized_inversion = self.check_chord(
                            attempt_notes, chord_name, target_notes
                        )
                        
                        if is_correct:
                            colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                            success_msg = f"[bold green]Correct ! {chord_name}[/bold green]\nNotes jouées : [{colored_notes}]"
                            live.update(success_msg, refresh=True)
                            time.sleep(1)
                            # Incrémenter le compteur de réussites
                            self.correct_count += 1
                            return 'correct'
                        else:
                            # Affichage de l'erreur
                            colored_string = get_colored_notes_string(attempt_notes, target_notes)
                            if recognized_name:
                                clean_name = str(recognized_name).replace('%', 'pct').replace('{', '(').replace('}', ')')
                                clean_inversion = str(recognized_inversion).replace('%', 'pct').replace('{', '(').replace('}', ')') if recognized_inversion else "position inconnue"
                                error_msg = f"[bold red]Incorrect.[/bold red] Vous avez joué : {clean_name} ({clean_inversion})\nNotes jouées : [{colored_string}]"
                            else:
                                error_msg = f"[bold red]Incorrect. Réessayez.[/bold red]\nNotes jouées : [{colored_string}]"
                            
                            live.update(error_msg, refresh=True)
                            time.sleep(2)
                            if not self.first_display_done:
                                live.update(self.create_cadence_display(nom_cadence, degres_str, progression_str, tonalite, prog_index, progression_accords), refresh=True)
                            attempt_notes.clear()

                    time.sleep(0.01)
                    
            finally:
                disable_raw_mode()

        return 'quit'

    def afficher_entete_cadence(self):
        """Affiche l'entête et la consigne pour la cadence en cours"""
        self.display_header("Cadences", "Mode Cadences Musicales", "magenta")
        self.console.print("Jouez la cadence demandée dans la bonne tonalité.")
        self.console.print("Appuyez sur 'q' pour quitter, 'r' pour répéter, 'n' pour passer.")

    def wait_for_end_choice(self):
        """Attend une saisie instantanée pour continuer ou quitter"""
        self.console.print("\n[bold green]Progression terminée ![/bold green] Appuyez sur une touche pour continuer ou 'q' pour quitter...")
        enable_raw_mode()
        try:
            while not self.exit_flag:
                char = wait_for_input(timeout=0.05)
                if char:
                    if char.lower() == 'q':
                        self.exit_flag = True
                    return  # N'importe quelle autre touche continue
                time.sleep(0.01)
        finally:
            disable_raw_mode()
        
    def run(self):
        """Méthode principale du mode cadence"""
        while not self.exit_flag:
            self.clear_midi_buffer()
            # Affichage uniquement si ce n'est pas déjà fait pour cette cadence
            #if not self.first_display_done:
            self.afficher_entete_cadence()
                
            # Sélectionner une cadence valide
            tonalite, nom_cadence, degres_cadence, progression_accords, gammes_filtrees = self.select_valid_cadence()

            # Afficher le tableau des degrés
            self.display_degrees_table(tonalite, gammes_filtrees)

            degres_str = ' -> '.join(degres_cadence)
            progression_str = ' -> '.join(progression_accords)
            
            self.console.print(f"\nDans la tonalité de [bold yellow]{tonalite}[/bold yellow], jouez la [bold cyan]{nom_cadence}[/bold cyan] ([bold cyan]{degres_str}[/bold cyan]):")
            self.console.print(f"[bold yellow]{progression_str}[/bold yellow]")

            # Jouer la progression si demandé
            if self.play_progression_before_start and progression_accords:
                play_progression_sequence(self.outport, progression_accords, self.chord_set)

            # Traitement de la progression
            progression_correct_count = 0
            progression_total_attempts = 0
            is_progression_started = False
            start_time = None
            skip_progression = False
                     
            with Live(console=self.console, screen=False, auto_refresh=False) as live:
                prog_index = 0
                while prog_index < len(progression_accords) and not self.exit_flag and not skip_progression:
                    chord_name = progression_accords[prog_index]
                    target_notes = self.chord_set[chord_name]
                    chord_attempts = 0

                    time_info = ""
                    if self.use_timer and is_progression_started:
                        remaining_time = self.timer_duration - (time.time() - start_time)
                        time_info = f"Temps restant : [bold magenta]{remaining_time:.1f}s[/bold magenta]"

                    live.update(self.create_live_display(chord_name, prog_index, len(progression_accords), time_info), refresh=True)

                    notes_currently_on = set()
                    attempt_notes = set()

                    # Activer le mode raw seulement pour cette boucle d'interaction
                    enable_raw_mode()
                    try:
                        while not self.exit_flag and not skip_progression:
                            if self.use_timer and is_progression_started:
                                remaining_time = self.timer_duration - (time.time() - start_time)
                                time_info = f"Temps restant : [bold magenta]{remaining_time:.1f}s[/bold magenta]"
                                # Désactiver/réactiver le mode raw pour l'update
                                disable_raw_mode()
                                live.update(self.create_live_display(chord_name, prog_index, len(progression_accords), time_info), refresh=True)
                                enable_raw_mode()

                                if remaining_time <= 0:
                                    disable_raw_mode()
                                    live.update("[bold red]Temps écoulé ! Session terminée.[/bold red]", refresh=True)
                                    enable_raw_mode()
                                    time.sleep(2)
                                    self.exit_flag = True
                                    break

                            char = wait_for_input(timeout=0.01)
                            if char:
                                action = self.handle_keyboard_input(char)
                                if action == 'repeat':
                                    # Vider le buffer clavier
                                    while wait_for_input(timeout=0.001):
                                        pass
                                    
                                    # Désactiver le mode raw pour les updates
                                    disable_raw_mode()
                                    live.update("[bold cyan]Lecture de la progression...[/bold cyan]", refresh=True)
                                    play_progression_sequence(self.outport, progression_accords, self.chord_set)
                                    
                                    # Vider le buffer après la lecture
                                    enable_raw_mode()
                                    while wait_for_input(timeout=0.001):
                                        pass
                                    disable_raw_mode()
                                    
                                    # Revenir au premier accord
                                    prog_index = 0
                                    chord_name = progression_accords[prog_index]
                                    target_notes = self.chord_set[chord_name]
                                    live.update(self.create_live_display(chord_name, prog_index, len(progression_accords)), refresh=True)
                                    enable_raw_mode()
                                    break
                                elif action == 'next':
                                    skip_progression = True
                                    break
                                elif action is True:  # 'q' pressed
                                    break

                            for msg in self.inport.iter_pending():
                                if msg.type == 'note_on' and msg.velocity > 0:
                                    notes_currently_on.add(msg.note)
                                    attempt_notes.add(msg.note)
                                elif msg.type == 'note_off':
                                    notes_currently_on.discard(msg.note)

                            if not notes_currently_on and attempt_notes:
                                chord_attempts += 1
                                progression_total_attempts += 1

                                if self.use_timer and not is_progression_started:
                                    is_progression_started = True
                                    start_time = time.time()

                                is_correct, recognized_name, recognized_inversion = self.check_chord(attempt_notes, chord_name, target_notes)

                                if is_correct:
                                    success_msg = f"[bold green]Correct ! {chord_name}[/bold green]\nNotes jouées : [{get_colored_notes_string(attempt_notes, target_notes)}]"
                                    disable_raw_mode()
                                    live.update(success_msg, refresh=True)
                                    enable_raw_mode()
                                    time.sleep(2)
                                    if chord_attempts == 1:
                                        progression_correct_count += 1
                                    prog_index += 1
                                    break
                                else:
                                    error_msg = f"[bold red]Incorrect.[/bold red] Vous avez joué : {recognized_name if recognized_name else 'Accord non reconnu'}\nNotes jouées : [{get_colored_notes_string(attempt_notes, target_notes)}]"
                                    disable_raw_mode()
                                    live.update(error_msg, refresh=True)
                                    time.sleep(2)
                                    live.update(self.create_live_display(chord_name, prog_index, len(progression_accords)), refresh=True)
                                    enable_raw_mode()
                                    attempt_notes.clear()

                            time.sleep(0.01)
                    finally:
                        disable_raw_mode()

                if self.exit_flag:
                    break

            if not self.exit_flag and not skip_progression:
                # Si la progression n'est pas sautée, afficher les statistiques
                self.session_correct_count += progression_correct_count
                self.session_total_attempts += progression_total_attempts
                self.session_total_count += len(progression_accords)

                self.console.print(f"\n--- Statistiques de cette progression ---")
                self.console.print(f"Accords à jouer : [bold cyan]{len(progression_accords)}[/bold cyan]")
                self.console.print(f"Tentatives totales : [bold yellow]{progression_total_attempts}[/bold yellow]")
                self.console.print(f"Réussis du premier coup : [bold green]{progression_correct_count}[/bold green]")

                if progression_total_attempts > 0:
                    accuracy = (progression_correct_count / progression_total_attempts) * 100
                    self.console.print(f"Précision : [bold cyan]{accuracy:.1f}%[/bold cyan]")

                if self.use_timer and is_progression_started:
                    end_time = time.time()
                    self.elapsed_time = end_time - start_time
                    self.console.print(f"\nTemps pour la progression : [bold cyan]{self.elapsed_time:.2f} secondes[/bold cyan]")

                # Utiliser la nouvelle méthode pour la saisie instantanée
                self.wait_for_end_choice()
                if not self.exit_flag:
                    clear_screen()

            elif skip_progression:
                self.console.print("\n[bold yellow]Passage à la progression suivante.[/bold yellow]")
                time.sleep(1)

        if self.use_timer:
            display_stats_fixed(self.session_correct_count, self.session_total_attempts, self.session_total_count, self.elapsed_time)
        else:
            self.console.print("\nAffichage des statistiques.")            
            display_stats_fixed(self.session_correct_count, self.session_total_attempts, self.session_total_count)

        self.console.print("\nAppuyez sur une touche pour retourner au menu principal.")
        self.clear_midi_buffer()
        wait_for_any_key(self.inport)

def cadence_mode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set):
    mode = CadenceMode(inport, outport, use_timer, timer_duration, progression_selection_mode, play_progression_before_start, chord_set)
    mode.run()
# modes/reverse_chord_mode.py
import time
from .chord_mode_base import ChordModeBase
from music_theory import recognize_chord, get_note_name
from keyboard_handler import wait_for_input, enable_raw_mode, disable_raw_mode
from data.chords import enharmonic_map

class ReverseChordMode(ChordModeBase):
    def __init__(self, inport, outport, chord_set):
        super().__init__(inport, outport, chord_set)
        # Ce mode n'utilise pas les compteurs classiques car il ne "teste" pas
        # mais on peut garder une trace du nombre d'accords reconnus
        #self.recognized_count = 0
        #self.total_played = 0

    def recognize_and_display_chord(self, attempt_notes):
        """Reconnaît et affiche l'accord joué"""
        if len(attempt_notes) > 1:
            #self.total_played += 1
            chord_name, inversion_label = recognize_chord(attempt_notes)
            
            if chord_name:
                #self.recognized_count += 1
                enharmonic_name = enharmonic_map.get(chord_name)
                if enharmonic_name:
                    self.console.print(f"Accord reconnu : [bold green]{chord_name}[/bold green] ou [bold green]{enharmonic_name}[/bold green] ({inversion_label})\n")
                else:
                    self.console.print(f"Accord reconnu : [bold green]{chord_name}[/bold green] ({inversion_label})\n")
            else:
                # Afficher les notes jouées en rouge si l'accord n'est pas reconnu
                colored_string = ", ".join([f"[bold red]{get_note_name(n)}[/bold red]" for n in sorted(list(attempt_notes))])
                self.console.print(f"[bold red]Accord non reconnu.[/bold red] Notes jouées : [{colored_string}]\n")
        else:
            self.console.print("[bold yellow]Veuillez jouer au moins 3 notes pour former un accord.[/bold yellow]\n")

    def run(self):
        def pre_display():
            self.console.print("Jouez un accord sur votre clavier MIDI.")
            self.console.print("Appuyez sur 'q' pour quitter.")
            self.console.print("\nCe mode reconnaît les accords à 3 ou 4 notes en position fondamentale ainsi qu'en 1er et 2ème (et 3ème) renversement, quelle que soit l'octave.")
            self.console.print("---")

        # Utiliser la méthode display_header de la classe mère avec pre_display
        self.display_header("Reconnaissance d'accords", "Mode Reconnaissance d'accords (Tous les accords)", "cyan")

        pre_display()

        # Activer le mode raw pour la saisie instantanée
        enable_raw_mode()
        
        try:
            while not self.exit_flag:
                self.clear_midi_buffer()
                
                # Utiliser la méthode collect_notes de la classe mère
                attempt_notes, ready = self.collect_notes()
                
                if not ready:
                    # Si collect_notes retourne False, c'est que l'utilisateur a quitté
                    break
                
                # Reconnaître et afficher l'accord
                self.recognize_and_display_chord(attempt_notes)

            # Mettre à jour les statistiques de session pour utiliser la méthode de la classe mère
            #self.session_total_count = self.total_played
            #self.session_correct_count = self.recognized_count
            #self.session_total_attempts = self.total_played
            
            # Utiliser la méthode de statistiques de la classe mère
        #self.show_overall_stats_and_wait()
        finally:
            disable_raw_mode()
            
    def display_recognition_stats(self):
        pass

def reverse_chord_mode(inport, outport, chord_set):
    """Point d'entrée pour le mode reconnaissance d'accords"""
    mode = ReverseChordMode(inport, outport, chord_set)
    mode.run()
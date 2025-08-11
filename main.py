# main.py
import mido
from rich.console import Console

# Importer les modules refactorisés
from settings import Settings
import midi_handler
import music_theory
import ui

# Importer les classes des modes
from modes.single_chord_mode import SingleChordMode
# from modes.listen_reveal_mode import ListenRevealMode
# ... etc.

def main():
    console = Console()
    settings = Settings()

    # Sélection des ports
    inport_name = midi_handler.select_midi_port("input", console)
    if not inport_name: return
    outport_name = midi_handler.select_midi_port("output", console)
    if not outport_name: return

    try:
        with mido.open_input(inport_name) as inport, mido.open_output(outport_name) as outport:
            while True:
                # Appliquer le choix du set d'accords
                current_chord_set = music_theory.all_chords if settings.chord_set_choice == 'all' else music_theory.three_note_chords
                
                choice = ui.display_main_menu(console)

                if choice == '1':
                    # Lancer le mode Explorateur (qui n'est pas un mode de "jeu", donc peut être une fonction simple)
                    ui.chord_explorer_mode(outport, console)
                elif choice == '2':
                    mode = SingleChordMode(console, inport, outport, settings, current_chord_set)
                    mode.run()
                # ... autres elif pour les autres modes ...
                elif choice == '11':
                    ui.options_menu(console, settings)
                elif choice == '12':
                    console.print("Arrêt du programme.", style="bold red")
                    break
                
                # Attendre une touche avant de ré-afficher le menu
                console.print("\nAppuyez sur une touche pour retourner au menu principal.")
                midi_handler.wait_for_any_key(inport)

    except Exception as e:
        console.print(f"[bold red]Une erreur critique est survenue : {e}[/bold red]")

if __name__ == "__main__":
    main()
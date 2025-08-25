# ui.py
from music_theory import get_note_name
from rich.console import Console
from messages import UI

# Initialisation de la console Rich
console = Console()

def get_colored_notes_string(played_notes, correct_notes):
    """
    Retourne une chaîne de caractères avec les notes jouées, colorées en fonction de leur justesse.
    
    Correction de bug : cette fonction est maintenant plus intelligente.
    - Vert : La note jouée est exactement la bonne (même note, même octave).
    - Jaune : La note jouée est la bonne, mais dans une octave différente.
    - Rouge : La note jouée est incorrecte.
    """
    output_parts = []
    
    # Créer un ensemble des classes de hauteur correctes (indépendant de l'octave)
    correct_pitch_classes = {note % 12 for note in correct_notes}
    
    for note in sorted(played_notes):
        note_name = get_note_name(note)
        
        if note in correct_notes:
            # Correspondance parfaite (note et octave)
            output_parts.append(f"[bold green]{note_name}[/bold green]")
        elif (note % 12) in correct_pitch_classes:
            # Bonne note, mais mauvaise octave
            output_parts.append(f"[bold yellow]{note_name}[/bold yellow]")
        else:
            # Mauvaise note
            output_parts.append(f"[bold red]{note_name}[/bold red]")
            
    return ", ".join(output_parts)

def display_stats(correct_count, total_count, elapsed_time=None):
    """Affiche les statistiques de performance."""
    console.print(UI.SESSION_SUMMARY)
    if total_count > 0:
        pourcentage = (correct_count / total_count) * 100
        console.print(UI.CORRECT_CHORDS.format(correct_count=correct_count))
        console.print(UI.INCORRECT_CHORDS.format(incorrect_count=total_count - correct_count))
        console.print(UI.SUCCESS_RATE.format(percentage=pourcentage))
    else:
        console.print(UI.NO_CHORDS_PLAYED)
    if elapsed_time is not None:
        console.print(UI.ELAPSED_TIME.format(elapsed_time=elapsed_time))
    console.print("-------------------------")

def display_stats_fixed(correct_count, total_attempts, total_chords, elapsed_time=None):
    """Affiche les statistiques de performance corrigées."""
    console.print(UI.SESSION_SUMMARY_FIXED)
    if total_attempts > 0:
        accuracy = (correct_count / total_attempts) * 100
        console.print(UI.TOTAL_ATTEMPTS.format(total_attempts=total_attempts))
        console.print(UI.SUCCESSFUL_ATTEMPTS.format(correct_count=correct_count))
        console.print(UI.FAILED_ATTEMPTS.format(failed_count=total_attempts - correct_count))
        console.print(UI.GLOBAL_ACCURACY.format(accuracy=accuracy))
        
        if total_chords > 0:
            avg_attempts_per_chord = total_attempts / total_chords
            console.print(UI.AVG_ATTEMPTS_PER_CHORD.format(avg_attempts=avg_attempts_per_chord))
    else:
        console.print(UI.NO_ATTEMPTS_RECORDED)
    
    if elapsed_time is not None:
        console.print(UI.ELAPSED_TIME.format(elapsed_time=elapsed_time))

def create_degrees_table(tonalite: str, chords_in_scale: list, chords_to_highlight: list = None) -> "Table":
    """Crée et retourne une table Rich pour les degrés d'une tonalité, avec surlignage optionnel."""
    from rich.table import Table
    from screen_handler import int_to_roman

    if chords_to_highlight is None:
        chords_to_highlight = []

    table = Table(title=UI.TONALITY_TITLE.format(tonality=tonalite), border_style="blue")
    table.add_column(UI.DEGREE_COLUMN, justify="center", style="bold cyan")
    table.add_column(UI.CHORD_COLUMN, justify="center")

    for i, chord_name in enumerate(chords_in_scale, 1):
        roman_degree = int_to_roman(i)

        # Définir le style de l'accord
        if chord_name in chords_to_highlight:
            style = "bold magenta"
        else:
            style = "yellow"

        table.add_row(roman_degree, f"[{style}]{chord_name}[/]")

    return table
    console.print("-------------------------")

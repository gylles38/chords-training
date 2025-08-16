# ui.py
from music_theory import get_note_name
from rich.console import Console

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
    console.print("\n--- Bilan de la session totale ---")
    if total_count > 0:
        pourcentage = (correct_count / total_count) * 100
        console.print(f"Accords corrects : [bold green]{correct_count}[/bold green]")
        console.print(f"Accords incorrects : [bold red]{total_count - correct_count}[/bold red]")
        console.print(f"Taux de réussite : [bold cyan]{pourcentage:.2f}%[/bold cyan]")
    else:
        console.print("Aucun accord ou progression d'accords n'a été joué.")
    if elapsed_time is not None:
        console.print(f"Temps écoulé : [bold cyan]{elapsed_time:.2f} secondes[/bold cyan]")
    console.print("-------------------------")

def display_stats_fixed(correct_count, total_attempts, total_chords, elapsed_time=None):
    """Affiche les statistiques de performance corrigées."""
    console.print("\n--- Bilan de la session ---")
    if total_attempts > 0:
        accuracy = (correct_count / total_attempts) * 100
        console.print(f"Tentatives totales : [bold yellow]{total_attempts}[/bold yellow]")
        console.print(f"Tentatives réussies : [bold green]{correct_count}[/bold green]")
        console.print(f"Tentatives échouées : [bold red]{total_attempts - correct_count}[/bold red]")
        console.print(f"Précision globale : [bold cyan]{accuracy:.2f}%[/bold cyan]")
        
        if total_chords > 0:
            avg_attempts_per_chord = total_attempts / total_chords
            console.print(f"Moyenne tentatives/accord : [bold magenta]{avg_attempts_per_chord:.1f}[/bold magenta]")
    else:
        console.print("Aucune tentative enregistrée.")
    
    if elapsed_time is not None:
        console.print(f"Temps écoulé : [bold cyan]{elapsed_time:.2f} secondes[/bold cyan]")
    console.print("-------------------------")

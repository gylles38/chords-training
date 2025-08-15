def tonal_progression_mode(inport, outport, chord_set):
    """Mode qui joue une progression d'accords puis demande à l'utilisateur de la rejouer."""
    current_tonalite = None
    current_progression_name = None
    current_progression_accords = None
    
    while True:
        clear_screen()
        console.print(Panel(
            Text("Mode Progression Tonale", style="bold bright_magenta", justify="center"),
            title="Progression Tonale",
            border_style="bright_magenta"
        ))
        
        if current_tonalite is None:
            current_tonalite, gammes = random.choice(list(gammes_majeures.items()))
            gammes_filtrees = [g for g in gammes if g in chord_set]
            
            current_progression_name, degres_progression = random.choice(list(tonal_progressions.items()))
            
            current_progression_accords = []
            for degre in degres_progression:
                index = DEGREE_MAP.get(degre)
                if index is not None and index < len(gammes_filtrees):
                    current_progression_accords.append(gammes_filtrees[index])
        
        console.print(f"Tonalité : [bold yellow]{current_tonalite}[/bold yellow]")
        console.print(f"Progression : [bold cyan]{current_progression_name}[/bold cyan]")
        console.print(f"Accords : [bold yellow]{' → '.join(current_progression_accords)}[/bold yellow]")
        
        console.print("\n[bold green]Écoutez la progression...[/bold green]")
        for chord_name in current_progression_accords:
            console.print(f"Joue : [bold bright_yellow]{chord_name}[/bold bright_yellow]")
            play_chord(outport, chord_set[chord_name], duration=1.0)
            time.sleep(0.3)
        
        console.print("\n[bold green]À vous de jouer! Répétez la progression accord par accord.[/bold green]")
        console.print("Appuyez sur 'r' pour réécouter la progression ou 'q' pour quitter en cours.")
        
        correct_count = 0
        skip_progression = False
        
        for chord_index, chord_name in enumerate(current_progression_accords):
            if skip_progression:
                break

            target_notes = chord_set[chord_name]
            
            with Live(console=console, screen=False, auto_refresh=True) as live:
                live.update(f"\nJouez l'accord ({chord_index+1}/{len(current_progression_accords)}): [bold yellow]{chord_name}[/bold yellow]")
                
                notes_currently_on = set()
                attempt_notes = set()
                
                while True:
                    char = wait_for_input(timeout=0.01)
                    if char:
                        char = char.lower()
                        if char == 'q':
                            skip_progression = True
                            break
                        if char == 'r':
                            live.console.print("[bold blue]Réécoute de la progression...[/bold blue]")
                            for name in current_progression_accords:
                                play_chord(outport, chord_set[name], duration=1.0)
                                time.sleep(0.3)
                            live.update(f"\nJouez l'accord ({chord_index+1}/{len(current_progression_accords)}): [bold yellow]{chord_name}[/bold yellow]")
                            continue
                    
                    for msg in inport.iter_pending():
                        if msg.type == 'note_on' and msg.velocity > 0:
                            notes_currently_on.add(msg.note)
                            attempt_notes.add(msg.note)
                        elif msg.type == 'note_off':
                            notes_currently_on.discard(msg.note)
                    
                    if not notes_currently_on and attempt_notes:
                        recognized_name, inversion_label = recognize_chord(attempt_notes)
                        
                        if recognized_name and is_enharmonic_match_improved(recognized_name, chord_name, None) and len(attempt_notes) == len(target_notes):
                            colored_notes = get_colored_notes_string(attempt_notes, target_notes)
                            live.console.print(f"Notes jouées : [{colored_notes}]")
                            live.console.print("[bold green]Correct ![/bold green]")
                            correct_count += 1
                            time.sleep(1)
                            break
                        else:
                            colored_string = get_colored_notes_string(attempt_notes, target_notes)
                            
                            if recognized_name:
                                live.console.print(f"[bold red]Incorrect.[/bold red] Vous avez joué : {recognized_name} ({inversion_label})")
                            else:
                                live.console.print("[bold red]Incorrect. Réessayez.[/bold red]")
                            
                            live.console.print(f"Notes jouées : [{colored_string}]")
                            attempt_notes.clear()
                    
                    time.sleep(0.01)
                
                if skip_progression:
                    break
        
        if not skip_progression:
            total_chords = len(current_progression_accords)
            accuracy = (correct_count / total_chords) * 100 if total_chords > 0 else 0
            
            console.print("\n--- Résultats de la progression ---")
            console.print(f"Accords corrects : [bold green]{correct_count}/{total_chords}[/bold green]")
            console.print(f"Précision : [bold cyan]{accuracy:.2f}%[/bold cyan]")
            console.print("----------------------------------")

        choice = Prompt.ask(
            "\nProgression terminée ! Appuyez sur Entrée pour choisir une autre progression ou 'q' pour revenir au menu principal...", 
            console=console, 
            choices=["", "q"], 
            show_choices=False
        )

        if choice == '':
            pass
        elif choice == 'q':
            current_tonalite = None
            current_progression_name = None
            current_progression_accords = None
            break


# data/modulations.py

"""
Ce fichier définit les exercices de modulation.
Chaque modulation est un dictionnaire avec les clés suivantes :
- 'name': Le nom de la modulation (ex: "Vers le ton de la dominante").
- 'description': Une explication de la modulation.
- 'progression': Une liste de degrés. La logique du mode se chargera de
                 traduire ces degrés en accords réels en fonction d'une
                 tonalité de départ.

Syntaxe spéciale pour les degrés dans 'progression':
- Les degrés standards (ex: 'I', 'IV', 'V', 'vi') se réfèrent à la tonalité de DÉPART.
- "V/V" signifie "le V du V". C'est un accord d'emprunt qui prépare la nouvelle tonalité.
- "I_new", "IV_new", etc., se réfèrent aux degrés dans la NOUVELLE tonalité.
- La logique du mode doit être capable de parser cela pour générer la progression.
"""

modulations = [
    {
        "name": "Modulation vers la Dominante (V)",
        "description": "Une des modulations les plus courantes. On utilise l'accord de dominante de la nouvelle tonalité pour 'annoncer' le changement.",
        "progression_degrees": ["I", "IV", "V/V", "V_new_I"],
        "explanation_template": "Modulation de {start_key} vers sa dominante, {target_key}. La progression utilise {pivot_chord_name} (le V de {target_key}) pour préparer la nouvelle tonique."
    },
    {
        "name": "Modulation vers la Sous-dominante (IV)",
        "description": "Une modulation douce, souvent réalisée en utilisant la tonique de départ pour pivoter vers la nouvelle tonalité.",
        "progression_degrees": ["I", "V", "I", "IV_new_I"],
        "explanation_template": "Modulation de {start_key} vers sa sous-dominante, {target_key}. L'accord {pivot_chord_name} (I) sert de pivot avant de passer à {target_key}."
    },
    {
        "name": "Modulation vers le Relatif Mineur (vi)",
        "description": "Passe d'une tonalité majeure à sa relative mineure. L'accord du 6ème degré (vi) sert de pivot car il est le 1er degré de la nouvelle tonalité.",
        "progression_degrees": ["I", "vi", "V/vi", "vi_new_i"],
        "explanation_template": "Modulation de {start_key} vers son relatif mineur, {target_key}. L'accord {pivot_chord_name} (le V de {target_key}) sert à établir la nouvelle tonalité mineure."
    },
    {
        "name": "Modulation vers le Ton Homonyme Mineur",
        "description": "Change le mode de majeur à mineur tout en gardant la même tonique. Crée un changement d'ambiance dramatique.",
        "progression_degrees": ["I", "IV", "V", "i_new_i"],
        "explanation_template": "Modulation de {start_key} vers son ton homonyme, {target_key}. La progression se termine sur l'accord de tonique mineur pour un changement de couleur saisissant."
    },
     {
        "name": "Anatole (Rhythm Changes Bridge)",
        "description": "Une progression célèbre utilisée comme pont dans de nombreux standards de jazz, basée sur un cycle de dominantes.",
        "progression_degrees": ["V/vi", "V/ii", "V/V", "V"],
        "explanation_template": "La progression 'Anatole' ou 'Rhythm Changes Bridge' module rapidement à travers un cycle de dominantes secondaires, partant de {start_key}."
    }
]

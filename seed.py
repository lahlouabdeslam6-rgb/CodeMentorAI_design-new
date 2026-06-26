import os, sys
sys.path.insert(0, os.path.dirname(__file__))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

from core.models import Formation, Cours, Exercice, QuestionDiagnostic, OptionDiag, Profil

# Set specialite for existing professor profiles
prof_specialites = {
    10: 'JavaScript',
}
for uid, spec in prof_specialites.items():
    prof = Profil.objects(user_id=uid, role='professor').first()
    if prof:
        prof.specialite = spec
        prof.save()
        print(f'Specialite definie: {prof.username} - {spec}')

# Seed Formations
formations = [
    {'nom': 'JavaScript', 'slug': 'javascript', 'description': 'Maîtrise JavaScript du débutant à l\'expert : variables, DOM, async, frameworks.', 'emoji': '🟨', 'professor_id': 10, 'ordre': 1},
    {'nom': 'Python', 'slug': 'python', 'description': 'Apprends Python : syntaxe, POO,数据分析, automatisation et backend.', 'emoji': '🐍', 'professor_id': 10, 'ordre': 2},
    {'nom': 'Java', 'slug': 'java', 'description': 'Développe avec Java : POO, Spring, applications d\'entreprise.', 'emoji': '☕', 'professor_id': 10, 'ordre': 3},
    {'nom': 'PHP', 'slug': 'php', 'description': 'Crée des sites dynamiques avec PHP et MySQL.', 'emoji': '🐘', 'professor_id': 10, 'ordre': 4},
    {'nom': 'React', 'slug': 'react', 'description': 'Construis des UIs modernes avec React, hooks, et écosystème.', 'emoji': '⚛️', 'professor_id': 10, 'ordre': 5},
    {'nom': 'Laravel', 'slug': 'laravel', 'description': 'Développe des applications web robustes avec Laravel.', 'emoji': '🎸', 'professor_id': 10, 'ordre': 6},
]
for f in formations:
    if not Formation.objects(slug=f['slug']).first():
        Formation(**f).save()
        print(f'Formation créée: {f["nom"]}')

# Seed Cours (modules within formations)
cours_data = [
    {'slug': 'intro-js', 'titre': 'Introduction à JavaScript', 'description': 'Découvre les bases de JavaScript : histoire, syntaxe, et premiers pas.', 'emoji': '📘', 'niveau': 'debutant', 'ordre': 1, 'category': 'JavaScript'},
    {'slug': 'variables-types', 'titre': 'Variables et types de données', 'description': 'Maîtrise les variables, chaînes, nombres, booléens, null et undefined.', 'emoji': '📦', 'niveau': 'debutant', 'ordre': 2, 'category': 'JavaScript'},
    {'slug': 'conditions', 'titre': 'Conditions et opérateurs', 'description': 'If, else, switch, opérateurs de comparaison et logiques.', 'emoji': '🔀', 'niveau': 'debutant', 'ordre': 3, 'category': 'JavaScript'},
    {'slug': 'boucles', 'titre': 'Boucles', 'description': 'For, while, do-while et itérations sur les tableaux.', 'emoji': '🔄', 'niveau': 'debutant', 'ordre': 4, 'category': 'JavaScript'},
    {'slug': 'fonctions', 'titre': 'Fonctions', 'description': 'Apprends à créer et utiliser des fonctions, paramètres, retour et portée.', 'emoji': '⚙️', 'niveau': 'debutant', 'ordre': 5, 'category': 'JavaScript'},
    {'slug': 'tableaux', 'titre': 'Tableaux avancés', 'description': 'Méthodes avancées : map, filter, reduce, spread.', 'emoji': '📊', 'niveau': 'intermediaire', 'ordre': 6, 'category': 'JavaScript'},
    {'slug': 'objets', 'titre': 'Objets', 'description': 'Manipule les objets, prototypes, classes ES6.', 'emoji': '🧩', 'niveau': 'intermediaire', 'ordre': 7, 'category': 'JavaScript'},
    {'slug': 'dom', 'titre': 'DOM et événements', 'description': 'Interagis avec le navigateur via le DOM et les événements.', 'emoji': '🌐', 'niveau': 'intermediaire', 'ordre': 8, 'category': 'JavaScript'},
    {'slug': 'async', 'titre': 'JavaScript asynchrone', 'description': 'Promises, async/await, et gestion des opérations asynchrones.', 'emoji': '⏳', 'niveau': 'avance', 'ordre': 9, 'category': 'JavaScript'},
]

for c in cours_data:
    if not Cours.objects(slug=c['slug']).first():
        Cours(**c).save()
        print(f'Cours créé: {c["titre"]}')

# Seed Exercices
exo_data = [
    {'titre': 'Hello World', 'difficulte': 'facile', 'categorie': 'Syntaxe', 'points': 10, 'enonce': 'Écris un programme qui affiche "Hello, World!" dans la console.', 'slug_cours': 'intro-js'},
    {'titre': 'Calculatrice simple', 'difficulte': 'facile', 'categorie': 'Opérateurs', 'points': 15, 'enonce': 'Crée une fonction qui additionne deux nombres et retourne le résultat.', 'slug_cours': 'variables-types'},
    {'titre': 'Pair ou Impair', 'difficulte': 'moyen', 'categorie': 'Conditions', 'points': 20, 'enonce': 'Écris une fonction qui détermine si un nombre est pair ou impair.', 'slug_cours': 'conditions'},
    {'titre': 'Compter les voyelles', 'difficulte': 'moyen', 'categorie': 'Boucles', 'points': 20, 'enonce': 'Écris une fonction qui compte le nombre de voyelles dans une chaîne.', 'slug_cours': 'boucles'},
    {'titre': 'Fonction fléchée', 'difficulte': 'facile', 'categorie': 'Fonctions', 'points': 15, 'enonce': "Convertis une fonction classique en fonction fléchée.", 'slug_cours': 'fonctions'},
    {'titre': 'Filtrer tableau', 'difficulte': 'moyen', 'categorie': 'Tableaux', 'points': 25, 'enonce': "Utilise filter() pour garder uniquement les nombres pairs d'un tableau.", 'slug_cours': 'tableaux'},
    {'titre': 'Créer une classe', 'difficulte': 'moyen', 'categorie': 'Objets', 'points': 25, 'enonce': 'Crée une classe Personne avec nom et âge, et une méthode afficher().', 'slug_cours': 'objets'},
    {'titre': 'Manipulation DOM', 'difficulte': 'difficile', 'categorie': 'DOM', 'points': 30, 'enonce': "Crée un bouton qui change la couleur d'un paragraphe au clic.", 'slug_cours': 'dom'},
    {'titre': 'Appel API async', 'difficulte': 'difficile', 'categorie': 'Async', 'points': 35, 'enonce': "Écris une fonction async qui récupère des données depuis une API.", 'slug_cours': 'async'},
]

for e in exo_data:
    if not Exercice.objects(titre=e['titre']).first():
        cours = Cours.objects(slug=e['slug_cours']).first()
        if cours:
            Exercice(titre=e['titre'], difficulte=e['difficulte'], categorie=e['categorie'], points=e['points'], enonce=e['enonce'], cours=cours).save()
            print(f'Exercice créé: {e["titre"]}')

# Seed Diagnostic Questions
questions = [
    {
        'texte': 'Quelle est la bonne façon de déclarer une variable en JavaScript ?',
        'code': '',
        'niveau': 'debutant',
        'options': [
            {'texte': 'var x = 5;', 'est_correcte': True},
            {'texte': 'variable x = 5;', 'est_correcte': False},
            {'texte': 'int x = 5;', 'est_correcte': False},
            {'texte': 'x := 5;', 'est_correcte': False},
        ]
    },
    {
        'texte': "Quelle méthode permet d'ajouter un élément à la fin d'un tableau ?",
        'code': '',
        'niveau': 'debutant',
        'options': [
            {'texte': 'push()', 'est_correcte': True},
            {'texte': 'pop()', 'est_correcte': False},
            {'texte': 'shift()', 'est_correcte': False},
            {'texte': 'unshift()', 'est_correcte': False},
        ]
    },
    {
        'texte': 'Quel mot-clé permet de déclarer une variable avec une portée de bloc ?',
        'code': 'if (true) { ___ x = 10; }',
        'niveau': 'intermediaire',
        'options': [
            {'texte': 'let', 'est_correcte': True},
            {'texte': 'var', 'est_correcte': False},
            {'texte': 'const', 'est_correcte': True},
            {'texte': 'int', 'est_correcte': False},
        ]
    },
]

for q in questions:
    opts = [OptionDiag(**o) for o in q['options']]
    QuestionDiagnostic(texte=q['texte'], code=q['code'], niveau=q['niveau'], options=opts).save()
    print(f'Question créée: {q["texte"][:40]}')

print('\nSeed terminé !')

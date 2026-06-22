import os, sys
sys.path.insert(0, os.path.dirname(__file__))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

from core.models import Cours, Exercice, QuestionDiagnostic, OptionDiag

# Seed Cours
cours_data = [
    {'slug': 'intro-js', 'titre': 'Introduction à JavaScript', 'description': 'Découvre les bases de JavaScript : histoire, syntaxe, et premiers pas.', 'emoji': '📘', 'niveau': 'debutant', 'ordre': 1},
    {'slug': 'variables-types', 'titre': 'Variables et types de données', 'description': 'Maîtrise les variables, chaînes, nombres, booléens, null et undefined.', 'emoji': '📦', 'niveau': 'debutant', 'ordre': 2},
    {'slug': 'fonctions', 'titre': 'Fonctions', 'description': 'Apprends à créer et utiliser des fonctions, paramètres, retour et portée.', 'emoji': '⚙️', 'niveau': 'debutant', 'ordre': 3},
    {'slug': 'objets-tableaux', 'titre': 'Objets et tableaux', 'description': 'Manipule les objets, tableaux et méthodes associées.', 'emoji': '🧩', 'niveau': 'intermediaire', 'ordre': 4},
    {'slug': 'dom', 'titre': 'DOM et événements', 'description': 'Interagis avec le navigateur via le DOM et les événements.', 'emoji': '🌐', 'niveau': 'intermediaire', 'ordre': 5},
    {'slug': 'async', 'titre': 'JavaScript asynchrone', 'description': 'Promises, async/await, et gestion des opérations asynchrones.', 'emoji': '⏳', 'niveau': 'avance', 'ordre': 6},
]

for c in cours_data:
    if not Cours.objects(slug=c['slug']).first():
        Cours(**c).save()
        print(f'Cours créé: {c["titre"]}')

# Seed Exercices
exo_data = [
    {'titre': 'Hello World', 'difficulte': 'facile', 'categorie': 'Syntaxe', 'points': 10, 'enonce': 'Écris un programme qui affiche "Hello, World!" dans la console.', 'slug_cours': 'intro-js'},
    {'titre': 'Calculatrice simple', 'difficulte': 'facile', 'categorie': 'Opérateurs', 'points': 15, 'enonce': 'Crée une fonction qui additionne deux nombres et retourne le résultat.', 'slug_cours': 'variables-types'},
    {'titre': 'Pair ou Impair', 'difficulte': 'moyen', 'categorie': 'Conditions', 'points': 20, 'enonce': 'Écris une fonction qui détermine si un nombre est pair ou impair.', 'slug_cours': 'fonctions'},
    {'titre': 'Inverser tableau', 'difficulte': 'moyen', 'categorie': 'Tableaux', 'points': 25, 'enonce': "Écris une fonction qui inverse l'ordre des éléments d'un tableau.", 'slug_cours': 'objets-tableaux'},
    {'titre': 'Manipulation DOM', 'difficulte': 'difficile', 'categorie': 'DOM', 'points': 30, 'enonce': "Crée un bouton qui change la couleur d'un paragraphe au clic.", 'slug_cours': 'dom'},
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

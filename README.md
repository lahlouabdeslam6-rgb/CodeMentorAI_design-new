# CodeMentor AI

Plateforme intelligente d'apprentissage du développement informatique avec parcours adaptatif, tuteur IA, exercices corrigés automatiquement et examens par matière.

---

## Architecture

| Couche | Technologie |
|--------|-------------|
| Backend | Django 5.2 + Python 3.14 |
| Base de données | MongoDB 8.3 (via mongoengine ODM) + SQLite (auth Django) |
| Frontend | Django Templates + CSS personnalisé (Dark UI) |
| IA | Moteur de recherche plein texte dans les leçons + réponses structurées |
| Auth | Sessions Django + backend email/username |

## Fonctionnalités

### Rôles

- **Étudiant** : test de niveau, cours, leçons, exercices, examens, tuteur IA, progression par matière
- **Professeur** : gestion des cours, leçons, exercices, suivi des étudiants, statistiques XP par matière
- **Administrateur** : gestion des utilisateurs, demandes de mot de passe, création de professeurs

### Parcours d'apprentissage

Chaque matière (JavaScript, Python, PHP, Java, React, Laravel, C++) suit le même parcours :

```
Test de niveau → Cours → Leçons → Exercices → Examen → Certification
```

- **Test de niveau** obligatoire avant d'accéder au contenu
- Niveaux déterminés : Débutant (0-40%), Intermédiaire (41-70%), Avancé (71-100%)
- **XP par matière** : chaque matière a son propre compteur (FormationProgress)
- **8 exercices** requis pour débloquer l'examen de la matière
- **+100 XP** à la réussite de l'examen

### Tuteur IA

Moteur de recherche intégré dans les leçons :
1. Recherche par mots-clés dans les titres (×5) et contenus (×1) des leçons
2. Réponses structurées : explication, code, erreurs fréquentes, conseil, leçons recommandées
3. Si aucune leçon ne correspond → connaissances générales + ressources externes (MDN, docs officielles)
4. Contexte automatique : matière, niveau, leçons terminées

### Exercices

- Liés à une leçon spécifique (ReferenceField `lesson`)
- Correction automatique par comparaison textuelle
- Points XP attribués à la matière uniquement
- Page dédiée par leçon listant tous les exercices associés

### Examens

- 15 QCM par matière (5 débutant + 5 intermédiaire + 5 avancé)
- Timer de 60 minutes
- Seuil de réussite : 60%
- Pénalité en cas d'échec : -100 XP, réinitialisation des exercices
- Pénalité de timeout : -50 XP

### Interface

- Thème sombre (#080808, or #D4A843, blanc)
- Grille de fond, animations au scroll, design responsive
- Barre de navigation adaptée à chaque rôle
- Tableau de bord avec progression par matière

## Pages principales

| URL | Description |
|-----|-------------|
| `/` | Landing page avec statistiques dynamiques |
| `/dashboard/` | Dashboard étudiant (XP, niveaux, progression) |
| `/cours/` | Catalogue des formations |
| `/cours/<slug>/` | Détail d'une formation avec cours |
| `/cours/<slug>/lecon/` | Leçon avec exercices associés |
| `/cours/<slug>/lecon/exercices/` | Liste des exercices d'une leçon |
| `/exercice/<id>/` | Exercice individuel |
| `/examens/` | Liste des examens par matière |
| `/examen/` | Examen final d'une matière |
| `/tuteur/` | Tuteur IA avec contexte matière |
| `/niveau-test/` | Test de niveau général |
| `/test/<slug>/` | Test de niveau par matière |
| `/contact-admin/` | Demander un changement de mot de passe |
| `/profile/edit/` | Modifier son profil (email) |

### Professeur

| URL | Description |
|-----|-------------|
| `/professor/dashboard/` | Dashboard professeur (stats, étudiants, graphiques) |
| `/professor/courses/` | Gestion des cours |
| `/professor/lessons/<slug>/` | Gestion des leçons d'un cours |
| `/professor/exercises/<slug>/` | Gestion des exercices avec leçon associée |
| `/professor/students/` | Liste des étudiants avec XP par matière |

### Administration

| URL | Description |
|-----|-------------|
| `/admin-panel/` | Dashboard administrateur |
| `/admin-panel/students/` | Gestion des étudiants |
| `/admin-panel/professors/` | Gestion des professeurs |
| `/admin-panel/password-requests/` | Demandes de changement de mot de passe |

## Modèles de données (MongoDB)

### `formations` — Formations (matières)
- nom, slug, description, emoji, ordre

### `cours` — Cours / modules
- titre, slug, description, emoji, niveau, category (formation), professor_id

### `lessons` — Leçons
- cours (ref), titre, content (Markdown), ordre

### `exercices` — Exercices
- cours (ref), lesson (ref), titre, enonce, correction, difficulte, points

### `formations_progress` — Progression XP par matière
- user_id, formation_nom, xp, completed_exercises, exam_passed

### `niveaux_matieres` — Tests de niveau par matière
- user_id, formation_nom, niveau, test_complete

### `progressions` — Progression dans les cours
- user_id, cours (ref), pourcentage, lecons_accessed

### `resolutions` — Résultats d'exercices
- user_id, exercice (ref), resolu, note

### `acces_examens` — Accès aux examens
- user_id, formation_nom, debloque, examen_reussi

### `password_change_requests` — Demandes de changement de mot de passe
- user_id, username, email, new_password (hashé), status

## Installation

```bash
# Cloner
git clone https://github.com/lahlouabdeslam6-rgb/CodeMentorAI_design-new.git
cd CodeMentorAI_design-new

# Installer les dépendances
pip install django mongoengine pymongo markdown

# Lancer MongoDB (doit tourner sur localhost:27017)
# Base de données : codementor_ai

# Appliquer les migrations SQLite (auth)
python manage.py migrate

# Lancer le serveur
python manage.py runserver 0.0.0.0:8001
```

### Seeds

```bash
# Créer les formations, cours, leçons, exercices
python seed.py

# Créer le compte admin
python seed_admin.py

# Créer les questions d'examen (105 QCM)
python seed_questions.py
```

## Dépendances

- Django 5.2.15
- mongoengine 0.29.3
- pymongo 4.17.0
- markdown 3.10.2
- MongoDB 8.3.4
- Python 3.14.3

---

Projet développé par Ismail Lahlou — PFA 2026

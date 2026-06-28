# CodeMentor AI

Plateforme intelligente d'apprentissage du développement informatique avec parcours adaptatif, tuteur IA, exercices auto-corrigés, examens par matière et système de certification.

---

## 1. Présentation du projet

**Objectif** : Proposer un parcours d'apprentissage structuré et autonome pour les développeurs, avec un suivi individuel par matière (JavaScript, Python, PHP, Java, React, Laravel, C++, C#, anglais).

**Problème résolu** : Les plateformes d'apprentissage manquent souvent de granularité — un étudiant peut être avancé en Python mais débutant en JavaScript. CodeMentor AI traite chaque matière comme un parcours indépendant avec son propre test de niveau, sa progression XP, ses exercices, son examen et sa certification. L'échec dans une matière n'affecte pas les autres.

**Fonctionnement général** : Inscription → approbation par admin → test de niveau par matière → cours adaptés au niveau → exercices → examen final chronométré → certificat téléchargeable. Trois rôles (Étudiant, Professeur, Administrateur) gèrent la plateforme. Un Tuteur IA (recherche par mots-clés dans les leçons) assiste les étudiants.

---

## 2. Architecture globale

```
┌───────────────────────────────────────────────────────────────────┐
│                        NAVIGATEUR                                 │
│              HTML/CSS/JS — Chart.js CDN — window.print()          │
│       Templates Django — Dark theme (#080808 / #D4A843)           │
└──────────────────────────┬────────────────────────────────────────┘
                           │ HTTP (GET/POST)
                           ▼
┌───────────────────────────────────────────────────────────────────┐
│                       DJANGO 5.2                                   │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  core/views   │  │ admin_views  │  │professor_views│             │
│  │  (étudiant)   │  │ (admin)      │  │ (professeur)  │             │
│  │  1450 lignes  │  │ 565 lignes   │  │ 596 lignes    │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                 │                  │                       │
│         ▼                 ▼                  ▼                       │
│  ┌──────────────────────────────────────────────────────┐          │
│  │            core/models.py (mongoengine)               │          │
│  │  19 documents — profils, formations, cours,           │          │
│  │  exercices, examens, certificats, chat, etc.          │          │
│  └──────────────────────┬───────────────────────────────┘          │
│                         │                                           │
│  ┌──────────────────────▼───────────────────────────────┐          │
│  │  MOTEURS SPÉCIALISÉS                                  │          │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │          │
│  │  │tuteur_engine  │  │ core/utils   │  │decorators  │ │          │
│  │  │recherche      │  │ scoring,     │  │rôle guard  │ │          │
│  │  │plein texte    │  │ progression  │  │@student_   │ │          │
│  │  │dans leçons    │  │ vérification │  │required    │ │          │
│  │  └──────────────┘  └──────────────┘  └────────────┘ │          │
│  └──────────────────────────────────────────────────────┘          │
└──────────────────────────┬────────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
┌──────────────────────┐   ┌──────────────────────────┐
│    SQLite             │   │    MongoDB 8.3.4          │
│    db.sqlite3         │   │    database: codementor_ai│
│    ─ auth.User        │   │    Collections :          │
│    ─ sessions         │   │    profils, formations    │
│    ─ messages         │   │    cours, lessons,        │
│    ─ admin logs       │   │    exercices, examens,    │
│                       │   │    certificats, chat...   │
└──────────────────────┘   └──────────────────────────┘
```

Double base de données : SQLite pour l'authentification Django (User, sessions, messages) + MongoDB (via mongoengine 0.29.3) pour toutes les données métier. Ce choix permet de bénéficier de la flexibilité de MongoDB (documents dénormalisés, pas de migrations, schéma évolutif) tout en conservant la simplicité de Django auth sur SQLite.

---

## 3. Structure des dossiers

```
CodeMentorAI_design new/
│
├── config/                       # Configuration Django
│   ├── __init__.py               # Package Python
│   ├── settings.py               # 92 lignes — DB, apps, templates, sécurité
│   ├── urls.py                   # 12 lignes — root URLconf (admin + core.urls)
│   └── wsgi.py                   # 5 lignes — point d'entrée WSGI
│
├── core/                         # Application principale (tout le métier)
│   ├── __init__.py               # Package Python
│   ├── apps.py                   # AppConfig Django
│   ├── admin.py                  # Commentaire (MongoDB non supporté par admin Django)
│   ├── models.py                 # 324 lignes — 19 modèles MongoDB
│   ├── views.py                  # 1450 lignes — ~35 vues étudiant
│   ├── admin_views.py            # 565 lignes — 14 vues admin
│   ├── professor_views.py        # 596 lignes — 15 vues professeur
│   ├── tuteur_engine.py          # 456 lignes — moteur de recherche IA
│   ├── urls.py                   # 64 lignes — 64 routes
│   ├── utils.py                  # 67 lignes — scoring, progression
│   ├── decorators.py             # 49 lignes — 3 décorateurs de rôle
│   ├── auth_backend.py           # 18 lignes — login par email/username
│   ├── context_processors.py     # 8 lignes — injecte profil dans les templates
│   ├── management/commands/
│   │   └── backfill_emails.py    # Commande pour remplir les emails vides
│   └── migrations/
│       └── __init__.py           # Vides (MongoDB schemaless)
│
├── static/css/                   # Styles CSS (pas de préprocesseur)
│   ├── main.css                  # 1891 lignes — design système complet
│   ├── dashboard.css             # 229 lignes — styles dashboard
│   └── exam.css                  # 115 lignes — styles examens
│
├── templates/                    # Templates Django
│   ├── base.html                 # Template racine (nav, footer, toast, Chart.js)
│   ├── core/                     # 24 templates étudiant
│   ├── admin/                    # 9 templates admin
│   └── professor/                # 10 templates professeur
│
├── media/                        # Uploads (PDF de leçons) — vide actuellement
├── db.sqlite3                    # Base auth Django
├── manage.py                     # Point d'entrée Django
├── seed.py                       # Seed formations, cours, exercices
├── seed_admin.py                 # Seed admin user
├── seed_questions.py             # Seed 105 questions d'examen
└── .gitignore                    # __pycache__, .env, db.sqlite3, media/
```

---

## 4. Structure des fichiers principaux

### Noyau métier

| Fichier | Lignes | Rôle principal |
|---|---|---|
| `core/models.py` | 324 | 19 documents MongoDB (toutes les données métier) |
| `core/views.py` | 1450 | Toutes les vues étudiant : dashboard, cours, leçons, exercices, examens, certificats, tuteur, inscription, profil |
| `core/admin_views.py` | 565 | Panneau d'administration : utilisateurs, professeurs, stats, mots de passe |
| `core/professor_views.py` | 596 | Panneau professeur : CRUD cours/leçons/exercices, suivi étudiants |
| `core/tuteur_engine.py` | 456 | Moteur de recherche dans les leçons par mots-clés |
| `core/urls.py` | 64 | 64 URL patterns (31 étudiant + 14 admin + 19 professeur) |
| `core/utils.py` | 67 | Fonctions partagées : scoring, vérification accès examen |
| `core/decorators.py` | 49 | `@student_required`, `@admin_required`, `@professor_required` |
| `core/auth_backend.py` | 18 | Authentification par email ou nom d'utilisateur |
| `core/context_processors.py` | 8 | Injecte `profil` dans le contexte de tous les templates |

### Configuration

| Fichier | Lignes | Rôle |
|---|---|---|
| `config/settings.py` | 92 | Configuration Django : bases de données, apps, templates, sécurité |
| `config/urls.py` | 12 | Inclusion de `core.urls` + admin Django + media en debug |
| `config/wsgi.py` | 5 | Point d'entrée WSGI pour le serveur |

### Frontend

| Fichier | Lignes | Contenu |
|---|---|---|
| `static/css/main.css` | 1891 | Design system : variables CSS, navigation, formulaires, cartes, grilles, hero section, Tuteur IA, formations, administration, light mode |
| `static/css/dashboard.css` | 229 | Dashboard étudiant : cartes de stats, anneaux de progression, roadmap, activités |
| `static/css/exam.css` | 115 | Cartes d'examen (verrouillé/débloqué/réussi/échoué), badges, barres de progression |

---

## 5. Base de données

### Modèles MongoDB (mongoengine — 19 documents)

```
AUTH & PROFIL
┌──────────────┐     ┌──────────────────────┐
│ User (SQLite)│     │ Profil (profils)     │
│ id (PK)      │────→│ user_id (IntField)   │
│ username     │     │ username, email      │
│ email        │     │ role [student|professor|admin]│
│ password     │     │ status [pending|approved|rejected]│
└──────────────┘     │ niveau (global)      │
                     │ points, serie_jours  │
                     │ specialite (prof)    │
                     └──────────────────────┘

CONTENU PÉDAGOGIQUE
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ Formation   │     │ Cours        │     │ Lesson       │
│ (formations)│     │ (cours)      │     │ (lessons)    │
│─────────────│     │──────────────│     │──────────────│
│ _id (UUID)  │     │ _id (UUID)   │     │ _id (UUID)   │
│ nom         │←────│ formation_nom│     │ cours (Ref)  │←──────┐
│ slug        │     │ slug         │     │ titre        │       │
│ description │     │ titre        │     │ content (MD) │       │
│ emoji       │     │ description  │     │ video_url    │       │
│ ordre       │     │ emoji        │     │ pdf_url      │       │
│ professor_id│     │ niveau       │     │ chapitre     │       │
└─────────────┘     │ ordre        │     │ ordre        │       │
                    │ category     │     └──────┬───────┘       │
                    │ chapitres[]  │            │               │
                    │ professor_id │            │               │
                    └──────┬───────┘            │               │
                           │                    │               │
                    ┌──────▼───────┐   ┌────────▼───────┐      │
                    │ Exercice     │   │ Progression    │      │
                    │ (exercices)  │   │ (progressions) │      │
                    │──────────────│   │────────────────│      │
                    │ _id (UUID)   │   │ _id (UUID)     │      │
                    │ cours (Ref)──┼───│ cours (Ref)────┼──────┘
                    │ lesson (Ref)─┼───│ user_id        │
                    │ titre        │   │ pourcentage    │
                    │ enonce       │   │ lecons_accessed│
                    │ correction   │   └────────────────┘
                    │ difficulte   │
                    │ categorie    │
                    │ points       │
                    │ lesson_nom   │
                    └──────────────┘

PROGRESSION ÉTUDIANT PAR FORMATION
┌────────────────────┐  ┌──────────────────┐  ┌────────────────────┐
│ FormationProgress  │  │ NiveauMatiere    │  │ ScoreExercice      │
│ (formations_progr) │  │(niveaux_matieres)│  │ (scores_exercices) │
│────────────────────│  │──────────────────│  │────────────────────│
│ _id (UUID)         │  │ _id (UUID)       │  │ _id (UUID)         │
│ user_id            │  │ user_id          │  │ user_id            │
│ formation_nom      │  │ formation_nom    │  │ exercice (Ref)     │
│ xp                 │  │ niveau (str)     │  │ score_obtenu       │
│ completed_exercises│  │ score, total     │  │ score_max          │
│ exam_passed        │  │ test_complete    │  │ date_completion    │
│ level              │  └──────────────────┘  │ tentatives         │
└────────────────────┘                       └────────────────────┘

EXAMEN
┌─────────────────┐  ┌────────────────┐  ┌──────────────────┐  ┌─────────────────────┐
│ QuestionExamen  │  │ AccesExamen    │  │ ExamAttempt      │  │ ExamHistory         │
│(questions_examen)│  │(acces_examens) │  │ (exam_attempts)  │  │ (exam_history)      │
│─────────────────│  │────────────────│  │──────────────────│  │─────────────────────│
│ _id (UUID)      │  │ _id (UUID)     │  │ _id (UUID)       │  │ _id (UUID)          │
│ question        │  │ user_id        │  │ user_id          │  │ user_id             │
│ options[]       │  │ formation_nom  │  │ formation_nom    │  │ formation_nom       │
│ reponse_correcte│  │ debloque       │  │ start_time       │  │ score_examen        │
│ difficulte      │  │ score_global   │  │ end_time         │  │ reussi (bool)       │
│ categorie       │  │ examen_passe   │  │ duration_minutes │  │ penalite_xp         │
│ formation_nom   │  │ examen_reussi  │  │ is_finished      │  │ type_echec          │
└─────────────────┘  │ score_examen   │  │ penalty_applied  │  │ exercices_reinit()  │
                     └────────────────┘  │ reponses[]       │  └─────────────────────┘
                                          │ score            │
                                          │ total_questions  │
                                          └──────────────────┘

CERTIFICATION
┌─────────────────────┐  ┌──────────────────┐
│ StudentCertificate  │  │ Resolution       │
│ (student_certificat)│  │ (resolutions)    │
│─────────────────────│  │──────────────────│
│ _id (UUID)          │  │ _id (UUID)       │
│ user_id (UNIQUE+)   │  │ user_id          │
│ formation_nom (+)   │  │ exercice (Ref)   │
│ score, obtained_at  │  │ resolu, note     │
│ exam_id             │  │ date             │
└─────────────────────┘  └──────────────────┘
  (+) index unique composé

TESTS DE NIVEAU
┌──────────────────┐  ┌─────────────────────┐  ┌────────────────────┐
│ QuestionNiveau   │  │ QuestionDiagnostic  │  │ SessionDiagnostic  │
│(questions_niveau)│  │(questions_diagnostic)│  │(sessions_diagnostic)│
│──────────────────│  │─────────────────────│  │────────────────────│
│ _id (UUID)       │  │ _id (UUID)          │  │ _id (UUID)         │
│ formation_nom    │  │ texte, code         │  │ user_id            │
│ question         │  │ niveau              │  │ question_index     │
│ options[]        │  │ options[] (Embedded)│  │ terminee           │
│ reponse_correcte │  └─────────────────────┘  │ score, total       │
│ difficulte       │                           └────────────────────┘
└──────────────────┘

CHAT & UTILITAIRES
┌──────────────────┐  ┌──────────────────────────┐  ┌──────────────────────┐
│ MessageChat      │  │ Activite                 │  │ PasswordChangeRequest│
│ (messages_chat)  │  │ (activites)              │  │(password_change_reqs)│
│──────────────────│  │──────────────────────────│  │──────────────────────│
│ _id (UUID)       │  │ _id (UUID)               │  │ _id (UUID)           │
│ user_id          │  │ user_id                  │  │ user_id, username    │
│ role [user|ai]   │  │ type, description        │  │ email, new_password  │
│ contenu          │  │ date                     │  │ reason, status       │
│ date             │  └──────────────────────────┘  │ [pending/accepted/  │
└──────────────────┘                                 │  rejected]           │
                                                     └──────────────────────┘
```

### Relations clés

| Relation | Type | Implémentation |
|---|---|---|
| User (SQLite) → Profil (MongoDB) | 1:1 | `Profil.user_id` = `User.id` (IntField) |
| Formation → Cours | 1:N | `Cours.formation_nom` = `Formation.nom` (chaîne) |
| Cours → Lesson | 1:N | `Lesson.cours` = ReferenceField(Cours) |
| Cours → Exercice | 1:N | `Exercice.cours` = ReferenceField(Cours) |
| Lesson → Exercice | 1:N | `Exercice.lesson` = ReferenceField(Lesson) |
| Étudiant → FormationProgress | 1:N | `FormationProgress.user_id` = User.id |
| Étudiant → StudentCertificate | 1:N | `StudentCertificate.user_id` = User.id (+ index unique sur formation) |
| Étudiant → AccesExamen | 1:N | `AccesExamen.user_id` = User.id |

---

## 6. Authentification

**Backend** : `core/auth_backend.py` — `EmailOrUsernameBackend` qui permet la connexion avec l'email OU le nom d'utilisateur. Vérifie d'abord par email, puis par username.

**Login** : `CustomLoginView` (`views.py:20`) — après authentification réussie, redirige selon le rôle :
- `admin` → `/admin-panel/`
- `professor` → `/professor/`
- `student` → `/dashboard/`

**Inscription** : `register` (`views.py:300`) :
1. Valide le formulaire (nom, email, mot de passe)
2. Crée un `User` Django (is_active=True)
3. Crée un `Profil` MongoDB (role='student', status='pending')
4. Redirige vers `approval_pending` — l'étudiant doit attendre l'approbation admin

**Permissions** : Les trois décorateurs dans `core/decorators.py` vérifient `Profil.role` avant chaque vue :
- `@student_required` : role == 'student' AND status == 'approved'
- `@admin_required` : role == 'admin'
- `@professor_required` : role == 'professor'

---

## 7. Fonctionnement des rôles

### Administrateur
**Vues** : `core/admin_views.py` (14 vues) — accessible via `/admin-panel/*`

Actions :
- **Dashboard** : graphiques Chart.js (inscriptions par mois, formations, activités), stats globales (nb utilisateurs, cours, leçons, exercices)
- **Gestion des étudiants** : liste paginée, recherche par nom/email, filtre par statut, actions :
  - Approuver un compte (`status: pending → approved`)
  - Rejeter un compte (`status: pending → rejected`)
  - Activer/désactiver (is_active toggle)
  - Supprimer
- **Gestion des professeurs** : CRUD complet avec spécialité :
  - Création → `_assurer_formation()` crée automatiquement la formation associée ET génère 10 questions de niveau
  - Édition de la spécialité
  - Suppression
- **Détail utilisateur** : vue complète d'un étudiant (profil, progression par matière, XP, activités récentes)
- **Réinitialisation de mot de passe** : changement direct sans approbation
- **Demandes de mot de passe** : liste des requêtes avec action accepter/rejeter

### Professeur
**Vues** : `core/professor_views.py` (15 vues) — accessible via `/professor/*`

Actions :
- **Dashboard** : 6 formations suivies, nombre total d'étudiants, graphique XP des 15 derniers jours
- **Cours** : CRUD filtré par spécialité (`Formation.objects(professor_id=uid)`)
  - Création : titre, description, emoji, niveau, catégorie, chapitres (saisis comme texte, un par ligne)
- **Leçons** : CRUD par cours, regroupées par chapitre
  - Contenu en Markdown, URL vidéo, upload PDF (validation : .pdf, max 20 MB)
  - Ordre manuel via champ `ordre`
- **Exercices** : CRUD par cours, liés à une leçon
  - Énoncé, correction, difficulté (Débutant/Intermédiaire/Avancé), catégorie, points
  - Stats : nombre de tentatives, taux de réussite
- **Suivi étudiants** : liste paginée avec pour chaque étudiant :
  - XP par formation, exercices résolus, statut certification (✅ + date ou —)

### Étudiant
**Vues** : `core/views.py` (~35 vues) — accessible via `/dashboard/`, `/cours/`, `/examens/`, `/tuteur/`, etc.

Actions :
- Dashboard personnel : XP par matière, série de jours, roadmap, activités récentes
- Parcours d'apprentissage complet par formation
- Test de niveau général + test de niveau par matière
- Consultation de cours et leçons (Markdown → HTML)
- Résolution d'exercices avec correction automatique
- Passage d'examens chronométrés (60 min, 15 QCM)
- Obtention et consultation de certificats (modale sur la même page)
- Chat avec le Tuteur IA (recherche dans les leçons)
- Modification du profil (email)
- Demande de changement de mot de passe

---

## 8. Fonctionnement des cours

**Création** : Le professeur (dans sa spécialité) crée un cours via `professor_course_create` (`professor_views.py:120`). Champs : titre, description, emoji, niveau (Débutant/Intermédiaire/Avancé), catégorie, liste de chapitres. Le cours est automatiquement lié à la formation du professeur via `formation_nom`.

**Organisation** : Les cours sont regroupés par formation. Chaque cours a :
- Un niveau correspondant au résultat du test de l'étudiant (Débutant → voit les cours Débutant)
- Une liste de chapitres (simples chaînes, pas de modèle séparé)
- Un champ `ordre` pour le tri

**Affichage** pour l'étudiant :
1. `cours_list` (`views.py:555`) : catalogue des formations avec progression, niveau, statut test
2. `formation_detail` (`views.py:610`) : vue d'une formation avec :
   - Niveau de l'étudiant, score du test
   - Liste des cours filtrés par niveau
   - Progression : XP, exercices complétés, accès examen, certification
3. `cours_detail` (`views.py:660`) : cours individuel avec :
   - Chapitres et leçons associées
   - Barre de progression par chapitre
   - Pourcentage de complétion

**Progression** : `Progression` enregistre `lecons_accessed[]` (liste d'entiers). Le pourcentage est calculé comme `(nb leçons accédées / nb total de leçons) × 100`.

---

## 9. Fonctionnement des leçons

**Relation** : Les leçons (`Lesson`) sont liées à un cours via `ReferenceField(Cours)` et appartiennent à un chapitre (champ `chapitre` — chaîne). Pas de modèle Chapitre séparé — les chapitres sont définis dans le cours comme une liste de noms.

**Création** : `professor_lesson_create` (`professor_views.py:245`) :
- Champs : titre, contenu (Markdown), URL vidéo, PDF (upload)
- Le professeur sélectionne un chapitre parmi ceux définis dans le cours
- L'ordre est défini manuellement (champ `ordre` IntegerField)

**Affichage** (`lecon_detail`, `views.py:710`) :
1. Rendu du Markdown en HTML (bibliothèque `markdown`)
2. Navigation ← Leçon précédente / Leçon suivante → (basée sur `ordre`)
3. Liste des exercices liés à cette leçon
4. La leçon est marquée comme accédée dans `Progression.lecons_accessed`
5. Le pourcentage de progression du cours est recalculé

---

## 10. Fonctionnement des exercices

**Création** : `professor_exercise_create` (`professor_views.py:386`) :
- Champs : titre, énoncé (description du problème), correction (solution attendue), difficulté, catégorie, points
- Lié à un cours (`ReferenceField`) et à une leçon (`ReferenceField`)
- Affiché dans l'ordre du champ `ordre`

**Validation et correction automatique** (`exercice_detail`, `views.py:820`) :
1. L'étudiant soumet sa réponse (textarea)
2. Le système extrait les mots-clés de la correction (split sur espaces, filtre les mots courts)
3. Compte combien de ces mots-clés apparaissent dans la réponse de l'étudiant
4. Score = (mots-clés trouvés / mots-clés total) × 100
5. Si le score ≥ 70 → exercice considéré comme réussi
6. Met à jour `ScoreExercice` (conserve le meilleur score si plusieurs tentatives)
7. Appelle `enregistrer_score` (`utils.py:25`) :
   - Ajoute `Exercice.points` à `FormationProgress.xp`
   - Incrémente `completed_exercises`
   - Vérifie l'éligibilité à l'examen (≥ 8 exercices complétés)
   - Enregistre une `Activite`

**Progression** :
- `lecon_exercices` (`views.py:780`) : liste des exercices d'une leçon avec statut (score, tentatives)
- `resultat_exercice` : page de feedback après soumission (score, message, lien vers l'examen si débloqué)

---

## 11. Fonctionnement des tests de niveau

### Test par matière (obligatoire)

**Génération automatique des questions** (`_generer_questions_niveau` dans `admin_views.py`) :
- Appelée lors de la création d'une formation (dans `_assurer_formation`)
- 20 templates de questions génériques avec placeholder `{lang}`
- Exemple : `"Quelle est la syntaxe correcte pour déclarer une variable en {lang} ?"`
- Pioche aléatoirement 10 questions parmi les 20
- Stocke dans `QuestionNiveau` avec `formation_nom`

**Déroulement** (`test_niveau_matiere`, `views.py:401`) :
1. Vérifie que l'étudiant a le statut `approved`
2. Charge 10 questions depuis `QuestionNiveau` pour la formation donnée
3. Les mélange avec `random.shuffle`
4. Affiche les 10 QCM sur une seule page
5. Chaque champ radio est nommé `q_{{ q.id }}` (ObjectId MongoDB)

**Calcul du score** :
1. Pour chaque clé dans `request.POST` commençant par `q_` :
   - Extrait l'ObjectId de la question
   - Récupère `QuestionNiveau.objects(id=question_id)`
   - Compare `reponse_correcte` avec la réponse POST
2. Score = (bonnes réponses / 10) × 100
3. Niveau :
   - 0-40% → Débutant
   - 41-70% → Intermédiaire
   - 71-100% → Avancé
4. Stocke dans `NiveauMatiere`
5. Redirige vers la formation

### Test général (Diagnostic)
- Questions issues de `QuestionDiagnostic` (modèle avec `options` comme EmbeddedDocument list)
- Parcourues une par une avec session (`SessionDiagnostic`)
- Simple évaluation de niveau global — n'affecte pas l'accès aux formations

---

## 12. Fonctionnement des examens

### Conditions d'accès
1. Test de niveau passé (NiveauMatiere.test_complete = True)
2. ≥ 8 exercices complétés dans la formation (FormationProgress.completed_exercises ≥ 8)
3. Pas déjà certifié (pas de StudentCertificate pour cette formation)
4. Vérifié par `verifier_acces_examen` (`utils.py:43`)

### Déroulement

**Page d'accueil** (`examens_list`, `views.py:940`) :
- Affiche toutes les formations avec leur statut :
  - 🔒 Test de niveau non passé
  - 🔒 X/8 exercices (verrouillé tant que < 8)
  - ✅ Certification obtenue + date + bouton certificat (si déjà certifié)
  - 🟢 Examen prêt (si toutes conditions remplies)
  - 📝 Passer l'examen (si tentative précédente échouée)

**Passage de l'examen** (`examen_final`, `views.py:1010`) :
1. Clic "Démarrer" → crée `ExamAttempt` avec `start_time = now()`, `duration_minutes = 60`
2. Charge 15 questions `QuestionExamen` (5 Débutant + 5 Intermédiaire + 5 Avancé) pour la formation
3. Les mélange avec `random.shuffle`
4. Stocke les IDs dans `attempt.reponses` pour éviter les décalages d'ordre
5. Chronomètre côté client : timer JavaScript qui soumet automatiquement à 0
6. Vérification côté serveur : si `time > 60 min` → pénalité de timeout (-50 XP, exercices reset)

**Correction et scoring** :
1. Pour chaque réponse soumise, compare avec `QuestionExamen.reponse_correcte`
2. Utilise les IDs stockés dans `attempt.reponses` (pas une re-query)
3. Score = (bonnes réponses / total) × 100

**Résultat** :
- **≥ 60%** (Réussite) :
  - `AccesExamen.examen_reussi = True`
  - `StudentCertificate` créé (user_id, formation_nom, score, obtained_at)
  - `FormationProgress.xp += 100`
  - `FormationProgress.exam_passed = True`
  - Redirection vers `examen_reussi` (page de félicitations avec score, XP, lien certificat)
- **< 60%** (Échec) :
  - `ExamHistory` créé avec `reussi=False`, `penalite_xp=100`
  - `FormationProgress.xp -= 100` (minimum 0)
  - `FormationProgress.completed_exercises = 0`
  - Messages d'erreur : exercices et XP réinitialisés
- **Timeout** (pas de soumission dans les 60 min) :
  - Pénalité -50 XP
  - Exercices réinitialisés

**Navigation** : Une fois certifié, visiter `/examen/?formation=X` redirige vers `examen_reussi`.

---

## 13. Fonctionnement des certificats

**Génération** : Automatique dans `examen_final` (`views.py:1330`) sur score ≥ 60% :
- `StudentCertificate(user_id, formation_nom, score, obtained_at, exam_id)` est créé
- Index unique composé `(user_id, formation_nom)` empêche les doublons

**Stockage** : Document MongoDB (pas de fichier). Les données sont affichées dynamiquement dans une page HTML.

**Affichage** :
- Page `/certificats/` (`mes_certificats`, `views.py:1443`) : liste tous les certificats avec emoji, nom, date, score
- Clic "📄 Voir le certificat" : **modale dans la même page** (pas de redirection) :
  - 🏆 Sceau
  - "CERTIFICAT DE RÉUSSITE"
  - Nom de l'étudiant
  - Matière (ex: "Certification JavaScript")
  - Score % et date d'obtention
  - Signature "CodeMentor AI"
  - Trois boutons :
    - 🖨️ Imprimer → injection du contenu dans une zone d'impression cachée → `window.print()`
    - ⬇️ Télécharger (PDF) → idem (l'utilisateur choisit "Enregistrer au format PDF")
    - ❌ Fermer → masque la modale

**URL directe** : `/certificat/<slug>/` (vue `certificat`) accessible pour les liens partagés, avec redirection si non certifié.

---

## 14. Fonctionnement du Tuteur IA

**Fichier** : `core/tuteur_engine.py` (456 lignes)

**Mécanisme** : Moteur de recherche par mots-clés dans les leçons (pas d'IA générative).

1. **L'étudiant pose une question** (formulaire dans `tuteur.html`)
2. **`tuteur_message`** (`views.py:500`) :
   - Nettoie et enregistre le message dans `MessageChat` (role='user')
   - Appelle `repondre_question(contenu)` du moteur
3. **Analyse lexicale** (`tuteur_engine.py:repondre_question`) :
   - Tokenization : split sur espaces, suppression ponctuation
   - Stop words : français + anglais (150+ mots : le, la, de, du, the, and, for, etc.)
4. **Détection de commandes spéciales** :
   - "quiz" → génère 3 QCM aléatoires avec réponse
   - "exercice" → propose un exercice aléatoire
5. **Recherche dans les leçons** (fonction `_rechercher_dans_cours`) :
   - Parcourt TOUTES les leçons de toutes les formations
   - Scoring :
     - Mot présent dans le titre : ×5 points
     - Mot présent dans le contenu : ×1 point
     - Phrase entière trouvée textuellement : bonus ×2
   - Garde les 3 meilleures leçons (score ≥ 3)
6. **Construction de la réponse** (`_formater_reponse`) :
   - Explication générale
   - Extrait de la leçon trouvée
   - Exemple de code (si trouvé dans le contenu)
   - Erreurs fréquentes (extrapolées)
   - Conseils pédagogiques
   - Liens vers les leçons recommandées
   - Exercices associés
7. **Fallback** :
   - Si aucun résultat : vérifie des mots-clés génériques (variable, fonction, promesse, API REST, async, closure, etc.)
   - Si toujours rien : "Je n'ai pas trouvé de réponse dans mes cours"
8. **Enregistrement** : Réponse stockée dans `MessageChat` (role='ai'), affichée dans le chat

---

## 15. Parcours complet d'un étudiant

```
INSCRIPTION
    │
    ├── Création User Django (is_active=True)
    ├── Création Profil MongoDB (role=student, status=pending)
    └── Redirection vers page "En attente d'approbation"
    │
    ▼
APPROBATION ADMIN
    │
    ▼
DASHBOARD (/dashboard/)
    ├── Vue d'ensemble : XP par formation, série de jours
    ├── Roadmap : formations disponibles, progression
    └── Activités récentes
    │
    ▼
CATALOGUE (/cours/)
    ├── Liste des formations avec emoji et description
    ├── Statut : "Test de niveau requis" si non passé
    └── Redirection vers test si cliqué sans test
    │
    ▼
FORMATION (/formation/<slug>/)
    ├── Test de niveau obligatoire (/test/<slug>/)
    │   └── 10 QCM → Débutant (0-40%) / Intermédiaire (41-70%) / Avancé (71-100%)
    │
    ├── Cours filtrés par niveau
    │   └── COURS (/cours/<slug>/)
    │       ├── Chapitres et leçons
    │       └── Progression par chapitre
    │
    └── LEÇON (/cours/<slug>/lecon/)
        ├── Contenu Markdown rendu en HTML
        ├── Vidéo, PDF (si présents)
        ├── Navigation ← Précédent / Suivant →
        ├── Exercices liés à la leçon
        └── Marquée comme accédée → progression ++
    │
    ▼
EXERCICES (/cours/<slug>/lecon/exercices/)
    ├── Liste des exercices avec score et tentatives
    │
    └── EXERCICE (/exercice/<id>/)
        ├── Énoncé + zone de réponse
        ├── Soumission → correction automatique
        ├── Score sur 100, feedback
        ├── +XP si réussi
        └── Après 8 exercices → examen débloqué
    │
    ▼
EXAMEN (/examens/)
    ├── Statut : "Examen prêt" (vert)
    │
    └── EXAMEN (/examen/?formation=X)
        ├── Page d'accueil : durée, conditions
        ├── "Démarrer" → chronomètre 60 min
        ├── 15 QCM (5 débutant + 5 intermédiaire + 5 avancé)
        │
        ├── Score ≥ 60% : ✅ RÉUSSITE
        │   ├── +100 XP
        │   ├── Certificat créé
        │   ├── Page félicitations 🎉
        │   └── Formation certifiée
        │
        └── Score < 60% : ❌ ÉCHEC
            ├── -100 XP
            ├── Exercices réinitialisés à 0
            └── Doit refaire 8 exercices
    │
    ▼
CERTIFICATS (/certificats/)
    ├── Liste des certificats obtenus
    │
    └── CLIC "📄 Voir le certificat"
        ├── Modale dans la même page
        ├── Nom, matière, score %, date
        ├── Signature CodeMentor AI
        ├── 🖨️ Imprimer
        ├── ⬇️ Télécharger PDF
        └── ❌ Fermer
```

---

## 16. Technologies utilisées

| Technologie | Version | Rôle dans le projet |
|---|---|---|
| **Python** | 3.14.3 | Langage principal |
| **Django** | 5.2.15 | Framework web (MVT, sessions, auth, templates) |
| **mongoengine** | 0.29.3 | ODM MongoDB (déclaration des documents, requêtes) |
| **pymongo** | 4.17.0 | Driver MongoDB bas niveau (utilisé par mongoengine) |
| **MongoDB** | 8.3.4 | Base de données NoSQL (toutes les données métier) |
| **SQLite** | (built-in Django) | Base relationnelle (auth User, sessions, messages) |
| **markdown** | 3.10.2 | Rendu Markdown → HTML pour les leçons |
| **Chart.js** | 4.4.7 (CDN) | Graphiques du dashboard admin |
| **Google Fonts** | (CDN) | Polices Space Grotesk, Inter, Fira Code |
| **Git** | — | Contrôle de version, remote GitHub |

**Non utilisées** dans ce projet :
- Pas de Docker / docker-compose
- Pas de préprocesseur CSS (Sass, PostCSS, Tailwind)
- Pas de bundler JS (Webpack, Vite, esbuild)
- Pas de framework JS frontend (React, Vue, Angular)
- Pas de système de cache (Redis, Memcached)
- Pas de file d'attente (Celery, RQ)
- Pas de tests automatisés (aucun fichier test)
- Pas de ASGI / WebSocket
- Pas de base relationnelle autre que SQLite (pas de PostgreSQL, MySQL)

---

## 17. Sécurité

### Points forts
- **Décorateurs de rôle** : `@student_required`, `@admin_required`, `@professor_required` bloquent tout accès non autorisé au niveau de la vue
- **Double base** : les données métier sont isolées de l'auth Django — compromettre MongoDB ne donne pas accès aux mots de passe
- **CSRF protégé** : `CSRF_TRUSTED_ORIGINS` configuré
- **Upload PDF filtré** : extension `.pdf` + taille ≤ 20 MB
- **LoginRequired** : toutes les vues métier protégées par `@login_required`
- **Mots de passe hachés** : Django utilise PBKDF2+HMAC-SHA256

### Points faibles
- `DEBUG = True` en production (révèle des informations sensibles en cas d'erreur)
- `SECRET_KEY` codé en dur dans `settings.py` (devrait être en variable d'environnement)
- `ALLOWED_HOSTS = ['*']` en production (permet des attaques par en-tête Host)
- Pas de Content-Security-Policy, X-Frame-Options, HSTS
- Rendu Markdown sans échappement HTML (XSS potentiel via contenu de leçon)
- Pas de rate limiting sur login (brute-force possible)
- Aucune journalisation des actions sensibles
- Pas de vérification du contenu des PDF uploadés (seulement l'extension)

---

## 18. Performances

### Points forts
- MongoDB adapté : documents dénormalisés → peu de requêtes complexes
- Listes paginées (étudiants, professeurs)
- CSS minimal sans framework lourd
- Chart.js en CDN (un seul fichier externe)

### Optimisations possibles
1. **Index MongoDB** : seuls `StudentCertificate` a un index. Ajouter des index sur `user_id` et `(user_id, formation_nom)` dans tous les modèles fréquemment interrogés (ProfessionProgress, AccesExamen, NiveauMatiere, etc.)
2. **Requêtes N+1** : plusieurs boucles `for ... in ...` pourraient être remplacées par des requêtes MongoDB avec `in_` ou des agrégations
3. **Cache** : aucune couche de cache — chaque page est régénérée à chaque requête. Utiliser le cache Django (Redis) pour les données peu changeantes
4. **Tuteur IA** : parcourt toutes les leçons à chaque question. Solution : index texte MongoDB (`$text`) ou Elasticsearch
5. **Static files** : pas de `collectstatic` — en production, servir les fichiers statiques via NGINX ou CDN
6. **Middleware** : plusieurs middlewares Django chargés mais peu utilisés (CommonMiddleware, SecurityMiddleware)

---

## 19. Points forts

1. **Architecture trois rôles** : séparation claire des responsabilités (fichiers distincts + templates distincts + décorateurs)

2. **Parcours pédagogique complet** : chaque formation est un mini-parcours indépendant avec test → cours → exercices → examen → certificat

3. **Isolation par matière** : XP, progression, pénalités sont strictement limités à une formation — l'échec en JavaScript n'affecte pas Python

4. **Auto-génération des questions** : `_generer_questions_niveau()` crée 10 questions de test par formation à partir de 20 templates avec substitution de langage

5. **Système de motivation** : XP, séries de jours, niveaux, roadmap visuelle, badges de certification

6. **Tuteur IA intégré** : bien que basé sur des mots-clés, offre une réponse immédiate sans quitter la plateforme

7. **Système de pénalité dissuasif** : échec = -100 XP + exercices remis à zéro → encourage la préparation

8. **Double base de données** : choix pragmatique (SQLite pour l'auth simple et standard, MongoDB pour la flexibilité métier)

9. **Thème dark cohérent** : CSS variables, design responsive, animations, palette #080808 / #D4A843 / #FFFFFF

10. **Certificat en modale** : pas de redirection — expérience utilisateur fluide

---

## 20. Améliorations possibles

### Sécurité (priorité haute)
1. Désactiver `DEBUG = True` et restreindre `ALLOWED_HOSTS` en production
2. Externaliser `SECRET_KEY` dans une variable d'environnement (fichier `.env`)
3. Ajouter Content-Security-Policy, X-Frame-Options, HSTS via middleware
4. Nettoyer le HTML dans le rendu Markdown avec `bleach` ou `markdown.extensions.codehilite`
5. Rate limiting sur les endpoints de connexion (`django-ratelimit`)
6. Vérifier le contenu des PDF uploadés (pdfminer ou similaire)

### Base de données
7. Ajouter des index MongoDB sur `user_id` et `(user_id, formation_nom)` dans tous les modèles
8. Remplacer les chaînes `formation_nom` par des `ReferenceField` avec `reverse_delete_rule`
9. Uniformiser les relations : certaines utilisent `ReferenceField`, d'autres des chaînes

### Performances
10. Implémenter un cache Django (Redis) pour les formations et cours
11. Index texte MongoDB (`$text`) pour le Tuteur IA au lieu du parcours linéaire
12. Collecter les fichiers statiques avec `collectstatic` et servir via NGINX

### Tests et qualité
13. Ajouter des tests unitaires et d'intégration (Django TestCase)
14. Mettre en place du linting (ruff, mypy) et une CI (GitHub Actions)

### Fonctionnalités
15. Drag-and-drop pour ordonner les chapitres et leçons (interface professeur)
16. Génération PDF côté serveur avec `weasyprint` au lieu de `window.print()`
17. WebSockets pour le Tuteur IA (réponses en temps réel)
18. Historique des tentatives d'examen (actuellement une seule tentative conservée)
19. Badges supplémentaires (streak 7j, 30j, premier 100%, etc.)
20. Mode nuit/jour automatique (le CSS light mode existe déjà)

---

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

# Créer le compte admin (admin@codementor.ai / admin123)
python seed_admin.py

# Créer les questions d'examen (105 QCM pour 7 sujets)
python seed_questions.py
```

### Comptes par défaut

| Rôle | Email | Mot de passe |
|---|---|---|
| Administrateur | admin@codementor.ai | admin123 |
| Professeur | (créé via panneau admin) | — |
| Étudiant | (inscription libre) | — |

---

## Pages principales

| URL | Rôle | Description |
|---|---|---|
| `/` | Public | Landing page avec stats dynamiques |
| `/login/` | Public | Connexion email/username |
| `/register/` | Public | Inscription étudiant |
| `/dashboard/` | Étudiant | Dashboard personnel (XP, roadmap, activités) |
| `/cours/` | Étudiant | Catalogue des formations |
| `/cours/<slug>/` | Étudiant | Détail d'un cours avec chapitres |
| `/cours/<slug>/lecon/` | Étudiant | Leçon (Markdown, vidéo, exercices) |
| `/formation/<slug>/` | Étudiant | Vue d'une formation (cours, progression, test) |
| `/test/<slug>/` | Étudiant | Test de niveau par matière (10 QCM) |
| `/diagnostic/` | Étudiant | Test de niveau général |
| `/exercice/<id>/` | Étudiant | Exercice avec correction auto |
| `/cours/<slug>/lecon/exercices/` | Étudiant | Exercices d'une leçon |
| `/examens/` | Étudiant | Liste des examens par formation |
| `/examen/` | Étudiant | Examen final (15 QCM, 60 min) |
| `/examen/reussi/<slug>/` | Étudiant | Page félicitations 🎉 |
| `/certificats/` | Étudiant | Liste des certificats + modale |
| `/certificat/<slug>/` | Étudiant | Certificat (page directe) |
| `/tuteur/` | Étudiant | Tuteur IA |
| `/profile/edit/` | Étudiant | Modifier email |
| `/contact-admin/` | Étudiant | Demander changement mot de passe |
| `/professor/dashboard/` | Professeur | Dashboard professeur |
| `/professor/courses/` | Professeur | Gestion des cours |
| `/professor/students/` | Professeur | Suivi des étudiants |
| `/admin-panel/` | Admin | Dashboard admin (graphiques) |
| `/admin-panel/students/` | Admin | Gestion des étudiants |
| `/admin-panel/professors/` | Admin | Gestion des professeurs |
| `/admin-panel/password-requests/` | Admin | Demandes de mot de passe |

---

## Routes API (URL patterns)

```
Student URLs (31)
───────────────
/                                     → home
/login/                               → CustomLoginView
/register/                            → register
/logout/                              → logout_view
/dashboard/                           → dashboard
/cours/                               → cours_list
/cours/<slug>/                        → cours_detail
/formation/<slug>/                    → formation_detail
/cours/<slug>/lecon/                  → lecon_detail
/niveau-test/                         → niveau_test
/diagnostic/                          → diagnostic
/diagnostic/resultat/                 → diagnostic_resultat
/test/<slug>/                         → test_niveau_matiere
/tuteur/                              → tuteur
/tuteur/message/                      → tuteur_message
/cours/<slug>/lecon/exercices/        → lecon_exercices
/exercice/<pk>/                       → exercice_detail
/exercices/                           → exercices_list
/examens/                             → examens_list
/examen/                              → examen_final
/examen/resultat/                     → examen_resultat
/examen/reussi/<slug>/                → examen_reussi
/certificat/<slug>/                   → certificat
/certificats/                         → mes_certificats
/contact-admin/                       → contact_admin
/profile/edit/                        → profile_edit

Admin URLs (14)
─────────────
/admin-panel/                         → admin_dashboard
/admin-panel/students/                → admin_students
/admin-panel/students/<id>/approve/   → admin_approve_student
/admin-panel/students/<id>/reject/    → admin_reject_student
/admin-panel/students/<id>/toggle-active/ → admin_toggle_active
/admin-panel/students/<id>/delete/    → admin_delete_student
/admin-panel/professors/              → admin_professors
/admin-panel/professors/create/       → admin_professor_create
/admin-panel/professors/<id>/edit/    → admin_professor_edit
/admin-panel/professors/<id>/delete/  → admin_professor_delete
/admin-panel/user/<id>/               → admin_user_detail
/admin-panel/user/<id>/password-reset/ → admin_password_reset
/admin-panel/password-requests/       → admin_password_requests
/admin-panel/password-requests/<id>/<action>/ → admin_password_request_action

Professor URLs (19)
────────────────
/professor/                           → professor_dashboard
/professor/courses/                   → professor_courses
/professor/courses/create/            → professor_course_create
/professor/courses/<slug>/edit/       → professor_course_edit
/professor/courses/<slug>/delete/     → professor_course_delete
/professor/courses/<slug>/lessons/    → professor_lessons
/professor/courses/<slug>/lessons/create/ → professor_lesson_create
/professor/courses/<slug>/lessons/<id>/edit/ → professor_lesson_edit
/professor/courses/<slug>/lessons/<id>/delete/ → professor_lesson_delete
/professor/courses/<slug>/exercises/  → professor_exercises
/professor/courses/<slug>/exercises/create/ → professor_exercise_create
/professor/courses/<slug>/exercises/<id>/edit/ → professor_exercise_edit
/professor/courses/<slug>/exercises/<id>/delete/ → professor_exercise_delete
/professor/students/                  → professor_students
```

---

Projet développé par **Ismail Lahlou** — PFA 2026

Dépôt GitHub : https://github.com/lahlouabdeslam6-rgb/CodeMentorAI_design-new

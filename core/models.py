from datetime import datetime
from mongoengine import Document, StringField, IntField, BooleanField, DateTimeField, ReferenceField, ListField, FloatField, EmbeddedDocument, EmbeddedDocumentField


class Profil(Document):
    user_id = IntField(required=True)
    username = StringField(required=True)
    email = StringField(default='')
    role = StringField(choices=['student', 'professor', 'admin'], default='student')
    status = StringField(choices=['pending', 'approved', 'rejected'], default='approved')
    niveau = StringField(choices=['debutant', 'intermediaire', 'avance'], default='debutant')
    points = IntField(default=0)
    serie_jours = IntField(default=0)
    derniere_connexion = DateTimeField()
    cree_le = DateTimeField(default=datetime.now)
    fullname = StringField(default='')
    niveau_tested = BooleanField(default=False)
    specialite = StringField(default='')

    meta = {'collection': 'profils'}

    def get_niveau_label(self):
        return dict(Profil.niveau_choices).get(self.niveau, self.niveau)

    niveau_choices = [
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance', 'Avancé'),
    ]

    def __str__(self):
        return f"{self.username} ({self.role})"


class Formation(Document):
    nom = StringField(required=True, max_length=200)
    slug = StringField(required=True, unique=True)
    description = StringField(required=True)
    emoji = StringField(default='📘')
    image_url = StringField(default='')
    professor_id = IntField(default=0)
    ordre = IntField(default=0)

    meta = {'collection': 'formations', 'ordering': ['ordre']}

    def __str__(self):
        return self.nom


class Lesson(Document):
    cours = ReferenceField('Cours', required=True)
    titre = StringField(required=True, max_length=200)
    content = StringField(default='')
    video_url = StringField(default='')
    pdf_url = StringField(default='')
    chapitre = StringField(default='')
    ordre = IntField(default=0)

    meta = {'collection': 'lessons', 'ordering': ['ordre']}

    def __str__(self):
        return self.titre


class Cours(Document):
    slug = StringField(required=True, unique=True)
    titre = StringField(required=True, max_length=200)
    description = StringField(required=True)
    emoji = StringField(default='📘')
    niveau = StringField(choices=['debutant', 'intermediaire', 'avance'])
    ordre = IntField(default=0)
    professor_id = IntField(default=0)
    category = StringField(default='JavaScript')
    chapitres = ListField(StringField())

    meta = {'collection': 'cours', 'ordering': ['ordre']}

    def get_niveau_label(self):
        return dict(Cours.niveau_choices).get(self.niveau, self.niveau)

    niveau_choices = [
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance', 'Avancé'),
    ]

    def __str__(self):
        return self.titre


class Progression(Document):
    user_id = IntField(required=True)
    cours = ReferenceField(Cours, required=True)
    pourcentage = IntField(default=0)
    lecons_accessed = ListField(IntField(), default=[])

    meta = {'collection': 'progressions'}


class Activite(Document):
    user_id = IntField(required=True)
    type = StringField(choices=['cours', 'exercice', 'autre'])
    description = StringField(max_length=300)
    date = DateTimeField(default=datetime.now)

    meta = {'collection': 'activites', 'ordering': ['-date']}


class Exercice(Document):
    cours = ReferenceField(Cours)
    lesson = ReferenceField('Lesson')
    titre = StringField(required=True, max_length=200)
    difficulte = StringField(choices=['facile', 'moyen', 'difficile'])
    categorie = StringField(default='Général')
    points = IntField(default=10)
    enonce = StringField(default='')
    correction = StringField(default='')
    lesson_nom = StringField(default='')

    meta = {'collection': 'exercices'}

    def get_difficulte_label(self):
        return dict(Exercice.difficulte_choices).get(self.difficulte, self.difficulte)

    difficulte_choices = [
        ('facile', 'Facile'),
        ('moyen', 'Moyen'),
        ('difficile', 'Difficile'),
    ]


class Resolution(Document):
    user_id = IntField(required=True)
    exercice = ReferenceField(Exercice, required=True)
    resolu = BooleanField(default=False)
    note = IntField(default=0)
    date = DateTimeField(default=datetime.now)

    meta = {'collection': 'resolutions'}


class OptionDiag(EmbeddedDocument):
    texte = StringField(required=True, max_length=300)
    est_correcte = BooleanField(default=False)


class QuestionDiagnostic(Document):
    texte = StringField(required=True)
    code = StringField(default='')
    niveau = StringField(choices=['debutant', 'intermediaire', 'avance'], default='debutant')
    options = ListField(EmbeddedDocumentField(OptionDiag))

    meta = {'collection': 'questions_diagnostic'}


class SessionDiagnostic(Document):
    user_id = IntField(required=True)
    question_index = IntField(default=0)
    terminee = BooleanField(default=False)
    score = IntField(default=0)
    total = IntField(default=0)
    creee_le = DateTimeField(default=datetime.now)

    meta = {'collection': 'sessions_diagnostic'}


class MessageChat(Document):
    user_id = IntField(required=True)
    role = StringField(choices=['user', 'ai'])
    contenu = StringField(required=True)
    date = DateTimeField(default=datetime.now)

    meta = {'collection': 'messages_chat', 'ordering': ['date']}


class ScoreExercice(Document):
    user_id = IntField(required=True)
    exercice = ReferenceField(Exercice, required=True)
    score_obtenu = IntField(default=0)
    score_max = IntField(default=10)
    date_completion = DateTimeField(default=datetime.now)
    tentatives = IntField(default=1)

    meta = {'collection': 'scores_exercices'}


class QuestionExamen(Document):
    question = StringField(required=True)
    options = ListField(StringField())
    reponse_correcte = IntField(required=True)
    difficulte = StringField(choices=['debutant', 'intermediaire', 'avance'])
    categorie = StringField(default='Général')
    formation_nom = StringField(default='JavaScript')

    meta = {'collection': 'questions_examen'}


class AccesExamen(Document):
    user_id = IntField(required=True)
    formation_nom = StringField(default='JavaScript')
    debloque = BooleanField(default=False)
    date_deblocage = DateTimeField()
    score_global = FloatField(default=0.0)
    examen_passe = BooleanField(default=False)
    examen_reussi = BooleanField(default=False)
    date_examen = DateTimeField()
    score_examen = FloatField(default=0.0)

    meta = {'collection': 'acces_examens'}


class ExamAttempt(Document):
    user_id = IntField(required=True)
    formation_nom = StringField(default='JavaScript')
    start_time = DateTimeField(default=datetime.now)
    end_time = DateTimeField()
    duration_minutes = IntField(default=60)
    is_finished = BooleanField(default=False)
    penalty_applied = BooleanField(default=False)
    reponses = StringField(default='')
    score = IntField(default=0)
    total_questions = IntField(default=0)

    meta = {'collection': 'exam_attempts'}


class ExamHistory(Document):
    user_id = IntField(required=True)
    formation_nom = StringField(default='JavaScript')
    date = DateTimeField(default=datetime.now)
    score_examen = FloatField(default=0.0)
    reussi = BooleanField(default=False)
    penalite_xp = IntField(default=0)
    exercices_reinitialises = IntField(default=0)
    type_echec = StringField(default='note_insuffisante', choices=['note_insuffisante', 'temps_ecoule', 'abandon'])

    meta = {'collection': 'exam_history'}


class NiveauMatiere(Document):
    user_id = IntField(required=True)
    formation_nom = StringField(required=True)
    niveau = StringField(choices=['debutant', 'intermediaire', 'avance'], default='debutant')
    score = IntField(default=0)
    total = IntField(default=0)
    test_complete = BooleanField(default=False)
    completed_at = DateTimeField()

    meta = {'collection': 'niveaux_matieres'}


class FormationProgress(Document):
    user_id = IntField(required=True)
    formation_nom = StringField(required=True)
    xp = IntField(default=0)
    completed_exercises = IntField(default=0)
    exam_passed = BooleanField(default=False)
    level = StringField(choices=['debutant', 'intermediaire', 'avance'], default='debutant')

    meta = {'collection': 'formations_progress'}

    def get_level_display(self):
        return dict(FormationProgress.level_choices).get(self.level, self.level)

    level_choices = [
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance', 'Avancé'),
    ]


class PasswordChangeRequest(Document):
    user_id = IntField(required=True)
    username = StringField(required=True)
    email = StringField(default='')
    role = StringField(choices=['student', 'professor'], default='student')
    new_password = StringField(required=True)
    reason = StringField(default='')
    status = StringField(choices=['pending', 'accepted', 'rejected'], default='pending')
    created_at = DateTimeField(default=datetime.now)
    processed_at = DateTimeField()
    processed_by = IntField(default=0)

    meta = {'collection': 'password_change_requests'}

    def get_role_display(self):
        return dict(PasswordChangeRequest.role_choices).get(self.role, self.role)

    def get_status_display(self):
        return dict(PasswordChangeRequest.status_choices).get(self.status, self.status)

    role_choices = [
        ('student', 'Étudiant'),
        ('professor', 'Professeur'),
    ]
    status_choices = [
        ('pending', 'En attente'),
        ('accepted', 'Acceptée'),
        ('rejected', 'Refusée'),
    ]
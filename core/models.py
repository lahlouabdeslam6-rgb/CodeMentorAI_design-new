from datetime import datetime
from mongoengine import Document, StringField, IntField, BooleanField, DateTimeField, ReferenceField, ListField, FloatField, EmbeddedDocument, EmbeddedDocumentField


class Profil(Document):
    user_id = IntField(required=True)
    username = StringField(required=True)
    niveau = StringField(choices=['debutant', 'intermediaire', 'avance'], default='debutant')
    points = IntField(default=0)
    serie_jours = IntField(default=0)
    derniere_connexion = DateTimeField()

    meta = {'collection': 'profils'}

    def get_niveau_display(self):
        return dict(Profil.niveau_choices).get(self.niveau, self.niveau)

    niveau_choices = [
        ('debutant', 'Débutant'),
        ('intermediaire', 'Intermédiaire'),
        ('avance', 'Avancé'),
    ]

    def __str__(self):
        return f"{self.username} — {self.get_niveau_display()}"


class Cours(Document):
    slug = StringField(required=True, unique=True)
    titre = StringField(required=True, max_length=200)
    description = StringField(required=True)
    emoji = StringField(default='📘')
    niveau = StringField(choices=['debutant', 'intermediaire', 'avance'])
    ordre = IntField(default=0)

    meta = {'collection': 'cours', 'ordering': ['ordre']}

    def get_niveau_display(self):
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

    meta = {'collection': 'progressions'}

    def __str__(self):
        return f"{self.user_id} — {self.cours.titre} ({self.pourcentage}%)"


class Activite(Document):
    user_id = IntField(required=True)
    type = StringField(choices=['cours', 'exercice', 'autre'])
    description = StringField(max_length=300)
    date = DateTimeField(default=datetime.now)

    meta = {'collection': 'activites', 'ordering': ['-date']}

    def __str__(self):
        return f"{self.user_id} — {self.description[:50]}"


class Exercice(Document):
    cours = ReferenceField(Cours)
    titre = StringField(required=True, max_length=200)
    difficulte = StringField(choices=['facile', 'moyen', 'difficile'])
    categorie = StringField(default='Général')
    points = IntField(default=10)
    enonce = StringField(default='')
    correction = StringField(default='')

    meta = {'collection': 'exercices'}

    def get_difficulte_display(self):
        return dict(Exercice.difficulte_choices).get(self.difficulte, self.difficulte)

    difficulte_choices = [
        ('facile', 'Facile'),
        ('moyen', 'Moyen'),
        ('difficile', 'Difficile'),
    ]

    def __str__(self):
        return self.titre


class Resolution(Document):
    user_id = IntField(required=True)
    exercice = ReferenceField(Exercice, required=True)
    resolu = BooleanField(default=False)
    date = DateTimeField(default=datetime.now)

    meta = {'collection': 'resolutions'}

    def __str__(self):
        return f"{self.user_id} — {self.exercice.titre} {'✅' if self.resolu else '❌'}"


class OptionDiag(EmbeddedDocument):
    texte = StringField(required=True, max_length=300)
    est_correcte = BooleanField(default=False)

    def __str__(self):
        return self.texte[:60]


class QuestionDiagnostic(Document):
    texte = StringField(required=True)
    code = StringField(default='')
    niveau = StringField(choices=['debutant', 'intermediaire', 'avance'], default='debutant')
    options = ListField(EmbeddedDocumentField(OptionDiag))

    meta = {'collection': 'questions_diagnostic'}

    def __str__(self):
        return self.texte[:80]


class SessionDiagnostic(Document):
    user_id = IntField(required=True)
    question_index = IntField(default=0)
    terminee = BooleanField(default=False)
    score = IntField(default=0)
    total = IntField(default=0)
    creee_le = DateTimeField(default=datetime.now)

    meta = {'collection': 'sessions_diagnostic'}

    def __str__(self):
        return f"{self.user_id} — {self.score}/{self.total}"


class MessageChat(Document):
    user_id = IntField(required=True)
    role = StringField(choices=['user', 'ai'])
    contenu = StringField(required=True)
    date = DateTimeField(default=datetime.now)

    meta = {'collection': 'messages_chat', 'ordering': ['date']}

    def __str__(self):
        return f"[{self.role}] {self.user_id}: {self.contenu[:60]}"

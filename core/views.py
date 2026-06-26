import random
from datetime import datetime, timedelta, date
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from mongoengine import DoesNotExist, NotUniqueError, Q
from .models import (Profil, Formation, Cours, Lesson, Progression, Activite, Exercice,
                     Resolution, QuestionDiagnostic, SessionDiagnostic,
                     MessageChat, ScoreExercice, AccesExamen, QuestionExamen, ExamAttempt, ExamHistory,
                     NiveauMatiere, PasswordChangeRequest, FormationProgress, QuestionNiveau)
from .decorators import student_required, get_role_dashboard
from .utils import enregistrer_score
from .tuteur_engine import generer_reponse
import markdown
import bleach


class CustomLoginView(LoginView):
    template_name = 'core/login.html'

    def get_success_url(self):
        user = self.request.user
        profil = Profil.objects(user_id=user.id).first()
        if profil:
            if profil.role == 'admin':
                return reverse('admin_dashboard')
            elif profil.role == 'professor':
                return reverse('professor_dashboard')
        return reverse('dashboard')


def logout_view(request):
    logout(request)
    return redirect('home')


def home(request):
    total_formations = Formation.objects.count()
    valid_cours = Cours.objects(professor_id__ne=0)
    total_cours = valid_cours.count()
    valid_ids = [c.id for c in valid_cours]
    total_exercices = Exercice.objects(cours__in=valid_ids).count()
    total_lessons = Lesson.objects(cours__in=valid_ids).count()
    total_examens = QuestionExamen.objects.count()
    return render(request, 'core/home.html', {
        'total_formations': total_formations,
        'total_cours': total_cours,
        'total_exercices': total_exercices,
        'total_lessons': total_lessons,
        'total_examens': total_examens,
    })


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        errors = []
        if not username:
            errors.append("Le nom d'utilisateur est requis.")
        if User.objects.filter(username=username).exists():
            errors.append("Ce nom d'utilisateur est déjà pris.")
        if not email:
            errors.append("L'adresse email est requise.")
        elif User.objects.filter(email=email).exists():
            errors.append("Cette adresse email est déjà utilisée.")
        if password1 != password2:
            errors.append("Les mots de passe ne correspondent pas.")
        if password1 and len(password1) < 3:
            errors.append("Le mot de passe doit contenir au moins 3 caractères.")

        if errors:
            return render(request, 'core/register.html', {
                'form': type('obj', (object,), {'errors': {'__all__': errors}})(),
                'email': email,
            })

        user = User.objects.create_user(username=username, email=email, password=password1)
        Profil(user_id=user.id, username=username, role='student', status='pending', email=email).save()
        messages.success(request, "Compte créé ! Un administrateur doit approuver ton inscription avant que tu puisses accéder aux cours.")
        return redirect('login')

    return render(request, 'core/register.html', {'form': None, 'email': ''})


QUESTIONS_NIVEAU = [
    {
        'question': 'Quelle est la syntaxe correcte pour afficher un message dans la console ?',
        'options': ['print("Hello")', 'console.log("Hello")', 'echo "Hello"', 'System.out.println("Hello")'],
        'reponse': 1,
        'niveau': 'debutant',
    },
    {
        'question': 'Quel mot-clé permet de déclarer une constante en JavaScript ?',
        'options': ['var', 'let', 'const', 'int'],
        'reponse': 2,
        'niveau': 'debutant',
    },
    {
        'question': 'Quelle méthode ajoute un élément à la fin d\'un tableau ?',
        'options': ['pop()', 'push()', 'shift()', 'unshift()'],
        'reponse': 1,
        'niveau': 'debutant',
    },
    {
        'question': 'Qu\'est-ce qu\'une fonction fléchée (arrow function) ?',
        'options': [
            'function() {}',
            '() => {}',
            'def() :',
            'fn() ->',
        ],
        'reponse': 1,
        'niveau': 'intermediaire',
    },
    {
        'question': 'Quelle est la différence entre == et === ?',
        'options': [
            'Aucune différence',
            '== compare la valeur, === compare la valeur et le type',
            '=== compare uniquement le type',
            '== est plus rapide',
        ],
        'reponse': 1,
        'niveau': 'intermediaire',
    },
    {
        'question': 'Que retourne typeof [] en JavaScript ?',
        'options': ['"array"', '"object"', '"list"', '"undefined"'],
        'reponse': 1,
        'niveau': 'intermediaire',
    },
    {
        'question': 'Qu\'est-ce qu\'une Promise ?',
        'options': [
            'Une fonction synchrone',
            'Un objet représentant une valeur future',
            'Une boucle d\'événements',
            'Un type de variable',
        ],
        'reponse': 1,
        'niveau': 'avance',
    },
    {
        'question': 'Que fait le spread operator (...) dans un tableau ?',
        'options': [
            'Supprime des éléments',
            'Étend les éléments d\'un itérable',
            'Trie le tableau',
            'Inverse le tableau',
        ],
        'reponse': 1,
        'niveau': 'avance',
    },
    {
        'question': 'Qu\'est-ce que la closure en JavaScript ?',
        'options': [
            'Une fonction qui a accès à son scope parent même après la fin de celui-ci',
            'Une fonction qui se ferme automatiquement',
            'Une méthode de tableau',
            'Un mot-clé réservé',
        ],
        'reponse': 0,
        'niveau': 'avance',
    },
]


@login_required
@student_required
def niveau_test(request):

    index = request.session.get('niveau_test_index', 0)
    score = request.session.get('niveau_test_score', 0)
    total = len(QUESTIONS_NIVEAU)

    if request.method == 'POST':
        reponse = request.POST.get('reponse')
        if reponse is not None:
            try:
                idx = int(reponse)
                q = QUESTIONS_NIVEAU[index]
                if idx == q['reponse']:
                    score += 1
                request.session['niveau_test_score'] = score
            except (ValueError, IndexError):
                pass
        request.session['niveau_test_index'] = index + 1
        if index + 1 >= total:
            pct = (score / total) * 100
            if score == total:
                niveau = 'avance'
            elif pct >= 60:
                niveau = 'intermediaire'
            else:
                niveau = 'debutant'

            profil = Profil.objects(user_id=request.user.id).first()
            if profil:
                profil.niveau = niveau
                profil.niveau_tested = True
                profil.save()
                messages.success(
                    request,
                    f"Test terminé ! Niveau déterminé : <strong>{dict(Profil.niveau_choices).get(niveau, niveau)}</strong> "
                    f"({score}/{total})"
                )
            return redirect('dashboard')

    if index >= total:
        request.session.pop('niveau_test_index', None)
        request.session.pop('niveau_test_score', None)
        return redirect('dashboard')

    question = QUESTIONS_NIVEAU[index]
    progression_pct = int((index / total) * 100) if total else 0

    profil = Profil.objects(user_id=request.user.id).first()
    return render(request, 'core/niveau_test.html', {
        'question': question,
        'question_num': index + 1,
        'total_questions': total,
        'progression_pct': progression_pct,
        'profil': profil,
    })


@login_required
@student_required
def dashboard(request):
    uid = request.user.id
    _annuler_examen(request, uid)
    profil = Profil.objects(user_id=uid).first()
    if not profil:
        profil = Profil.objects(user_id=uid, username=request.user.username).save()
    if profil.role == 'student' and profil.status == 'pending':
        return render(request, 'core/approval_pending.html')

    formations_all = Formation.objects().order_by('ordre')

    # Récupérer toutes les progressions en une seule requête
    all_progressions = Progression.objects(user_id=uid)
    progression_map = {}
    for p in all_progressions:
        if p.cours:
            progression_map[str(p.cours.id)] = p

    total_cours = 0
    cours_termines = 0
    roadmap = []

    for f in formations_all:
        prof_profil = Profil.objects(specialite__iexact=f.nom, role='professor').first()
        prof_id = prof_profil.user_id if prof_profil else f.professor_id
        if prof_id:
            cours_list_f = Cours.objects(category=f.nom, professor_id=prof_id).order_by('ordre')
        else:
            cours_list_f = Cours.objects(category=f.nom, professor_id__ne=0).order_by('ordre')

        for c in cours_list_f:
            total_cours += 1
            prog = progression_map.get(str(c.id))
            if prog and prog.pourcentage == 100:
                cours_termines += 1

        # Roadmap dynamique : premiers cours de la formation
        for idx, c in enumerate(cours_list_f[:7]):
            statut = ''
            prog = progression_map.get(str(c.id))
            if prog and prog.pourcentage == 100:
                statut = 'done'
            elif prog and prog.pourcentage and prog.pourcentage > 0:
                statut = 'current' if not any(r.get('statut') == 'current' for r in roadmap) else ''
            else:
                statut = ''
            if not statut and idx == 0:
                statut = 'current'
            roadmap.append({'titre': c.titre, 'statut': statut, 'formation': f.nom})

    exercices_reussis = Resolution.objects(user_id=uid, resolu=True).count()
    total_exercices = Exercice.objects.count()
    activites = Activite.objects(user_id=uid).order_by('-date')[:5]

    all_activites = Activite.objects(user_id=uid).order_by('-date')
    active_dates = set()
    for a in all_activites:
        active_dates.add(a.date.date() if hasattr(a.date, 'date') else a.date)
    today = date.today()
    streak = 0
    check = today
    while check in active_dates:
        streak += 1
        check -= timedelta(days=1)
    if streak == 0:
        check = today - timedelta(days=1)
        while check in active_dates:
            streak += 1
            check -= timedelta(days=1)
    profil.serie_jours = streak
    profil.save()

    formations_progress = []
    for f in formations_all:
        fp = FormationProgress.objects(user_id=uid, formation_nom=f.nom).first()
        formations_progress.append({
            'formation': f,
            'xp': fp.xp if fp else 0,
            'completed_exercises': fp.completed_exercises if fp else 0,
            'exam_passed': fp.exam_passed if fp else False,
        })

    return render(request, 'core/dashboard.html', {
        'profil': profil,
        'cours_termines': cours_termines,
        'exercices_reussis': exercices_reussis,
        'total_cours': total_cours,
        'serie_jours': streak,
        'activites_recentes': activites,
        'roadmap': roadmap,
        'formations_avec_examens': Formation.objects().count(),
        'niveaux_matieres': _obtenir_niveaux_dashboard(uid),
        'formations_progress': formations_progress,
    })


@login_required
@student_required
def cours_list(request):
    uid = request.user.id
    _annuler_examen(request, uid)
    formations = Formation.objects().order_by('ordre')

    formation_data = []
    for f in formations:
        prof_profil = Profil.objects(specialite__iexact=f.nom, role='professor').first()
        prof_id = prof_profil.user_id if prof_profil else f.professor_id
        if prof_id:
            cours_list = Cours.objects(category=f.nom, professor_id=prof_id)
        else:
            cours_list = Cours.objects(category=f.nom, professor_id__ne=0)
        total_cours = cours_list.count()
        total_lessons = Lesson.objects(cours__in=cours_list).count()
        total_exos = Exercice.objects(cours__in=cours_list).count()
        cours_termines = Progression.objects(user_id=uid, cours__in=cours_list, pourcentage=100).count()
        formation_data.append({
            'formation': f,
            'total_cours': total_cours,
            'total_lessons': total_lessons,
            'total_exos': total_exos,
            'test_ok': _verifier_test_matiere(uid, f.nom),
        })

    return render(request, 'core/cours_list.html', {
        'formations': formation_data,
        'total_formations': Formation.objects.count(),
    })


@login_required
@student_required
def formation_detail(request, slug):
    uid = request.user.id
    _annuler_examen(request, uid)
    profil = Profil.objects(user_id=uid).first()
    formation = Formation.objects.get(slug=slug)

    if not _verifier_test_matiere(uid, formation.nom):
        messages.warning(request, f"🔒 Tu dois d'abord passer le test de niveau {formation.nom}.")
        return redirect('test_niveau_matiere', slug=slug)

    prof_profil = Profil.objects(specialite__iexact=formation.nom, role='professor').first()
    prof_id = prof_profil.user_id if prof_profil else formation.professor_id
    if prof_id:
        cours_list = Cours.objects(category=formation.nom, professor_id=prof_id).order_by('ordre')
    else:
        cours_list = Cours.objects(category=formation.nom, professor_id__ne=0).order_by('ordre')

    prof = None
    if prof_profil:
        user_prof = User.objects.filter(id=prof_profil.user_id).first()
        if user_prof:
            prof = prof_profil.fullname or user_prof.username
    if not prof and formation.professor_id:
        user_prof = User.objects.filter(id=formation.professor_id).first()
        if user_prof:
            prof_obj = Profil.objects(user_id=formation.professor_id).first()
            prof = prof_obj.fullname or user_prof.username if prof_obj else user_prof.username

    cours_data = []
    total_cours = cours_list.count()
    fp = FormationProgress.objects(user_id=uid, formation_nom=formation.nom).first()
    xp_total = fp.xp if fp else 0
    for c in cours_list:
        lessons = Lesson.objects(cours=c)
        exos_cours = Exercice.objects(cours=c)
        cours_data.append({
            'cours': c,
            'lesson_count': lessons.count(),
            'exercise_count': exos_cours.count(),
        })

    niveaux = ['debutant', 'intermediaire', 'avance']
    niveaux_labels = {'debutant': 'Débutant', 'intermediaire': 'Intermédiaire', 'avance': 'Avancé'}
    grouped = {}
    for n in niveaux:
        items = [cd for cd in cours_data if cd['cours'].niveau == n]
        if items:
            grouped[niveaux_labels[n]] = items

    return render(request, 'core/cours_detail.html', {
        'formation': formation,
        'professeur': prof or 'CodeMentor',
        'grouped_cours': grouped,
        'total_cours': total_cours,
        'xp_total': xp_total,
    })


def exercises_list_redirect(request):
    return redirect('cours_list')


@login_required
@student_required
def cours_detail(request, slug):
    uid = request.user.id
    cours = Cours.objects.get(slug=slug)
    progression = Progression.objects(user_id=uid, cours=cours).first()
    if not progression:
        progression = Progression(user_id=uid, cours=cours).save()

    lessons = Lesson.objects(cours=cours).order_by('ordre')
    chapters = []
    seen = set()
    for l in lessons:
        ch = l.chapitre or 'Général'
        if ch not in seen:
            seen.add(ch)
            chapters.append(ch)

    lesson_groups = []
    for ch in chapters:
        ch_lessons = [l for l in lessons if (l.chapitre or 'Général') == ch]
        lesson_groups.append({'chapitre': ch, 'lessons': ch_lessons})

    return render(request, 'core/cours_detail.html', {
        'cours': cours,
        'progression': progression,
        'lesson_groups': lesson_groups,
        'chapters': chapters,
    })


@login_required
@student_required
def lecon_detail(request, slug):
    import markdown as md_lib
    uid = request.user.id
    _annuler_examen(request, uid)
    formation = Formation.objects.get(slug=slug)

    if not _verifier_test_matiere(uid, formation.nom):
        messages.warning(request, f"🔒 Tu dois d'abord passer le test de niveau {formation.nom}.")
        return redirect('test_niveau_matiere', slug=slug)

    cours_slug = request.GET.get('module')
    if cours_slug:
        cours = Cours.objects.get(slug=cours_slug)
    else:
        cours_list = Cours.objects(category=formation.nom).order_by('ordre')
        if not cours_list:
            messages.error(request, "Aucun module disponible.")
            return redirect('cours_detail', slug=slug)
        cours = cours_list.first()
    lecon_ordre = int(request.GET.get('lecon', 1))
    lessons = Lesson.objects(cours=cours).order_by('ordre')
    if not lessons:
        messages.error(request, "Aucune leçon disponible.")
        return redirect('cours_detail', slug=formation.slug)
    lesson = lessons.filter(ordre=lecon_ordre).first()
    if not lesson:
        lesson = lessons.first()
        lecon_ordre = lesson.ordre

    content_html = bleach.clean(md_lib.markdown(lesson.content, extensions=['fenced_code', 'codehilite', 'tables']), tags=['p', 'br', 'strong', 'em', 'b', 'i', 'u', 'a', 'pre', 'code', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'blockquote', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'img', 'span', 'div', 'figure', 'figcaption'], attributes={'a': ['href', 'title', 'target', 'rel'], 'img': ['src', 'alt', 'title', 'class'], 'code': ['class'], 'span': ['class'], 'div': ['class'], 'td': ['style'], 'th': ['style']}) if lesson.content else ''

    prev_lesson = lessons.filter(ordre=lecon_ordre - 1).first() if lecon_ordre > 1 else None
    next_lesson = lessons.filter(ordre=lecon_ordre + 1).first()

    progression = Progression.objects(user_id=uid, cours=cours).first()
    if not progression:
        progression = Progression(user_id=uid, cours=cours).save()

    if lecon_ordre not in progression.lecons_accessed:
        progression.lecons_accessed.append(lecon_ordre)
        progression.save()

    total_lessons = lessons.count()
    progress_pct = int((lecon_ordre / max(total_lessons, 1)) * 100)

    exercises = list(Exercice.objects(Q(lesson=lesson) | Q(cours=cours, lesson_nom=lesson.titre)))
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f'lecon_detail: lesson="{lesson.titre}" (id={lesson.id}), cours="{cours.titre}", found {len(exercises)} exercises')
    for e in exercises:
        logger.debug(f'  - "{e.titre}" (lesson={e.lesson.titre if e.lesson else "None"}, lesson_nom="{e.lesson_nom}")')
    resolutions = Resolution.objects(user_id=uid, exercice__in=[e.id for e in exercises])
    resolu_map = {str(r.exercice.id): r.resolu for r in resolutions}
    for e in exercises:
        e.resolu = resolu_map.get(str(e.id), False)
    all_completed = exercises and all(e.resolu for e in exercises)
    remaining = sum(1 for e in exercises if not e.resolu)

    if request.GET.get('termine') == '1' and not next_lesson:
        progression.pourcentage = 100
        progression.save()
        Activite(user_id=uid, type='cours', description=f"Cours terminé : {cours.titre}").save()
        messages.success(request, f"Félicitations ! Tu as terminé le cours {cours.titre} !")
        return redirect('cours_detail', slug=formation.slug)

    return render(request, 'core/lecon_detail.html', {
        'cours': cours,
        'formation': formation,
        'lesson': lesson,
        'content_html': content_html,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'progression': progression,
        'progress_pct': progress_pct,
        'total_lessons': total_lessons,
        'lecon_ordre': lecon_ordre,
        'exercises': exercises,
        'all_completed': all_completed,
        'remaining': remaining,
    })


@login_required
@student_required
def lecon_exercices(request, slug):
    uid = request.user.id
    _annuler_examen(request, uid)
    formation = Formation.objects.get(slug=slug)

    if not _verifier_test_matiere(uid, formation.nom):
        messages.warning(request, f"🔒 Tu dois d'abord passer le test de niveau {formation.nom}.")
        return redirect('test_niveau_matiere', slug=slug)

    cours_slug = request.GET.get('module')
    if not cours_slug:
        messages.error(request, "Module manquant.")
        return redirect('cours_detail', slug=slug)
    cours = Cours.objects.get(slug=cours_slug)
    lecon_ordre = int(request.GET.get('lecon', 1))
    lesson = Lesson.objects(cours=cours, ordre=lecon_ordre).first()
    if not lesson:
        messages.error(request, "Leçon introuvable.")
        return redirect('cours_detail', slug=slug)

    progression = Progression.objects(user_id=uid, cours=cours).first()
    if not progression or lecon_ordre not in progression.lecons_accessed:
        messages.warning(request, "Tu dois d'abord ouvrir la leçon.")
        return redirect(f"{reverse('lecon_detail', kwargs={'slug': slug})}?module={cours.slug}&lecon={lecon_ordre}")

    exercises = list(Exercice.objects(Q(lesson=lesson) | Q(cours=cours, lesson_nom=lesson.titre)))
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f'lecon_exercices: lesson="{lesson.titre}" (id={lesson.id}), cours="{cours.titre}", found {len(exercises)} exercises')
    for e in exercises:
        logger.debug(f'  - "{e.titre}" (lesson={e.lesson.titre if e.lesson else "None"}, lesson_nom="{e.lesson_nom}")')
    resolutions = Resolution.objects(user_id=uid, exercice__in=[e.id for e in exercises])
    resolu_map = {str(r.exercice.id): r.resolu for r in resolutions}
    for e in exercises:
        e.resolu = resolu_map.get(str(e.id), False)
    all_completed = exercises and all(e.resolu for e in exercises)
    remaining = sum(1 for e in exercises if not e.resolu)

    next_lesson = Lesson.objects(cours=cours, ordre=lecon_ordre + 1).first()

    if not exercises:
        messages.info(request, "Aucun exercice pour cette leçon.")
        return redirect(f"{reverse('lecon_detail', kwargs={'slug': slug})}?module={cours.slug}&lecon={lecon_ordre}")

    return render(request, 'core/lecon_exercices.html', {
        'formation': formation,
        'cours': cours,
        'lesson': lesson,
        'exercises': exercises,
        'all_completed': all_completed,
        'remaining': remaining,
        'next_lesson': next_lesson,
    })


def _exercice_suivant(exercice):
    """Trouve le prochain exercice dans la même formation."""
    if not exercice.cours:
        return None
    cours_list = Cours.objects(category=exercice.cours.category, professor_id__ne=0)
    exos = list(Exercice.objects(cours__in=cours_list))
    ordre_diff = {'facile': 0, 'moyen': 1, 'difficile': 2}
    exos.sort(key=lambda e: (ordre_diff.get(e.difficulte, 9), e.titre))
    for i, e in enumerate(exos):
        if str(e.id) == str(exercice.id):
            if i + 1 < len(exos):
                return exos[i + 1]
    return None


def _verifier_test_matiere(uid, formation_nom):
    nm = NiveauMatiere.objects(user_id=uid, formation_nom=formation_nom).first()
    return nm and nm.test_complete


def _obtenir_niveau_label(niveau):
    mapping = {'debutant': 'Débutant', 'intermediaire': 'Intermédiaire', 'avance': 'Avancé'}
    return mapping.get(niveau, niveau)


def _obtenir_niveaux_dashboard(uid):
    niveaux = []
    formations = Formation.objects().order_by('ordre')
    formation_names = [f.nom for f in formations]
    nm_map = {}
    for nm in NiveauMatiere.objects(user_id=uid, formation_nom__in=formation_names):
        nm_map[nm.formation_nom] = nm
    for f in formations:
        nm = nm_map.get(f.nom)
        niveaux.append({
            'nom': f.nom,
            'emoji': f.emoji,
            'niveau': nm.niveau if nm and nm.test_complete else 'non_evalue',
            'test_complete': nm.test_complete if nm else False,
        })
    return niveaux


def _annuler_examen(request, uid):
    """Annule un examen en cours si l'etudiant quitte le parcours (per-formation)."""
    attempt = ExamAttempt.objects(user_id=uid, is_finished=False).first()
    penalise = False
    score_examen = 0

    if attempt:
        penalise = True
        score_examen = 0
        type_echec = 'abandon'
        f_nom = attempt.formation_nom or ''
        message = (
            f"Vous avez quitte le parcours d'examen{' ' + f_nom if f_nom else ''}. "
            "100 XP ont ete retires. "
            f"Les exercices{' ' + f_nom if f_nom else ''} ont ete reinitialises. "
            "Vous devez recommencer le parcours avant de repasser l'examen."
        )
    else:
        attempt = ExamAttempt.objects(user_id=uid, is_finished=True, penalty_applied=False).first()
        if attempt:
            penalise = True
            pct = int((attempt.score / max(attempt.total_questions, 1)) * 100)
            score_examen = pct
            f_nom = attempt.formation_nom or ''
            type_echec = 'note_insuffisante'
            message = (
                f"Examen{' ' + f_nom if f_nom else ''} echoue ({pct}%). "
                "100 XP ont ete retires. "
                f"Les exercices{' ' + f_nom if f_nom else ''} ont ete reinitialises. "
                "Vous devez recommencer le parcours avant de repasser l'examen."
            )

    if not penalise:
        return False

    old_scores = list(ScoreExercice.objects(user_id=uid))
    nb_exercices = len(old_scores)

    fp = FormationProgress.objects(user_id=uid, formation_nom=f_nom).first() if f_nom else None
    if fp:
        fp.xp = max(0, fp.xp - 100)
        fp.completed_exercises = 0
        fp.exam_passed = False
        fp.save()

    for s in old_scores:
        s.delete()

    for r in Resolution.objects(user_id=uid):
        r.resolu = False
        r.save()

    for p in Progression.objects(user_id=uid):
        p.pourcentage = 0
        p.save()

    acces_list = AccesExamen.objects(user_id=uid)
    for acces in acces_list:
        acces.debloque = False
        acces.examen_passe = False
        acces.examen_reussi = False
        acces.score_global = float(fp.xp if fp else 0)
        acces.save()

    attempt.is_finished = True
    attempt.end_time = datetime.now()
    attempt.penalty_applied = True
    attempt.save()

    ExamHistory(
        user_id=uid,
        score_examen=float(score_examen),
        reussi=False,
        penalite_xp=100,
        exercices_reinitialises=nb_exercices,
        type_echec=type_echec,
    ).save()

    if type_echec == 'abandon':
        messages.warning(request, message)
    else:
        messages.error(request, message)
    return True


@login_required
@student_required
def exercice_detail(request, pk):
    uid = request.user.id
    exercice = Exercice.objects.get(id=pk)

    formation_nom = None
    formation = None
    cours = None
    lesson = None
    next_lesson_url = None
    back_to_exercices_url = None

    if exercice.cours:
        cours = exercice.cours
        formation_nom = cours.category
        formation = Formation.objects(slug__iexact=formation_nom).first()

        if not _verifier_test_matiere(uid, formation_nom):
            messages.warning(request, f"🔒 Tu dois d'abord passer le test de niveau {formation_nom}.")
            if formation:
                return redirect('test_niveau_matiere', slug=formation.slug)
            return redirect('cours_list')

        if exercice.lesson:
            lesson = exercice.lesson
            progression = Progression.objects(user_id=uid, cours=cours).first()
            lecon_ordre = lesson.ordre if lesson else 0
            if not progression or lecon_ordre not in progression.lecons_accessed:
                messages.warning(request, "Tu dois d'abord ouvrir la lecon avant de faire l'exercice.")
                if formation:
                    url = reverse('lecon_detail', kwargs={'slug': formation.slug}) + f'?module={cours.slug}&lecon={lecon_ordre}'
                    return redirect(url)
                return redirect('cours_list')

            next_lesson = Lesson.objects(cours=cours, ordre=lecon_ordre + 1).first() if lesson else None
            if next_lesson and formation:
                next_lesson_url = f"{reverse('lecon_detail', kwargs={'slug': formation.slug})}?module={cours.slug}&lecon={next_lesson.ordre}"
            if formation:
                back_to_exercices_url = f"{reverse('lecon_exercices', kwargs={'slug': formation.slug})}?module={cours.slug}&lecon={lecon_ordre}"
        elif exercice.lesson_nom:
            lesson = Lesson.objects(cours=cours, titre=exercice.lesson_nom).first()
            progression = Progression.objects(user_id=uid, cours=cours).first()
            lecon_ordre = lesson.ordre if lesson else 0
            if not progression or lecon_ordre not in progression.lecons_accessed:
                messages.warning(request, "Tu dois d'abord ouvrir la lecon avant de faire l'exercice.")
                if formation:
                    url = reverse('lecon_detail', kwargs={'slug': formation.slug}) + f'?module={cours.slug}&lecon={lecon_ordre}'
                    return redirect(url)
                return redirect('cours_list')

            next_lesson = Lesson.objects(cours=cours, ordre=lecon_ordre + 1).first() if lesson else None
            if next_lesson and formation:
                next_lesson_url = f"{reverse('lecon_detail', kwargs={'slug': formation.slug})}?module={cours.slug}&lecon={next_lesson.ordre}"
            if formation:
                back_to_exercices_url = f"{reverse('lecon_exercices', kwargs={'slug': formation.slug})}?module={cours.slug}&lecon={lecon_ordre}"

    resolution = Resolution.objects(user_id=uid, exercice=exercice).first()
    if not resolution:
        resolution = Resolution(user_id=uid, exercice=exercice).save()

    erreur = None

    if request.method == 'POST':
        reponse = request.POST.get('reponse', '').strip()
        if not reponse:
            erreur = "Veuillez écrire une réponse."
        else:
            correct = False
            if exercice.correction and exercice.correction.strip():
                reponse_norm = reponse.lower().strip()
                correction_norm = exercice.correction.lower().strip()
                correct = (reponse_norm == correction_norm)
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"User answer: {reponse_norm}")
                logger.debug(f"Correct answer: {correction_norm}")
                logger.debug(f"Is correct: {correct}")
                if not correct:
                    erreur = "Réponse incorrecte. Réessaie encore."
            else:
                erreur = "Votre réponse a été enregistrée, mais cet exercice n'a pas de correction automatique."

            if correct:
                resolution.resolu = True
                resolution.save()

                score_obj, acces, score_global, formation_nom = enregistrer_score(uid, exercice, exercice.points)

                Activite(
                    user_id=uid,
                    type='exercice',
                    description=f"Exercice reussi : {exercice.titre}",
                ).save()

                nb_exercices_faits = ScoreExercice.objects(user_id=uid).count()
                total_xp_reel = FormationProgress.objects(user_id=uid, formation_nom=formation_nom).first()
                xp_val = total_xp_reel.xp if total_xp_reel else 0

                return render(request, 'core/resultat_exercice.html', {
                    'exercice': exercice,
                    'correct': True,
                    'score_obtenu': exercice.points,
                    'score_global': xp_val,
                    'acces_examen': acces,
                    'nb_exercices_faits': nb_exercices_faits,
                    'next_lesson_url': next_lesson_url,
                    'back_to_exercices_url': back_to_exercices_url,
                    'formation': formation,
                    'cours': cours,
                    'lesson': lesson,
                    'formation_nom': formation_nom,
                })

    return render(request, 'core/exercice_detail.html', {
        'exercice': exercice,
        'resolution': resolution,
        'erreur': erreur,
        'formation': formation,
        'cours': cours,
        'lesson': lesson,
        'next_lesson_url': next_lesson_url,
    })


@login_required
@student_required
def diagnostic(request):
    uid = request.user.id
    session = SessionDiagnostic.objects(user_id=uid, terminee=False).first()
    created = False
    if not session:
        session = SessionDiagnostic(
            user_id=uid,
            total=QuestionDiagnostic.objects.count()
        ).save()
        created = True

    questions = list(QuestionDiagnostic.objects())
    if created:
        random.shuffle(questions)
        request.session['diagnostic_order'] = [str(q.id) for q in questions]

    if not created:
        order = request.session.get('diagnostic_order', [str(q.id) for q in questions])
        ordered = {str(q.id): q for q in questions}
        questions = [ordered[oid] for oid in order if oid in ordered]

    total = len(questions)

    if session.terminee or session.question_index >= total:
        return render(request, 'core/diagnostic_resultat.html', {
            'score': session.score,
            'total': session.total,
        })

    question = questions[session.question_index]

    if request.method == 'POST':
        option_idx = request.POST.get('reponse')
        if option_idx is not None and question.options:
            try:
                idx = int(option_idx)
                if 0 <= idx < len(question.options) and question.options[idx].est_correcte:
                    session.score += 1
            except (ValueError, IndexError):
                pass
            session.question_index += 1
            session.total += 1
            session.save()
        return redirect('diagnostic')

    return render(request, 'core/diagnostic.html', {
        'question': question,
        'question_num': session.question_index + 1,
        'total_questions': total,
        'progression_pct': int((session.question_index / total) * 100) if total else 0,
    })


@login_required
@student_required
def tuteur(request):
    uid = request.user.id
    _annuler_examen(request, uid)
    historique = MessageChat.objects(user_id=uid).order_by('date')[:50]
    sujet = None
    formation_nom = None
    niveau = None
    progressions = Progression.objects(user_id=uid, pourcentage__gt=0)
    if progressions.count() > 0:
        dernier = progressions.order_by('-pourcentage').first()
        sujet = dernier.cours.titre
        formation_nom = dernier.cours.category
        nm = NiveauMatiere.objects(user_id=uid, formation_nom=formation_nom).first()
        if nm:
            niveau = nm.niveau

    formations = Formation.objects().order_by('ordre')

    for msg in historique:
        if msg.role == 'ai':
            msg.contenu_html = bleach.clean(markdown.markdown(msg.contenu, extensions=['fenced_code', 'codehilite']), tags=['p', 'br', 'strong', 'em', 'b', 'i', 'u', 'a', 'pre', 'code', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'blockquote', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'img', 'span', 'div', 'figure', 'figcaption'], attributes={'a': ['href', 'title', 'target', 'rel'], 'img': ['src', 'alt', 'title', 'class'], 'code': ['class'], 'span': ['class'], 'div': ['class'], 'td': ['style'], 'th': ['style']})

    return render(request, 'core/tuteur.html', {
        'historique': historique,
        'sujet_actuel': sujet,
        'formation_nom': formation_nom,
        'niveau': niveau,
        'formations': formations,
    })


@login_required
@student_required
def tuteur_message(request):
    if request.method == 'POST':
        uid = request.user.id
        contenu = request.POST.get('message', '').strip()
        if contenu:
            # Récupérer le contexte
            formation_nom = None
            niveau = None
            lecon_actuelle = None
            lecons_terminees = None
            prog = Progression.objects(user_id=uid, pourcentage__gt=0).order_by('-pourcentage').first()
            if prog and prog.cours:
                formation_nom = prog.cours.category
            nm = NiveauMatiere.objects(user_id=uid, formation_nom=formation_nom).first() if formation_nom else None
            if nm:
                niveau = nm.niveau
            # Leçons terminées : toutes celles où l'étudiant a des résolutions réussies
            resolu_ids = set()
            from .models import Resolution
            for r in Resolution.objects(user_id=uid, resolu=True):
                if r.exercice and r.exercice.lesson:
                    resolu_ids.add(str(r.exercice.lesson.id))
            lecons_terminees = list(resolu_ids) if resolu_ids else None

            MessageChat(user_id=uid, role='user', contenu=contenu).save()
            reponse_ia = generer_reponse(uid, contenu,
                                          formation_nom=formation_nom,
                                          lecon_actuelle=lecon_actuelle,
                                          niveau_etudiant=niveau,
                                          lecons_terminees=lecons_terminees)
            MessageChat(user_id=uid, role='ai', contenu=reponse_ia).save()
    return redirect('tuteur')


@login_required
@student_required
def test_niveau_matiere(request, slug):
    uid = request.user.id
    formation = Formation.objects(slug=slug).first()
    if not formation:
        messages.error(request, "Formation introuvable.")
        return redirect('cours_list')

    nm = NiveauMatiere.objects(user_id=uid, formation_nom=formation.nom).first()
    if nm and nm.test_complete:
        messages.info(request, f"✅ Test {formation.nom} déjà complété. Niveau : {_obtenir_niveau_label(nm.niveau)}")
        return redirect('formation_detail', slug=slug)

    if request.method == 'POST':
        nm = NiveauMatiere.objects(user_id=uid, formation_nom=formation.nom).first()
        questions = list(QuestionNiveau.objects(formation_nom=formation.nom))
        random.shuffle(questions)
        questions = questions[:10]
        total = len(questions)
        bonnes = 0
        for q in questions:
            val = request.POST.get(f'q_{q.id}')
            if val is not None and val.isdigit():
                if int(val) == q.reponse_correcte:
                    bonnes += 1

        pct = int((bonnes / max(total, 1)) * 100)
        if pct <= 40:
            niveau = 'debutant'
        elif pct <= 70:
            niveau = 'intermediaire'
        else:
            niveau = 'avance'

        if nm:
            nm.niveau = niveau
            nm.score = bonnes
            nm.total = total
            nm.test_complete = True
            nm.completed_at = datetime.now()
            nm.save()
        else:
            NiveauMatiere(
                user_id=uid,
                formation_nom=formation.nom,
                niveau=niveau,
                score=bonnes,
                total=total,
                test_complete=True,
                completed_at=datetime.now(),
            ).save()

        messages.success(request,
            f"✅ Test {formation.nom} terminé ! Score : {bonnes}/{total} ({pct}%). "
            f"Niveau : {_obtenir_niveau_label(niveau)}"
        )
        return redirect('formation_detail', slug=slug)

    questions = list(QuestionNiveau.objects(formation_nom=formation.nom))
    random.shuffle(questions)
    questions = questions[:10]

    return render(request, 'core/test_niveau_matiere.html', {
        'formation': formation,
        'questions': questions,
    })


@login_required
@student_required
def examens_list(request):
    uid = request.user.id
    formations = Formation.objects().order_by('ordre')
    examens = []
    for f in formations:
        cours_list = Cours.objects(category__iexact=f.nom, professor_id__ne=0)
        exos = Exercice.objects(cours__in=cours_list)
        exo_ids = [e.id for e in exos]
        nb_exos_total = len(exo_ids)
        nb_exos_faits = Resolution.objects(user_id=uid, exercice__in=exo_ids, resolu=True).count()
        resolutions = Resolution.objects(user_id=uid, exercice__in=exo_ids)
        resolu_map = {str(r.exercice.id): r.resolu for r in resolutions}
        nb_exos_faits = sum(1 for e in exos if resolu_map.get(str(e.id), False))

        acces = AccesExamen.objects(user_id=uid, formation_nom=f.nom).first()
        debloque = nb_exos_faits >= 8
        examen_passe = acces.examen_passe if acces else False
        examen_reussi = acces.examen_reussi if acces else False
        score_examen = acces.score_examen if acces else 0

        examens.append({
            'nom': f.nom,
            'slug': f.slug,
            'emoji': f.emoji,
            'description': f.description,
            'nb_cours': cours_list.count(),
            'exos_total': nb_exos_total,
            'exos_faits': nb_exos_faits,
            'debloque': debloque,
            'examen_passe': examen_passe,
            'examen_reussi': examen_reussi,
            'score_examen': score_examen,
        })

    return render(request, 'core/examens_list.html', {'examens': examens})


@login_required
@student_required
def examen_final(request):
    uid = request.user.id
    formation_slug = request.GET.get('formation', '')

    if not formation_slug:
        return redirect('examens_list')

    formation = Formation.objects(slug=formation_slug).first()
    if not formation:
        messages.error(request, "Formation introuvable.")
        return redirect('examens_list')

    if not _verifier_test_matiere(uid, formation.nom):
        messages.warning(request, f"🔒 Tu dois d'abord passer le test de niveau {formation.nom}.")
        return redirect('test_niveau_matiere', slug=formation_slug)

    f_nom = formation.nom
    cours_f = Cours.objects(category__iexact=f_nom, professor_id__ne=0)
    exos = Exercice.objects(cours__in=cours_f)
    exo_ids = [e.id for e in exos]

    resolutions = Resolution.objects(user_id=uid, exercice__in=exo_ids)
    resolu_map = {str(r.exercice.id): r.resolu for r in resolutions}
    nb_exercices_faits_f = sum(1 for e in exos if resolu_map.get(str(e.id), False))

    profil = Profil.objects(user_id=uid).first()
    fp = FormationProgress.objects(user_id=uid, formation_nom=f_nom).first()
    total_xp = fp.xp if fp else 0
    eligible = nb_exercices_faits_f >= 8
    reste_exercices = max(0, 8 - nb_exercices_faits_f)

    acces = AccesExamen.objects(user_id=uid, formation_nom=f_nom).first()
    if not acces:
        acces = AccesExamen(user_id=uid, formation_nom=f_nom).save()

    if eligible and not acces.debloque:
        acces.debloque = True
        acces.date_deblocage = datetime.now()
        acces.score_global = float(total_xp)
        acces.save()
    elif not eligible:
        acces.score_global = float(total_xp)
        acces.save()

    if acces.examen_passe:
        return render(request, 'core/examen_resultat.html', {'acces': acces, 'formation': formation})

    demarrer = request.GET.get('start') == '1'

    if demarrer and not eligible:
        messages.warning(request, f"Vous n'êtes pas encore éligible à l'examen {f_nom}. Complétez 8 exercices.")
        return redirect(f'{reverse("examen_final")}?formation={formation_slug}')

    if demarrer and eligible and request.method == 'POST':
        now = datetime.now()
        attempt = ExamAttempt.objects(user_id=uid, formation_nom=f_nom, is_finished=False).first()

        if attempt:
            elapsed = (now - attempt.start_time).total_seconds()
            timeout = elapsed > attempt.duration_minutes * 60

            reponses_str = request.POST.get('reponses', '')
            reponses_list = reponses_str.split(',') if reponses_str else []
            qids = attempt.reponses.split(',') if attempt.reponses else []
            questions_ordered = []
            for qid in qids:
                q = QuestionExamen.objects(id=qid).first()
                if q:
                    questions_ordered.append(q)
            total_q = len(questions_ordered)
            bonnes = 0
            for i, q in enumerate(questions_ordered):
                if i < len(reponses_list) and reponses_list[i].isdigit():
                    choix = int(reponses_list[i])
                    if choix == q.reponse_correcte:
                        bonnes += 1

            if timeout and not attempt.penalty_applied:
                if fp:
                    fp.xp = max(0, fp.xp - 50)
                    fp.save()
                attempt.penalty_applied = True
                messages.warning(request, f"⚠ Temps dépassé. 50 points ont été retirés de votre score.")

            pct = int((bonnes / max(total_q, 1)) * 100)
            attempt.is_finished = True
            attempt.end_time = now
            attempt.score = bonnes
            attempt.total_questions = total_q
            attempt.reponses = reponses_str
            attempt.save()

            reussi = pct >= 60

            if reussi:
                acces.examen_passe = True
                acces.examen_reussi = True
                acces.score_examen = float(pct)
                acces.date_examen = now
                acces.save()
                fp = FormationProgress.objects(user_id=uid, formation_nom=f_nom).first()
                if fp:
                    fp.xp += 100
                    fp.exam_passed = True
                    fp.save()
                return redirect(f'{reverse("examen_reussi", kwargs={"slug": formation_slug})}')
            else:
                acces.examen_passe = True
                acces.examen_reussi = False
                acces.score_examen = float(pct)
                acces.date_examen = now
                acces.save()

                if not timeout:
                    attempt.penalty_applied = False
                attempt.save()

                messages.error(request,
                    f"❌ Examen {f_nom} échoué ({pct}%). "
                    f"Les exercices {f_nom} et règles de l'examen seront réinitialisés "
                    f"lorsque vous quitterez cette page."
                )
        return redirect(f'{reverse("examen_final")}?formation={formation_slug}')

    if demarrer and eligible:
        existing = ExamAttempt.objects(user_id=uid, formation_nom=f_nom, is_finished=False).first()
        if existing:
            elapsed = (datetime.now() - existing.start_time).total_seconds()
            if elapsed > existing.duration_minutes * 60:
                existing.is_finished = True
                existing.save()
            else:
                attempt = existing

        if not existing or existing.is_finished:
            questions_deb = list(QuestionExamen.objects(formation_nom=f_nom, difficulte='debutant'))
            questions_int = list(QuestionExamen.objects(formation_nom=f_nom, difficulte='intermediaire'))
            questions_avc = list(QuestionExamen.objects(formation_nom=f_nom, difficulte='avance'))
            random.shuffle(questions_deb)
            random.shuffle(questions_int)
            random.shuffle(questions_avc)
            selected = questions_deb[:5] + questions_int[:5] + questions_avc[:5]
            random.shuffle(selected)
            qids = [str(q.id) for q in selected]
            attempt = ExamAttempt(
                user_id=uid,
                formation_nom=f_nom,
                start_time=datetime.now(),
                duration_minutes=60,
                reponses=','.join(qids),
                total_questions=len(selected),
            ).save()

        questions_ids = attempt.reponses.split(',') if attempt.reponses else []
        questions = []
        for qid in questions_ids:
            q = QuestionExamen.objects(id=qid).first()
            if q:
                questions.append(q)

        elapsed = (datetime.now() - attempt.start_time).total_seconds()
        remaining = max(0, int(attempt.duration_minutes * 60 - elapsed))

        return render(request, 'core/examen_final.html', {
            'acces': acces,
            'eligible': eligible,
            'demarrer': True,
            'en_cours': True,
            'questions': questions,
            'attempt': attempt,
            'remaining_seconds': remaining,
            'nb_exercices_faits': nb_exercices_faits_f,
            'total_xp': total_xp,
            'formation': formation,
        })

    dernier_echec = ExamHistory.objects(user_id=uid, formation_nom=f_nom, reussi=False).order_by('-date').first()

    return render(request, 'core/examen_final.html', {
        'acces': acces,
        'eligible': eligible,
        'demarrer': demarrer,
        'nb_exercices_faits': nb_exercices_faits_f,
        'total_xp': total_xp,
        'reste_exercices': reste_exercices,
        'reste_xp': 0,
        'formation': formation,
        'dernier_echec': dernier_echec,
    })


@login_required
def contact_admin(request):
    uid = request.user.id
    profil = Profil.objects(user_id=uid).first()
    if not profil or profil.role not in ('student', 'professor'):
        messages.error(request, "Accès réservé aux étudiants et professeurs.")
        return redirect('dashboard')

    if request.method == 'POST':
        new_pw = request.POST.get('new_password', '').strip()
        confirm_pw = request.POST.get('confirm_password', '').strip()
        reason = request.POST.get('reason', '').strip()

        existing = PasswordChangeRequest.objects(user_id=uid, status='pending').first()
        if existing:
            messages.warning(request, "Tu as déjà une demande en attente.")
            return redirect('contact_admin')

        if not new_pw:
            messages.error(request, "Le nouveau mot de passe est requis.")
            return redirect('contact_admin')

        if len(new_pw) < 8:
            messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
            return redirect('contact_admin')

        if not any(c.isupper() for c in new_pw):
            messages.error(request, "Le mot de passe doit contenir au moins une majuscule.")
            return redirect('contact_admin')

        if not any(c.isdigit() for c in new_pw):
            messages.error(request, "Le mot de passe doit contenir au moins un chiffre.")
            return redirect('contact_admin')

        if new_pw != confirm_pw:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect('contact_admin')

        PasswordChangeRequest(
            user_id=uid,
            username=request.user.username,
            email=profil.email or request.user.email,
            role=profil.role,
            new_password=make_password(new_pw),
            reason=reason,
        ).save()

        messages.success(request, "✅ Demande envoyée à l'administrateur.")
        return redirect('dashboard')

    return render(request, 'core/contact_admin.html', {
        'profil': profil,
    })


@login_required
def profile_edit(request):
    uid = request.user.id
    profil = Profil.objects(user_id=uid).first()
    if not profil:
        messages.error(request, "Profil introuvable.")
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if not email:
            messages.error(request, "L'adresse email est requise.")
        elif User.objects.filter(email=email).exclude(id=uid).exists():
            messages.error(request, "Cette adresse email est déjà utilisée.")
        else:
            user = request.user
            user.email = email
            user.save()
            profil.email = email
            profil.save()
            messages.success(request, "✅ Email mis à jour.")
        return redirect('profile_edit')

    formations_progress = FormationProgress.objects(user_id=uid).order_by('-xp')
    total_xp = sum(fp.xp for fp in formations_progress)
    return render(request, 'core/profile_edit.html', {
        'profil': profil,
        'formations_progress': formations_progress,
        'total_xp': total_xp,
    })


@login_required
@student_required
def examen_reussi(request, slug):
    uid = request.user.id
    formation = Formation.objects(slug=slug).first()
    if not formation:
        messages.error(request, "Formation introuvable.")
        return redirect('examens_list')

    acces = AccesExamen.objects(user_id=uid, formation_nom=formation.nom).first()
    if not acces or not acces.examen_reussi:
        messages.warning(request, "Tu n'as pas encore réussi cet examen.")
        return redirect('examen_final', formation=slug)

    fp = FormationProgress.objects(user_id=uid, formation_nom=formation.nom).first()

    return render(request, 'core/examen_reussi.html', {
        'formation': formation,
        'acces': acces,
        'fp': fp,
        'score': int(acces.score_examen),
    })


@login_required
@student_required
def certificat(request, slug):
    uid = request.user.id
    formation = Formation.objects(slug=slug).first()
    if not formation:
        messages.error(request, "Formation introuvable.")
        return redirect('examens_list')

    acces = AccesExamen.objects(user_id=uid, formation_nom=formation.nom).first()
    if not acces or not acces.examen_reussi:
        messages.warning(request, "Tu n'as pas encore obtenu cette certification.")
        return redirect('examens_list')

    profil = Profil.objects(user_id=uid).first()
    fp = FormationProgress.objects(user_id=uid, formation_nom=formation.nom).first()

    return render(request, 'core/certificat.html', {
        'formation': formation,
        'acces': acces,
        'fp': fp,
        'profil': profil,
        'score': int(acces.score_examen),
    })

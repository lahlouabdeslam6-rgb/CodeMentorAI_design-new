import random
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from mongoengine import DoesNotExist, NotUniqueError
from .models import (Profil, Cours, Progression, Activite, Exercice,
                     Resolution, QuestionDiagnostic, SessionDiagnostic,
                     MessageChat)


def home(request):
    return render(request, 'core/home.html')


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email', '')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        errors = []
        if not username:
            errors.append("Le nom d'utilisateur est requis.")
        if User.objects.filter(username=username).exists():
            errors.append("Ce nom d'utilisateur est déjà pris.")
        if password1 != password2:
            errors.append("Les mots de passe ne correspondent pas.")
        if password1 and len(password1) < 3:
            errors.append("Le mot de passe doit contenir au moins 3 caractères.")

        if errors:
            return render(request, 'core/register.html', {
                'form': type('obj', (object,), {'errors': {'__all__': errors}})()
            })

        user = User.objects.create_user(username=username, email=email, password=password1)
        Profil(user_id=user.id, username=username).save()
        login(request, user)
        return redirect('home')

    return render(request, 'core/register.html', {'form': None})


@login_required
def dashboard(request):
    uid = request.user.id
    profil = Profil.objects(user_id=uid).first()
    if not profil:
        profil = Profil(user_id=uid, username=request.user.username).save()

    cours_list = Cours.objects()
    progressions = Progression.objects(user_id=uid)
    progression_map = {str(p.cours.id): p for p in progressions}

    progression_data = []
    for cours in cours_list:
        p = progression_map.get(str(cours.id))
        pourcentage = p.pourcentage if p else 0
        progression_data.append({'cours': cours, 'pourcentage': pourcentage})

    cours_termines = Progression.objects(user_id=uid, pourcentage=100).count()
    exercices_reussis = Resolution.objects(user_id=uid, resolu=True).count()
    activites = Activite.objects(user_id=uid).order_by('-date')[:5]

    roadmap = [
        {'titre': 'Introduction JavaScript', 'statut': 'done'},
        {'titre': 'Variables et types', 'statut': 'done'},
        {'titre': 'Fonctions', 'statut': 'current' if cours_termines >= 2 else 'done' if cours_termines >= 1 else 'done'},
        {'titre': 'Objets et tableaux', 'statut': 'current' if cours_termines == 2 else 'done' if cours_termines > 2 else ''},
        {'titre': 'DOM et événements', 'statut': 'current' if cours_termines == 3 else ''},
        {'titre': 'Asynchrone (Promises, async/await)', 'statut': ''},
        {'titre': 'Projet final', 'statut': ''},
    ]

    found_current = False
    for etape in roadmap:
        if etape['statut'] == 'current':
            found_current = True
        elif not found_current and etape['statut'] == '':
            etape['statut'] = 'current'
            found_current = True

    peut_passer_examen = cours_termines >= 3

    return render(request, 'core/dashboard.html', {
        'profil': profil,
        'cours_termines': cours_termines,
        'exercices_reussis': exercices_reussis,
        'serie_jours': profil.serie_jours,
        'progression': progression_data,
        'activites_recentes': activites,
        'roadmap': roadmap,
        'peut_passer_examen': peut_passer_examen,
    })


@login_required
def cours_list(request):
    uid = request.user.id
    niveau = request.GET.get('niveau')
    cours_qs = Cours.objects()
    if niveau:
        cours_qs = cours_qs.filter(niveau=niveau)

    progressions = Progression.objects(user_id=uid)
    prog_map = {str(p.cours.id): p.pourcentage for p in progressions}

    cours_data = []
    for cours in cours_qs:
        cours_data.append({
            'slug': cours.slug,
            'emoji': cours.emoji,
            'niveau': cours.niveau,
            'get_niveau_display': cours.get_niveau_display(),
            'titre': cours.titre,
            'description': cours.description,
            'progression_pct': prog_map.get(str(cours.id), 0),
        })

    exercices = Exercice.objects()
    resolutions = Resolution.objects(user_id=uid)
    resolu_map = {str(r.exercice.id): r.resolu for r in resolutions}

    exo_data = []
    for exo in exercices:
        exo_data.append({
            'id': str(exo.id),
            'resolu': resolu_map.get(str(exo.id), False),
            'difficulte': exo.difficulte,
            'titre': exo.titre,
            'get_difficulte_display': exo.get_difficulte_display(),
            'categorie': exo.categorie,
            'points': exo.points,
        })

    cours_termines = sum(1 for p in prog_map.values() if p == 100)
    exo_reussis = sum(1 for r in resolutions if r.resolu)

    return render(request, 'core/cours_list.html', {
        'cours_list': cours_data,
        'total_cours': Cours.objects.count(),
        'cours_termines': cours_termines,
        'niveau_actif': niveau,
        'exercices': exo_data,
        'total_exo': Exercice.objects.count(),
        'exo_reussis': exo_reussis,
    })


@login_required
def cours_detail(request, slug):
    uid = request.user.id
    cours = Cours.objects.get(slug=slug)
    progression = Progression.objects(user_id=uid, cours=cours).first()
    if not progression:
        progression = Progression(user_id=uid, cours=cours).save()

    exercices = Exercice.objects(cours=cours)
    resolutions = Resolution.objects(user_id=uid)
    resolu_map = {str(r.exercice.id): r.resolu for r in resolutions}

    exo_data = []
    for exo in exercices:
        exo_data.append({
            'id': str(exo.id),
            'resolu': resolu_map.get(str(exo.id), False),
            'difficulte': exo.difficulte,
            'titre': exo.titre,
            'get_difficulte_display': exo.get_difficulte_display(),
            'categorie': exo.categorie,
            'points': exo.points,
        })

    return render(request, 'core/cours_detail.html', {
        'cours': cours,
        'progression': progression,
        'exercices': exo_data,
    })


@login_required
def exercice_detail(request, pk):
    uid = request.user.id
    exercice = Exercice.objects.get(id=pk)
    resolution = Resolution.objects(user_id=uid, exercice=exercice).first()
    if not resolution:
        resolution = Resolution(user_id=uid, exercice=exercice).save()

    if request.method == 'POST':
        reponse = request.POST.get('reponse', '').strip()
        if reponse:
            resolution.resolu = True
            resolution.save()
            profil = Profil.objects(user_id=uid).first()
            if profil:
                profil.points += exercice.points
                profil.save()
            Activite(
                user_id=uid,
                type='exercice',
                description=f"Exercice résolu : {exercice.titre}",
            ).save()
            messages.success(request, f"Bravo ! +{exercice.points} XP")
            return redirect('cours_list')

    return render(request, 'core/exercice_detail.html', {
        'exercice': exercice,
        'resolution': resolution,
    })


@login_required
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
def tuteur(request):
    uid = request.user.id
    historique = MessageChat.objects(user_id=uid).order_by('date')[:50]
    sujet = None
    progressions = Progression.objects(user_id=uid, pourcentage__gt=0)
    if progressions.count() > 0:
        dernier = progressions.order_by('-pourcentage').first()
        sujet = dernier.cours.titre

    return render(request, 'core/tuteur.html', {
        'historique': historique,
        'sujet_actuel': sujet,
    })


@login_required
def tuteur_message(request):
    if request.method == 'POST':
        uid = request.user.id
        contenu = request.POST.get('message', '').strip()
        if contenu:
            MessageChat(user_id=uid, role='user', contenu=contenu).save()
            reponses = [
                f"Bonne question ! Voici une explication simple : en JavaScript, « {contenu[:50]}… » est un concept important. "
                f"Je te conseille de regarder le module correspondant dans les cours pour approfondir.",
                f"Excellente question ! Pour comprendre « {contenu[:50]}… », il faut d'abord maîtriser les bases. "
                f"Pratique avec les exercices du cours, ça t'aidera à assimiler le concept.",
                f"Intéressant ! « {contenu[:50]}… » est effectivement un point clé en JavaScript. "
                f"Voici un petit exemple :\n\n```js\n// Exemple illustratif\nconsole.log('Apprentissage en cours...');\n```\n\n"
                f"N'hésite pas si tu veux plus de détails !",
            ]
            reponse_ia = random.choice(reponses)
            MessageChat(user_id=uid, role='ai', contenu=reponse_ia).save()
    return redirect('tuteur')


@login_required
def examen(request):
    return render(request, 'core/examen.html', {})

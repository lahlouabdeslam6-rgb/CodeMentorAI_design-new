import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from mongoengine import DoesNotExist
from .decorators import admin_required
from .models import Profil, Formation, Cours, Exercice, Progression, Resolution, Activite, PasswordChangeRequest


def _slugify(nom):
    return nom.lower().replace(' ', '-').replace('#', '-sharp').replace('++', '-plus-plus').replace('+', '-plus').replace('.', '-').replace("'", '').replace('é', 'e').replace('è', 'e').replace('ê', 'e').replace('à', 'a').replace('ù', 'u').replace('ç', 'c')


def _assurer_formation(specialite, professor_id=None):
    """Crée une formation si elle n'existe pas pour la spécialité donnée."""
    if not specialite:
        return None
    formation = Formation.objects(nom__iexact=specialite).first()
    if not formation:
        slug = _slugify(specialite)
        formation = Formation(
            nom=specialite,
            slug=slug,
            description=f"Formation complète en {specialite} — du débutant à l'avancé.",
            emoji='📚',
            professor_id=professor_id or 0,
            ordre=Formation.objects.count() + 1,
        ).save()
    return formation


@admin_required
def admin_dashboard(request):
    total_students = Profil.objects(role='student').count()
    total_professors = Profil.objects(role='professor').count()
    total_formations = Formation.objects.count()
    valid_cours = Cours.objects(professor_id__ne=0)
    total_courses = valid_cours.count()
    valid_ids = [c.id for c in valid_cours]
    total_exercises = Exercice.objects(cours__in=valid_ids).count()
    total_active = Profil.objects(role='student', status='approved').count()
    recent_registrations = Profil.objects(role='student').order_by('-cree_le')[:10]
    recent_activities = Activite.objects.order_by('-date')[:10]

    registrations = Profil.objects(role='student')
    students_approved = registrations.filter(status='approved').count()
    students_pending = registrations.filter(status='pending').count()
    students_rejected = registrations.filter(status='rejected').count()

    import datetime, math
    today = datetime.date.today()
    weeks_labels = []
    registrations_over_time = []
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        day_start = datetime.datetime.combine(day, datetime.datetime.min.time())
        day_end = day_start + datetime.timedelta(days=1)
        count = Profil.objects(cree_le__gte=day_start, cree_le__lt=day_end).count()
        weeks_labels.append(day.strftime('%d/%m'))
        registrations_over_time.append(count)

    month_labels = []
    for i in range(5, -1, -1):
        m = today.replace(day=1) - datetime.timedelta(days=30*i)
        month_labels.append(m.strftime('%b'))

    return render(request, 'admin/dashboard.html', {
        'total_etudiants': total_students,
        'total_professeurs': total_professors,
        'total_formations': total_formations,
        'total_cours': total_courses,
        'total_exercices': total_exercises,
        'utilisateurs_actifs': total_active,
        'recent_registrations': recent_registrations,
        'recent_activities': recent_activities,
        'students_approved': students_approved,
        'students_pending': students_pending,
        'students_rejected': students_rejected,
        'weeks_labels': weeks_labels,
        'registrations_over_time': registrations_over_time,
        'month_labels': month_labels,
    })


@admin_required
def admin_students(request):
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    page = int(request.GET.get('page', 1))

    query = Profil.objects(role='student')
    if search:
        query = query.filter(username__icontains=search)
    if status_filter:
        query = query.filter(status=status_filter)

    all_students = list(query.order_by('-cree_le'))
    per_page = 10
    total_pages = max(1, (len(all_students) + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    students_page = all_students[start:end]

    student_data = []
    for s in students_page:
        user = User.objects.filter(id=s.user_id).first()
        student_data.append({
            'profil': s,
            'email': user.email if user else '',
            'is_active': user.is_active if user else False,
        })

    return render(request, 'admin/students.html', {
        'students': student_data,
        'search': search,
        'status_filter': status_filter,
        'page': page,
        'total_pages': total_pages,
        'count_approved': Profil.objects(role='student', status='approved').count(),
        'count_pending': Profil.objects(role='student', status='pending').count(),
        'count_rejected': Profil.objects(role='student', status='rejected').count(),
        'count_total': Profil.objects(role='student').count(),
    })


@admin_required
def admin_student_approve(request, user_id):
    profil = Profil.objects(user_id=user_id, role='student').first()
    if profil:
        profil.status = 'approved'
        profil.save()
        messages.success(request, f"Étudiant {profil.username} approuvé.")
    return redirect('admin_students')


@admin_required
def admin_student_reject(request, user_id):
    profil = Profil.objects(user_id=user_id, role='student').first()
    if profil:
        profil.status = 'rejected'
        profil.save()
        messages.success(request, f"Étudiant {profil.username} rejeté.")
    return redirect('admin_students')


@admin_required
def admin_student_toggle_active(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    status = "activé" if user.is_active else "désactivé"
    messages.success(request, f"Compte {user.username} {status}.")
    return redirect('admin_students')


@admin_required
def admin_student_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)
    Profil.objects(user_id=user_id).delete()
    Activite.objects(user_id=user_id).delete()
    Progression.objects(user_id=user_id).delete()
    Resolution.objects(user_id=user_id).delete()
    username = user.username
    user.delete()
    messages.success(request, f"Étudiant {username} supprimé.")
    return redirect('admin_students')


@admin_required
def admin_professors(request):
    search = request.GET.get('search', '')
    page = int(request.GET.get('page', 1))

    query = Profil.objects(role='professor')
    if search:
        query = query.filter(username__icontains=search)

    all_profs = list(query.order_by('-cree_le'))
    per_page = 10
    total_pages = max(1, (len(all_profs) + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    profs_page = all_profs[start:end]

    prof_data = []
    for p in profs_page:
        user = User.objects.filter(id=p.user_id).first()
        courses = list(Cours.objects(professor_id=p.user_id))
        course_count = len(courses)
        prof_data.append({
            'profil': p,
            'email': user.email if user else '',
            'course_count': course_count,
            'courses': courses,
            'specialite': p.specialite or '—',
        })

    return render(request, 'admin/professors.html', {
        'professors': prof_data,
        'search': search,
        'page': page,
        'total_pages': total_pages,
        'count_total': Profil.objects(role='professor').count(),
    })


SPECIALITES = ['JavaScript', 'Python', 'Java', 'PHP', 'React', 'Laravel', 'C#', 'C++', 'Autre']

@admin_required
def admin_professor_create(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        specialite = request.POST.get('specialite', '').strip()
        if specialite == 'Autre':
            specialite = request.POST.get('nouvelle_matiere', '').strip()

        errors = []
        if not username:
            errors.append("Le nom d'utilisateur est requis.")
        if User.objects.filter(username=username).exists():
            errors.append("Ce nom d'utilisateur existe déjà.")
        if not email:
            errors.append("L'adresse email est requise.")
        elif User.objects.filter(email=email).exists():
            errors.append("Cette adresse email est déjà utilisée.")
        if not password or len(password) < 3:
            errors.append("Le mot de passe doit contenir au moins 3 caractères.")
        if not specialite:
            errors.append("La matière enseignée est requise.")

        if not errors:
            user = User.objects.create_user(username=username, email=email, password=password)
            Profil(
                user_id=user.id,
                username=username,
                email=email,
                role='professor',
                status='approved',
                specialite=specialite,
            ).save()
            formation = _assurer_formation(specialite, professor_id=user.id)
            msg = f"Professeur {username} créé avec succès (spécialité : {specialite})."
            if formation:
                msg += f" Formation « {formation.nom} » ajoutée au catalogue."
            messages.success(request, msg)
            return redirect('admin_professors')

        for err in errors:
            messages.error(request, err)

    return render(request, 'admin/professor_form.html', {'edit': False, 'specialites': SPECIALITES})


@admin_required
def admin_professor_edit(request, user_id):
    profil = Profil.objects(user_id=user_id, role='professor').first()
    if not profil:
        messages.error(request, "Professeur introuvable.")
        return redirect('admin_professors')
    user = User.objects.filter(id=user_id).first()

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        specialite = request.POST.get('specialite', '').strip()
        if specialite == 'Autre':
            specialite = request.POST.get('nouvelle_matiere', '').strip()

        if email:
            if User.objects.filter(email=email).exclude(id=user_id).exists():
                messages.error(request, "Cette adresse email est déjà utilisée.")
            else:
                user.email = email
                profil.email = email
                user.save()
                profil.save()
        if password:
            user.set_password(password)
            user.save()
        if specialite:
            old_specialite = profil.specialite
            profil.specialite = specialite
            profil.save()
            if specialite != old_specialite:
                _assurer_formation(specialite, professor_id=user_id)
        messages.success(request, f"Professeur {profil.username} modifié.")
        return redirect('admin_professors')

    return render(request, 'admin/professor_form.html', {
        'edit': True,
        'profil': profil,
        'user': user,
        'specialites': SPECIALITES,
    })


@admin_required
def admin_professor_delete(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if user:
        username = user.username
        Profil.objects(user_id=user_id).delete()
        Cours.objects(professor_id=user_id).update(professor_id=0)
        user.delete()
        messages.success(request, f"Professeur {username} supprimé.")
    return redirect('admin_professors')


@admin_required
def admin_user_detail(request, user_id):
    profil = Profil.objects(user_id=user_id).first()
    user = User.objects.filter(id=user_id).first()
    if not profil:
        messages.error(request, "Utilisateur introuvable.")
        return redirect('admin_students' if request.GET.get('role') != 'professor' else 'admin_professors')

    course_count = Cours.objects(professor_id=user_id).count() if profil.role == 'professor' else 0
    progressions = Progression.objects(user_id=user_id)
    resolutions = Resolution.objects(user_id=user_id)
    resolu_count = resolutions.filter(resolu=True).count()
    total_resolutions = resolutions.count()
    activities = Activite.objects(user_id=user_id).order_by('-date')[:20]
    formations_progress = FormationProgress.objects(user_id=user_id).order_by('-xp')

    return render(request, 'admin/user_detail.html', {
        'profil': profil,
        'user': user,
        'course_count': course_count,
        'progressions': progressions,
        'resolu_count': resolu_count,
        'total_resolutions': total_resolutions,
        'activities': activities,
        'formations_progress': formations_progress,
    })


@admin_required
def admin_password_reset(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if not user:
        messages.error(request, "Utilisateur introuvable.")
        return redirect('admin_students')

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm = request.POST.get('confirm_password', '').strip()
        if not new_password or len(new_password) < 3:
            messages.error(request, "Le mot de passe doit contenir au moins 3 caractères.")
        elif new_password != confirm:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        else:
            user.set_password(new_password)
            user.save()
            messages.success(request, f"Mot de passe réinitialisé pour {user.username}.")
            return redirect('admin_user_detail', user_id=user_id)

    return render(request, 'admin/password_reset.html', {'target_user': user})


@admin_required
def admin_password_requests(request):
    filtres = {
        'etudiant': {'role': 'student'},
        'professeur': {'role': 'professor'},
        'en_attente': {'status': 'pending'},
        'acceptee': {'status': 'accepted'},
        'refusee': {'status': 'rejected'},
    }
    q = {}
    for key, fq in filtres.items():
        if request.GET.get(key):
            q.update(fq)

    demandes = PasswordChangeRequest.objects(**q).order_by('-created_at')
    return render(request, 'admin/password_requests.html', {
        'demandes': demandes,
        'total_pending': PasswordChangeRequest.objects(status='pending').count(),
    })


@admin_required
def admin_password_request_action(request, request_id, action):
    demande = PasswordChangeRequest.objects(id=request_id).first()
    if not demande:
        messages.error(request, "Demande introuvable.")
        return redirect('admin_password_requests')

    if demande.status != 'pending':
        messages.warning(request, "Cette demande a déjà été traitée.")
        return redirect('admin_password_requests')

    if action == 'accept':
        user = User.objects.filter(id=demande.user_id).first()
        if user:
            user.password = demande.new_password
            user.save()
        demande.status = 'accepted'
        demande.processed_at = datetime.now()
        demande.processed_by = request.user.id
        demande.save()
        messages.success(request, f"✅ Mot de passe mis à jour pour {demande.username}.")
        import logging
        logging.getLogger('password_requests').info(
            f"Admin {request.user.username} a accepté la demande de {demande.username} "
            f"(id={demande.user_id}) le {demande.processed_at}."
        )
    elif action == 'reject':
        demande.status = 'rejected'
        demande.processed_at = datetime.now()
        demande.processed_by = request.user.id
        demande.save()
        messages.info(request, f"❌ Demande refusée pour {demande.username}.")
        import logging
        logging.getLogger('password_requests').info(
            f"Admin {request.user.username} a refusé la demande de {demande.username} "
            f"(id={demande.user_id}) le {demande.processed_at}."
        )

    return redirect('admin_password_requests')

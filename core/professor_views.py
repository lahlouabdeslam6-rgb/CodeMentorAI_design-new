from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from mongoengine import DoesNotExist
from .decorators import professor_required
from .models import Profil, Cours, Lesson, Exercice, Resolution, Progression, Activite, FormationProgress


def _get_prof_specialite(user_id):
    profil = Profil.objects(user_id=user_id, role='professor').first()
    return profil.specialite if profil else ''


@professor_required
def professor_dashboard(request):
    uid = request.user.id
    specialite = _get_prof_specialite(uid)
    if specialite:
        my_courses = Cours.objects(category__iexact=specialite, professor_id=uid)
    else:
        my_courses = Cours.objects(professor_id=uid)
    course_count = my_courses.count()
    total_lessons = Lesson.objects(cours__in=my_courses).count()
    exercises = Exercice.objects(cours__in=my_courses)
    exercise_count = exercises.count()

    enrolled_students = set()
    for c in my_courses:
        progressions = Progression.objects(cours=c)
        for p in progressions:
            enrolled_students.add(p.user_id)
    student_count = len(enrolled_students)

    course_list = []
    for c in my_courses:
        lesson_count = Lesson.objects(cours=c).count()
        exo_count = Exercice.objects(cours=c).count()
        stu_count = Progression.objects(cours=c).count()
        course_list.append({
            'cours': c,
            'lesson_count': lesson_count,
            'exo_count': exo_count,
            'student_count': stu_count,
        })

    all_profils = Profil.objects(role='student').order_by('-cree_le')
    total_cours_all = Cours.objects.count()
    student_list = []
    for p in all_profils:
        user_model = User.objects.filter(id=p.user_id).first()
        if not user_model:
            continue
        has_activity = False
        for c in my_courses:
            prog = Progression.objects(user_id=p.user_id, cours=c).first()
            if prog:
                has_activity = True
                break
        if not has_activity:
            continue
        stu_courses = []
        for c in my_courses:
            prog = Progression.objects(user_id=p.user_id, cours=c).first()
            if prog:
                stu_courses.append({'titre': c.titre, 'slug': c.slug})
        if stu_courses:
            fp = FormationProgress.objects(user_id=p.user_id, formation_nom=specialite).first() if specialite else None
            student_list.append({
                'username': user_model.username,
                'fullname': p.fullname or user_model.username,
                'email': user_model.email,
                'niveau': p.niveau,
                'niveau_display': p.get_niveau_label(),
                'courses': stu_courses,
                'xp_formation': fp.xp if fp else 0,
                'course_count': len(stu_courses),
            })

    student_list.sort(key=lambda x: x['xp_formation'], reverse=True)

    return render(request, 'professor/dashboard.html', {
        'course_count': course_count,
        'total_lessons': total_lessons,
        'exercise_count': exercise_count,
        'student_count': len(student_list),
        'course_list': course_list,
        'student_list': student_list,
        'specialite': specialite,
    })


@professor_required
def professor_courses(request):
    uid = request.user.id
    specialite = _get_prof_specialite(uid)
    if specialite:
        all_courses = Cours.objects(category__iexact=specialite, professor_id=uid).order_by('ordre')
    else:
        all_courses = Cours.objects(professor_id=uid).order_by('ordre')

    course_data = []
    for c in all_courses:
        lesson_count = Lesson.objects(cours=c).count()
        exo_count = Exercice.objects(cours=c).count()
        student_count = Progression.objects(cours=c).count()
        course_data.append({
            'cours': c,
            'lesson_count': lesson_count,
            'exo_count': exo_count,
            'student_count': student_count,
            'is_owner': True,
            'professor_name': request.user.username,
            'specialite': specialite,
        })

    return render(request, 'professor/course_list.html', {
        'courses': course_data,
        'total': len(course_data),
        'specialite': specialite,
    })


@professor_required
def professor_course_create(request):
    uid = request.user.id
    specialite = _get_prof_specialite(uid)

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        description = request.POST.get('description', '').strip()
        niveau = request.POST.get('niveau', 'debutant')
        emoji = request.POST.get('emoji', '📘')

        errors = []
        if not titre:
            errors.append("Le titre est requis.")
        if not description:
            errors.append("La description est requise.")
        if not specialite:
            errors.append("Vous n'avez pas de spécialité définie. Contactez l'administrateur.")

        if not errors:
            slug = titre.lower().replace(' ', '-')[:50]
            import re
            slug = re.sub(r'[^a-z0-9-]', '', slug)
            base_slug = slug
            counter = 1
            while Cours.objects(slug=slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1

            max_ordre = Cours.objects(professor_id=request.user.id).count() + 1
            Cours(
                titre=titre,
                slug=slug,
                description=description,
                niveau=niveau,
                category=specialite,
                emoji=emoji,
                professor_id=request.user.id,
                ordre=max_ordre,
            ).save()
            messages.success(request, f"Cours '{titre}' créé.")
            return redirect('professor_courses')

        for err in errors:
            messages.error(request, err)

    return render(request, 'professor/course_form.html', {
        'edit': False,
        'specialite': specialite,
    })


@professor_required
def professor_course_edit(request, slug):
    uid = request.user.id
    specialite = _get_prof_specialite(uid)
    cours = Cours.objects(slug=slug, professor_id=uid).first()
    if not cours:
        messages.error(request, "Cours introuvable ou vous n'êtes pas le propriétaire.")
        return redirect('professor_courses')
    if specialite and cours.category.lower() != specialite.lower():
        messages.error(request, "Vous ne pouvez modifier que les cours de votre spécialité.")
        return redirect('professor_courses')

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        description = request.POST.get('description', '').strip()
        niveau = request.POST.get('niveau', cours.niveau)
        emoji = request.POST.get('emoji', cours.emoji)

        if titre:
            cours.titre = titre
        cours.description = description
        cours.niveau = niveau
        cours.category = specialite if specialite else cours.category
        cours.emoji = emoji
        cours.save()
        messages.success(request, f"Cours '{cours.titre}' modifié.")
        return redirect('professor_courses')

    return render(request, 'professor/course_form.html', {
        'edit': True,
        'cours': cours,
    })


@professor_required
def professor_course_delete(request, slug):
    uid = request.user.id
    specialite = _get_prof_specialite(uid)
    cours = Cours.objects(slug=slug, professor_id=uid).first()
    if cours:
        if specialite and cours.category.lower() != specialite.lower():
            messages.error(request, "Vous ne pouvez supprimer que les cours de votre spécialité.")
            return redirect('professor_courses')
        titre = cours.titre
        Exercice.objects(cours=cours).delete()
        Lesson.objects(cours=cours).delete()
        Progression.objects(cours=cours).delete()
        cours.delete()
        messages.success(request, f"Cours '{titre}' supprimé.")
    return redirect('professor_courses')


@professor_required
def professor_lessons(request, slug):
    uid = request.user.id
    specialite = _get_prof_specialite(uid)
    cours = Cours.objects(slug=slug).first()
    if not cours:
        messages.error(request, "Cours introuvable.")
        return redirect('professor_courses')
    if specialite and cours.category.lower() != specialite.lower():
        messages.error(request, "Vous ne pouvez accéder qu'aux cours de votre spécialité.")
        return redirect('professor_courses')

    lessons = Lesson.objects(cours=cours).order_by('ordre')
    chapters = []
    seen = set()
    for l in lessons:
        ch = l.chapitre or 'Général'
        if ch not in seen:
            seen.add(ch)
            chapters.append(ch)

    return render(request, 'professor/lesson_list.html', {
        'cours': cours,
        'lessons': lessons,
        'chapters': chapters,
        'count': lessons.count(),
    })


@professor_required
def professor_lesson_create(request, slug):
    uid = request.user.id
    specialite = _get_prof_specialite(uid)
    cours = Cours.objects(slug=slug).first()
    if not cours:
        messages.error(request, "Cours introuvable.")
        return redirect('professor_courses')
    if specialite and cours.category.lower() != specialite.lower():
        messages.error(request, "Vous ne pouvez créer des leçons que dans votre spécialité.")
        return redirect('professor_courses')

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        content = request.POST.get('content', '').strip()
        video_url = request.POST.get('video_url', '').strip()
        chapitre = request.POST.get('chapitre', '').strip()

        pdf_path = ''
        if request.FILES.get('pdf_file'):
            pdf_file = request.FILES['pdf_file']
            if not pdf_file.name.lower().endswith('.pdf'):
                messages.error(request, "Seuls les fichiers PDF sont autorisés.")
                return redirect('professor_lesson_create', slug=slug)
            if pdf_file.size > 20 * 1024 * 1024:
                messages.error(request, "Le fichier PDF ne doit pas dépasser 20 Mo.")
                return redirect('professor_lesson_create', slug=slug)
            import os
            from django.conf import settings
            subdir = 'lesson_pdfs'
            upload_dir = settings.MEDIA_ROOT / subdir
            os.makedirs(upload_dir, exist_ok=True)
            safe_name = f"{cours.slug}_{titre.replace(' ', '_')}_{pdf_file.name}"
            dest = upload_dir / safe_name
            with open(dest, 'wb+') as f:
                for chunk in pdf_file.chunks():
                    f.write(chunk)
            pdf_path = f"{subdir}/{safe_name}"

        if not titre:
            messages.error(request, "Le titre de la leçon est requis.")
        else:
            max_ordre = Lesson.objects(cours=cours).count() + 1
            Lesson(
                cours=cours,
                titre=titre,
                content=content,
                video_url=video_url,
                pdf_url=pdf_path,
                chapitre=chapitre or 'Général',
                ordre=max_ordre,
            ).save()
            messages.success(request, f"Lecon '{titre}' creee.")
            return redirect('professor_lessons', slug=slug)

    chapters = list(set(l.chapitre for l in Lesson.objects(cours=cours)))
    return render(request, 'professor/lesson_form.html', {
        'edit': False,
        'cours': cours,
        'chapters': chapters,
    })


@professor_required
def professor_lesson_edit(request, slug, lesson_id):
    uid = request.user.id
    specialite = _get_prof_specialite(uid)
    cours = Cours.objects(slug=slug).first()
    if specialite and cours and cours.category.lower() != specialite.lower():
        messages.error(request, "Vous ne pouvez modifier que les leçons de votre spécialité.")
        return redirect('professor_courses')
    lesson = Lesson.objects(id=lesson_id, cours=cours).first()
    if not lesson:
        messages.error(request, "Leçon introuvable.")
        return redirect('professor_lessons', slug=slug)

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        content = request.POST.get('content', '').strip()
        video_url = request.POST.get('video_url', '').strip()
        chapitre = request.POST.get('chapitre', '').strip()

        if request.FILES.get('pdf_file'):
            pdf_file = request.FILES['pdf_file']
            if not pdf_file.name.lower().endswith('.pdf'):
                messages.error(request, "Seuls les fichiers PDF sont autorisés.")
                return redirect('professor_lesson_edit', slug=slug, lesson_id=lesson_id)
            if pdf_file.size > 20 * 1024 * 1024:
                messages.error(request, "Le fichier PDF ne doit pas dépasser 20 Mo.")
                return redirect('professor_lesson_edit', slug=slug, lesson_id=lesson_id)
            import os
            from django.conf import settings
            subdir = 'lesson_pdfs'
            upload_dir = settings.MEDIA_ROOT / subdir
            os.makedirs(upload_dir, exist_ok=True)
            safe_name = f"{cours.slug}_{titre.replace(' ', '_')}_{pdf_file.name}"
            dest = upload_dir / safe_name
            with open(dest, 'wb+') as f:
                for chunk in pdf_file.chunks():
                    f.write(chunk)
            lesson.pdf_url = f"{subdir}/{safe_name}"

        if titre:
            lesson.titre = titre
        lesson.content = content
        lesson.video_url = video_url
        lesson.chapitre = chapitre or 'Général'
        lesson.save()
        messages.success(request, f"Lecon '{lesson.titre}' modifiee.")
        return redirect('professor_lessons', slug=slug)

    chapters = list(set(l.chapitre for l in Lesson.objects(cours=cours)))
    return render(request, 'professor/lesson_form.html', {
        'edit': True,
        'cours': cours,
        'lesson': lesson,
        'chapters': chapters,
    })


@professor_required
def professor_lesson_delete(request, slug, lesson_id):
    uid = request.user.id
    specialite = _get_prof_specialite(uid)
    lesson = Lesson.objects(id=lesson_id).first()
    if lesson and lesson.cours:
        if specialite and lesson.cours.category.lower() != specialite.lower():
            messages.error(request, "Vous ne pouvez supprimer que les leçons de votre spécialité.")
            return redirect('professor_courses')
    if lesson:
        titre = lesson.titre
        lesson.delete()
        messages.success(request, f"Leçon '{titre}' supprimée.")
    return redirect('professor_lessons', slug=slug)


@professor_required
def professor_exercises(request, slug):
    uid = request.user.id
    specialite = _get_prof_specialite(uid)
    cours = Cours.objects(slug=slug).first()
    if not cours:
        messages.error(request, "Cours introuvable.")
        return redirect('professor_courses')
    if specialite and cours.category.lower() != specialite.lower():
        messages.error(request, "Vous ne pouvez accéder qu'aux exercices de votre spécialité.")
        return redirect('professor_courses')

    exercises = Exercice.objects(cours=cours)
    exo_data = []
    for exo in exercises:
        total_attempts = Resolution.objects(exercice=exo).count()
        resolved = Resolution.objects(exercice=exo, resolu=True).count()
        exo_data.append({
            'exercice': exo,
            'total_attempts': total_attempts,
            'resolved': resolved,
        })

    return render(request, 'professor/exercise_list.html', {
        'cours': cours,
        'exercises': exo_data,
        'count': len(exo_data),
    })


@professor_required
def professor_exercise_create(request, slug):
    uid = request.user.id
    specialite = _get_prof_specialite(uid)
    cours = Cours.objects(slug=slug).first()
    if not cours:
        messages.error(request, "Cours introuvable.")
        return redirect('professor_courses')
    if specialite and cours.category.lower() != specialite.lower():
        messages.error(request, "Vous ne pouvez créer des exercices que dans votre spécialité.")
        return redirect('professor_courses')

    lessons = Lesson.objects(cours=cours).order_by('ordre')

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        enonce = request.POST.get('enonce', '').strip()
        correction = request.POST.get('correction', '').strip()
        difficulte = request.POST.get('difficulte', 'facile')
        categorie = request.POST.get('categorie', 'Général')
        points = request.POST.get('points', 10)
        lesson_id = request.POST.get('lesson_id', '').strip()

        if not titre:
            messages.error(request, "Le titre est requis.")
        elif not lesson_id:
            messages.error(request, "Veuillez sélectionner une leçon.")
        else:
            lesson = Lesson.objects(id=lesson_id, cours=cours).first()
            if not lesson:
                messages.error(request, "Leçon invalide.")
            else:
                Exercice(
                    cours=cours,
                    lesson=lesson,
                    titre=titre,
                    enonce=enonce,
                    correction=correction,
                    difficulte=difficulte,
                    categorie=categorie,
                    points=int(points),
                    lesson_nom=lesson.titre,
                ).save()
                messages.success(request, f"Exercice '{titre}' créé.")
                return redirect('professor_exercises', slug=slug)

    return render(request, 'professor/exercise_form.html', {
        'edit': False,
        'cours': cours,
        'lessons': lessons,
    })


@professor_required
def professor_exercise_edit(request, slug, exercise_id):
    uid = request.user.id
    specialite = _get_prof_specialite(uid)
    cours = Cours.objects(slug=slug).first()
    if specialite and cours and cours.category.lower() != specialite.lower():
        messages.error(request, "Vous ne pouvez modifier que les exercices de votre spécialité.")
        return redirect('professor_courses')
    exercice = Exercice.objects(id=exercise_id, cours=cours).first()
    if not exercice:
        messages.error(request, "Exercice introuvable.")
        return redirect('professor_exercises', slug=slug)

    lessons = Lesson.objects(cours=cours).order_by('ordre')

    if request.method == 'POST':
        titre = request.POST.get('titre', '').strip()
        enonce = request.POST.get('enonce', '').strip()
        correction = request.POST.get('correction', '').strip()
        difficulte = request.POST.get('difficulte', exercice.difficulte)
        categorie = request.POST.get('categorie', exercice.categorie)
        points = request.POST.get('points', exercice.points)
        lesson_id = request.POST.get('lesson_id', '').strip()

        if titre:
            exercice.titre = titre
        exercice.enonce = enonce
        exercice.correction = correction
        exercice.difficulte = difficulte
        exercice.categorie = categorie
        exercice.points = int(points)
        if lesson_id:
            lesson = Lesson.objects(id=lesson_id, cours=cours).first()
            if lesson:
                exercice.lesson = lesson
                exercice.lesson_nom = lesson.titre
        exercice.save()
        messages.success(request, f"Exercice '{exercice.titre}' modifié.")
        return redirect('professor_exercises', slug=slug)

    return render(request, 'professor/exercise_form.html', {
        'edit': True,
        'cours': cours,
        'exercice': exercice,
        'lessons': lessons,
    })


@professor_required
def professor_exercise_delete(request, slug, exercise_id):
    uid = request.user.id
    specialite = _get_prof_specialite(uid)
    exercice = Exercice.objects(id=exercise_id).first()
    if exercice and exercice.cours:
        if specialite and exercice.cours.category.lower() != specialite.lower():
            messages.error(request, "Vous ne pouvez supprimer que les exercices de votre spécialité.")
            return redirect('professor_courses')
    if exercice:
        titre = exercice.titre
        Resolution.objects(exercice=exercice).delete()
        exercice.delete()
        messages.success(request, f"Exercice '{titre}' supprimé.")
    return redirect('professor_exercises', slug=slug)


@professor_required
def professor_students(request):
    uid = request.user.id
    specialite = _get_prof_specialite(uid)
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    all_profils = Profil.objects(role='student').order_by('-cree_le')
    if search:
        all_profils = all_profils.filter(username__icontains=search)

    if specialite:
        prof_courses = list(Cours.objects(category__iexact=specialite, professor_id=uid))
    else:
        prof_courses = list(Cours.objects(professor_id=uid))
    total_specialite = len(prof_courses)

    student_list = []
    for p in all_profils:
        user_model = User.objects.filter(id=p.user_id).first()
        if not user_model:
            continue
        stu_courses = []
        for c in prof_courses:
            prog = Progression.objects(user_id=p.user_id, cours=c).first()
            if prog:
                stu_courses.append({'titre': c.titre, 'slug': c.slug})
        fp = FormationProgress.objects(user_id=p.user_id, formation_nom=specialite).first() if specialite else None
        xp_formation = fp.xp if fp else 0
        student_list.append({
            'user_id': p.user_id,
            'username': user_model.username,
            'fullname': p.fullname or user_model.username,
            'email': user_model.email,
            'is_active': user_model.is_active,
            'status': p.status,
            'niveau': p.niveau,
            'niveau_display': p.get_niveau_label(),
            'xp_formation': xp_formation,
            'formation_nom': specialite or '',
            'courses': stu_courses,
            'course_count': total_specialite,
        })

    return render(request, 'professor/student_list.html', {
        'students': student_list,
        'total': len(student_list),
        'search': search,
    })

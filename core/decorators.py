from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from .models import Profil


def student_required(view_func):
    def wrapper(request, *args, **kwargs):
        profil = Profil.objects(user_id=request.user.id).first()
        if not profil or profil.role != 'student':
            messages.error(request, "Accès réservé aux étudiants.")
            if profil:
                return redirect(get_role_dashboard(profil.role))
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        profil = Profil.objects(user_id=request.user.id).first()
        if not profil or profil.role != 'admin':
            messages.error(request, "Accès réservé aux administrateurs.")
            if profil:
                return redirect(get_role_dashboard(profil.role))
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def professor_required(view_func):
    def wrapper(request, *args, **kwargs):
        profil = Profil.objects(user_id=request.user.id).first()
        if not profil or profil.role != 'professor':
            messages.error(request, "Accès réservé aux professeurs.")
            if profil:
                return redirect(get_role_dashboard(profil.role))
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_role_dashboard(role):
    roles = {
        'admin': 'admin_dashboard',
        'professor': 'professor_dashboard',
        'student': 'dashboard',
    }
    return roles.get(role, 'home')
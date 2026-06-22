from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('register/', views.register, name='register'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('cours/', views.cours_list, name='cours_list'),
    path('cours/<slug:slug>/', views.cours_detail, name='cours_detail'),
    path('diagnostic/', views.diagnostic, name='diagnostic'),
    path('tuteur/', views.tuteur, name='tuteur'),
    path('tuteur/message/', views.tuteur_message, name='tuteur_message'),
    path('exercice/<str:pk>/', views.exercice_detail, name='exercice_detail'),
    path('examen/', views.examen, name='examen'),
]

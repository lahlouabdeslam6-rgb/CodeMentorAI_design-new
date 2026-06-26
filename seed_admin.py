import os, sys
sys.path.insert(0, os.path.dirname(__file__))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

import django
django.setup()

from django.contrib.auth.models import User
from core.models import Profil

ADMIN_USERNAME = 'admin'
ADMIN_EMAIL = 'admin@codementor.ai'
ADMIN_PASSWORD = 'admin123'

existing = User.objects.filter(username=ADMIN_USERNAME).first()
if existing:
    existing.email = ADMIN_EMAIL
    existing.set_password(ADMIN_PASSWORD)
    existing.is_superuser = True
    existing.is_staff = True
    existing.save()
    print(f"Admin '{ADMIN_USERNAME}' mis à jour.")
else:
    user = User.objects.create_superuser(
        username=ADMIN_USERNAME,
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
    )
    print(f"Admin '{ADMIN_USERNAME}' créé.")

profil = Profil.objects(user_id=user.id if 'user' in dir() else existing.id).first()
uid = user.id if 'user' in dir() else existing.id

if profil:
    profil.role = 'admin'
    profil.status = 'approved'
    profil.fullname = 'Administrateur'
    profil.email = ADMIN_EMAIL
    profil.save()
    print(f"Profil admin mis à jour (user_id={profil.user_id}).")
else:
    Profil(
        user_id=uid,
        username=ADMIN_USERNAME,
        email=ADMIN_EMAIL,
        fullname='Administrateur',
        role='admin',
        status='approved',
    ).save()
    print(f"Profil admin créé (user_id={uid}).")

print(f"\n✅ Admin prêt : {ADMIN_EMAIL} / {ADMIN_PASSWORD}")

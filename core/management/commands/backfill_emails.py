from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Profil


class Command(BaseCommand):
    help = "Remplit les emails vides avec username@gmail.com"

    def handle(self, *args, **options):
        count = 0
        for user in User.objects.all():
            if not user.email:
                user.email = f"{user.username}@gmail.com"
                user.save()
                count += 1
                self.stdout.write(f"  {user.username} -> {user.email}")

        for profil in Profil.objects(email__in=['', None]):
            if not profil.email:
                profil.email = f"{profil.username}@gmail.com"
                profil.save()
                count += 1
                self.stdout.write(f"  Profil {profil.username} -> {profil.email}")

        self.stdout.write(self.style.SUCCESS(f"{count} comptes mis a jour."))

from .models import Profil


def profil_context(request):
    if request.user.is_authenticated:
        profil = Profil.objects(user_id=request.user.id).first()
        return {'profil': profil}
    return {}
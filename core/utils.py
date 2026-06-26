from datetime import datetime
from .models import Profil, ScoreExercice, AccesExamen, FormationProgress


def _obtenir_ou_creer_progress(user_id, formation_nom):
    fp = FormationProgress.objects(user_id=user_id, formation_nom=formation_nom).first()
    if not fp:
        fp = FormationProgress(user_id=user_id, formation_nom=formation_nom).save()
    return fp


def verifier_acces_examen(user_id, formation_nom='JavaScript'):
    scores = ScoreExercice.objects(user_id=user_id)
    fp = _obtenir_ou_creer_progress(user_id, formation_nom)
    condition = fp.completed_exercises >= 8

    acces = AccesExamen.objects(user_id=user_id, formation_nom=formation_nom).first()
    if not acces:
        acces = AccesExamen(user_id=user_id, formation_nom=formation_nom).save()

    if condition and not acces.debloque:
        acces.debloque = True
        acces.date_deblocage = datetime.now()
        acces.score_global = float(fp.xp)
        acces.save()
    elif not condition:
        acces.score_global = float(fp.xp)
        acces.save()

    return acces


def enregistrer_score(user_id, exercice, score_obtenu):
    formation_nom = exercice.cours.category if exercice.cours else 'Général'

    score_obj = ScoreExercice.objects(user_id=user_id, exercice=exercice).first()
    if not score_obj:
        score_obj = ScoreExercice(
            user_id=user_id,
            exercice=exercice,
            score_obtenu=score_obtenu,
            score_max=exercice.points,
        ).save()
    else:
        if score_obtenu > score_obj.score_obtenu:
            score_obj.score_obtenu = score_obtenu
        score_obj.tentatives += 1
        score_obj.score_max = exercice.points
        score_obj.save()

    fp = _obtenir_ou_creer_progress(user_id, formation_nom)
    exos_faits = ScoreExercice.objects(user_id=user_id).count()
    exos_dans_formation = [s for s in ScoreExercice.objects(user_id=user_id)
                          if s.exercice and s.exercice.cours
                          and s.exercice.cours.category == formation_nom]
    fp.completed_exercises = len(exos_dans_formation)

    total_xp_formation = sum(
        s.score_obtenu for s in exos_dans_formation
    )
    fp.xp = total_xp_formation
    fp.save()

    acces = verifier_acces_examen(user_id, formation_nom)
    total_xp = float(fp.xp)

    return score_obj, acces, total_xp, formation_nom

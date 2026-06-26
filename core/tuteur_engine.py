import re, html
from collections import Counter
from .models import Cours, Lesson, Exercice, Progression, Formation, NiveauMatiere

# ─────────────────────────────────────────────
#  SEARCH — find relevant lessons for a question
# ─────────────────────────────────────────────

STOP_WORDS = {
    'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'est', 'et', 'à', 'a',
    'dans', 'pour', 'sur', 'par', 'avec', 'que', 'qui', 'quoi', 'comment',
    'pourquoi', 'quand', 'où', 'ce', 'cet', 'cette', 'ces', 'mon', 'ton',
    'son', 'ma', 'ta', 'sa', 'mes', 'tes', 'ses', 'je', 'tu', 'il', 'elle',
    'nous', 'vous', 'ils', 'elles', 'me', 'te', 'se', 'en', 'y', 'au', 'aux',
    'pas', 'plus', 'très', 'trop', 'si', 'non', 'oui', 'ça', 'cela', 'faire',
    'voir', 'savoir', 'pouvoir', 'vouloir', 'devoir', 'falloir', 'être', 'avoir',
    'the', 'a', 'an', 'is', 'it', 'to', 'in', 'of', 'for', 'on', 'that', 'this',
    'what', 'how', 'why', 'which', 'with', 'or', 'and', 'not', 'are', 'was',
}


def _tokeniser(texte):
    """Extrait les mots clés significatifs d'un texte."""
    mots = re.findall(r"[a-zA-Z0-9_#+.-]+", texte.lower())
    return [m for m in mots if len(m) > 2 and m not in STOP_WORDS]


def _rechercher_lecons(formation_nom, question, top_k=5):
    """Cherche dans les leçons de la formation les plus pertinentes pour la question.
    
    Score basé sur :
      - Mots-clés dans le titre de la leçon (×5)
      - Mots-clés dans le contenu markdown (×1)
    Retourne une liste de (lesson, score, mots_trouves).
    """
    tokens = _tokeniser(question)
    if not tokens:
        return {}

    # Récupérer tous les cours de la formation
    cours_list = Cours.objects(category__iexact=formation_nom, professor_id__ne=0)
    if not cours_list:
        cours_list = Cours.objects(professor_id__ne=0)

    scores = {}  # lesson_id -> (lesson, score, matches)

    for c in cours_list:
        for lesson in Lesson.objects(cours=c):
            # Titre
            titre_tokens = _tokeniser(lesson.titre)
            titre_matches = sum(1 for t in tokens if t in titre_tokens)
            # Contenu
            contenu_tokens = _tokeniser(lesson.content or '')
            contenu_matches = sum(1 for t in tokens if t in contenu_tokens)

            total = titre_matches * 5 + contenu_matches
            if total > 0:
                matched = [t for t in tokens
                           if t in titre_tokens or t in contenu_tokens]
                # Bonus de phrase exacte (si la question apparaît presque textuellement)
                words_q = set(tokens)
                words_content = set(_tokeniser((lesson.titre or '') + ' ' + (lesson.content or '')))
                phrase_score = len(words_q & words_content) / max(len(words_q), 1)
                total += int(phrase_score * 10)

                if str(lesson.id) not in scores:
                    scores[str(lesson.id)] = (lesson, total, matched)
                else:
                    old = scores[str(lesson.id)]
                    scores[str(lesson.id)] = (lesson, old[1] + total, old[2] + matched)

    # Trier par score décroissant et garder top_k
    sorted_scores = sorted(scores.values(), key=lambda x: -x[1])
    result = {}
    for lesson, score, matches in sorted_scores[:top_k]:
        result[str(lesson.id)] = {
            'lesson': lesson,
            'score': score,
            'matches': list(set(matches)),
        }
    return result


def _trouver_exos_par_lesson(lesson):
    if not lesson:
        return []
    return list(Exercice.objects(lesson=lesson))


def _trouver_cours_par_lesson(lesson):
    if not lesson or not lesson.cours:
        return None
    return lesson.cours


# ─────────────────────────────────────────────
#  RÉPONSES PRÉDÉFINIES
# ─────────────────────────────────────────────

def _reponse_quiz():
    return (
        "📝 **Quiz express**\n\n"
        "Voici une question pour tester tes connaissances :\n\n"
        "**Question :** Quelle est la différence entre `let` et `const` en JavaScript ?\n\n"
        "a) `let` ne peut pas être réassignée, `const` oui\n"
        "b) `const` ne peut pas être réassignée, `let` oui ✅\n"
        "c) Il n'y a pas de différence\n"
        "d) Les deux ne peuvent pas être réassignées\n\n"
        "Réponds avec la lettre de ton choix ! 🤗"
    )


def _reponse_exercice_aleatoire(user_id):
    import random
    exos = list(Exercice.objects())
    if not exos:
        return "Aucun exercice disponible pour le moment."
    e = random.choice(exos)
    lesson_link = ''
    if e.lesson:
        formation = Formation.objects(nom=e.cours.category).first() if e.cours else None
        if formation:
            lesson_link = f'\n➡ Cette notion est abordée dans la leçon **[>{e.lesson.titre}]({_lien_lecon(formation.slug, e.cours.slug, e.lesson.ordre)})**'
    return (
        f"💪 **Exercice suggéré**\n\n"
        f"👉 **{e.titre}** ({e.difficulte}) — +{e.points} XP\n\n"
        f"{e.enonce or 'Pas d\'énoncé disponible.'}"
        f"{lesson_link}\n\n"
        f"➡ [Ouvrir l'exercice →](/exercice/{e.id}/)"
    )


def _lien_lecon(formation_slug, cours_slug, lecon_ordre):
    return f'/cours/{formation_slug}/lecon/?module={cours_slug}&lecon={lecon_ordre}'


# ─────────────────────────────────────────────
#  GÉNÉRATEUR PRINCIPAL
# ─────────────────────────────────────────────

def generer_reponse(uid, question, formation_nom=None, lecon_actuelle=None,
                    niveau_etudiant=None, lecons_terminees=None):
    """
    Point d'entrée principal.
    
    uid              — ID utilisateur
    question         — texte de la question
    formation_nom    — matière en cours (ex: 'JavaScript')
    lecon_actuelle   — objet Lesson ou None
    niveau_etudiant  — 'debutant', 'intermediaire', 'avance' ou None
    lecons_terminees — liste d'ids de leçons terminées ou None
    """

    # ── Détection des commandes rapides ──
    q = question.lower().strip()
    if any(m in q for m in ['quiz', 'qcm', 'test']):
        return _reponse_quiz()
    if any(m in q for m in ['exercice', 'entraînement', 'pratique', "suggère"]):
        return _reponse_exercice_aleatoire(uid)

    # ── Déterminer la formation ──
    if not formation_nom:
        cours_list = Cours.objects(professor_id__ne=0)
        if cours_list:
            # Deviner depuis la progression
            prog = Progression.objects(user_id=uid, pourcentage__gt=0).order_by('-pourcentage').first()
            if prog and prog.cours:
                formation_nom = prog.cours.category
        if not formation_nom and cours_list:
            formation_nom = cours_list.first().category

    # ── Rechercher dans les leçons ──
    lecons_trouvees = _rechercher_lecons(formation_nom, question)
    
    if lecons_trouvees:
        return _reponse_avec_cours(question, lecons_trouvees, formation_nom,
                                    lecon_actuelle, niveau_etudiant, lecons_terminees)
    else:
        return _reponse_generale(question, formation_nom, lecon_actuelle)


# ─────────────────────────────────────────────
#  RÉPONSE AVEC CONTENU DES COURS
# ─────────────────────────────────────────────

def _reponse_avec_cours(question, lecons_trouvees, formation_nom,
                         lecon_actuelle, niveau_etudiant, lecons_terminees):
    # Meilleure leçon
    top = list(lecons_trouvees.values())[0]
    meilleure_lecon = top['lesson']
    cours = _trouver_cours_par_lesson(meilleure_lecon)
    formation_slug = ''
    if cours:
        f = Formation.objects(nom=cours.category).first()
        if f:
            formation_slug = f.slug

    # Nombre de leçons pertinentes
    nb_trouve = len(lecons_trouvees)

    # Extraire un extrait du contenu pour l'explication
    extrait = _extraire_extrait(meilleure_lecon.content or '', question, 400)

    # Réponse structurée
    lignes = []

    # 📖 Explication
    lignes.append(f'📖 **Explication**\n')
    if extrait:
        lignes.append(f'D\'après le cours "{meilleure_lecon.titre}" :\n')
        lignes.append(extrait + '\n')
    else:
        lignes.append(f'Cette notion est abordée dans la leçon **"{meilleure_lecon.titre}"**.\n')

    # 💻 Exemple de code (cherche un bloc code dans le contenu)
    code_block = _extraire_code(meilleure_lecon.content or '', question)
    if code_block:
        lignes.append(f'💻 **Exemple de code**\n{code_block}\n')

    # ⚠️ Erreurs fréquentes
    erreurs = _generer_erreurs(question, meilleure_lecon.titre)
    if erreurs:
        lignes.append(f'⚠️ **Erreurs fréquentes**\n{erreurs}\n')

    # 💡 Conseil pédagogique
    conseil = _generer_conseil(meilleure_lecon.titre, niveau_etudiant)
    if conseil:
        lignes.append(f'💡 **Conseil pédagogique**\n{conseil}\n')

    # 📚 Leçons recommandées
    lignes.append(f'📚 **Leçons de CodeMentor AI à revoir**\n')
    for lid, data in lecons_trouvees.items():
        l = data['lesson']
        slug = formation_slug
        if not slug and l.cours:
            f = Formation.objects(nom=l.cours.category).first()
            if f:
                slug = f.slug
        lien = _lien_lecon(slug, l.cours.slug, l.ordre) if slug and l.cours else '#'
        etat = ''
        if lecons_terminees and str(l.id) in lecons_terminees:
            etat = ' ✅'
        mots = ', '.join(data['matches'][:4])
        lignes.append(f'➡ [{l.titre}]({lien}) " pertinence: {data["score"],}"{etat}')
    lignes.append('')

    # Exercices associés à la meilleure leçon
    exos = _trouver_exos_par_lesson(meilleure_lecon)
    if exos:
        lignes.append(f'💪 **Exercices associés**\n')
        for e in exos:
            lignes.append(f'➡ [{e.titre}](/exercice/{e.id}/) — +{e.points} XP')
        lignes.append('')

    return '\n'.join(lignes)


# ─────────────────────────────────────────────
#  RÉPONSE GÉNÉRALE (hors cours)
# ─────────────────────────────────────────────

def _reponse_generale(question, formation_nom=None, lecon_actuelle=None):
    q = question.lower()

    # Réponses générales sur la programmation
    GENERAL = {
        'variable': (
            "📖 **Explication**\n"
            "Une variable est un conteneur qui permet de stocker une valeur en mémoire. "
            "Chaque variable a un nom unique et peut contenir différents types de données "
            "(nombres, textes, listes, etc.).\n\n"
            "💻 **Exemple de code**\n"
            "```js\n"
            "let age = 25;\n"
            "const nom = 'Alice';\n"
            "var ancienne = 'Évite var';\n"
            "console.log(age, nom);\n"
            "```\n\n"
            "⚠️ **Erreurs fréquentes**\n"
            "- Utiliser une variable sans la déclarer\n"
            "- Essayer de réassigner une constante (`const`)\n"
            "- Confondre `let` et `var` (portée différente)\n\n"
            "💡 **Conseil pédagogique**\n"
            "Privilégie `const` par défaut, utilise `let` uniquement quand la variable doit changer."
        ),
        'fonction': (
            "📖 **Explication**\n"
            "Une fonction est un bloc de code réutilisable qui effectue une tâche spécifique. "
            "Elle peut accepter des paramètres en entrée et retourner un résultat.\n\n"
            "💻 **Exemple de code**\n"
            "```js\n"
            "function saluer(nom) {\n"
            "  return 'Bonjour, ' + nom + ' !';\n"
            "}\n"
            "console.log(saluer('Alice')); // Bonjour, Alice !\n"
            "```\n\n"
            "⚠️ **Erreurs fréquentes**\n"
            "- Oublier le `return` (la fonction retourne `undefined`)\n"
            "- Confondre paramètre et argument\n"
            "- Noms de fonctions peu explicites\n\n"
            "💡 **Conseil pédagogique**\n"
            "Une fonction doit faire une seule chose. Si elle fait trop de choses, découpe-la."
        ),
        'promesse': (
            "📖 **Explication**\n"
            "Une promesse (Promise) est un objet qui représente l'achèvement ou l'échec "
            "d'une opération asynchrone. Elle peut être dans trois états :\n"
            "- **Pending** (en attente)\n"
            "- **Fulfilled** (résolue avec succès)\n"
            "- **Rejected** (échouée)\n\n"
            "💻 **Exemple de code**\n"
            "```js\n"
            "const promesse = new Promise((resolve, reject) => {\n"
            "  setTimeout(() => resolve('Terminé !'), 1000);\n"
            "});\n"
            "promesse.then(msg => console.log(msg));\n"
            "```\n\n"
            "⚠️ **Erreurs fréquentes**\n"
            "- Oublier de retourner la promesse dans une chaîne `.then()`\n"
            "- Ne pas gérer les erreurs avec `.catch()`\n"
            "- Créer un « callback hell » au lieu d'utiliser `async/await`\n\n"
            "💡 **Conseil pédagogique**\n"
            "Utilise `async/await` pour un code plus lisible. C'est du sucre syntaxique "
            "sur les promesses."
        ),
    }

    for mot_cle, rep in GENERAL.items():
        if mot_cle in q:
            return rep + '\n\n🔗 **Ressources complémentaires**\n' \
                   '➡ [MDN — ' + mot_cle.capitalize() + 's](https://developer.mozilla.org/fr/docs/Web/JavaScript/Reference/Global_Objects/' + mot_cle.capitalize() + ')\n' \
                   '➡ [Documentation officielle](https://developer.mozilla.org/fr/docs/Web/JavaScript/Guide)\n'

    # Réponse par défaut
    return (
        "📖 **Explication**\n"
        "Je n'ai pas trouvé de réponse spécifique dans les cours de CodeMentor AI pour cette question.\n\n"
        "💡 **Conseil pédagogique**\n"
        "Tu peux reformuler ta question ou essayer de chercher dans les cours disponibles "
        "sur la plateforme.\n\n"
        "📚 **Leçons de CodeMentor AI à revoir**\n"
        "➡ [Voir tous les cours](/cours/)\n\n"
        "🔗 **Ressources complémentaires**\n"
        "➡ [MDN Web Docs](https://developer.mozilla.org/fr/)\n"
        "➡ [Documentation officielle](https://developer.mozilla.org/fr/docs/Web/JavaScript/Guide)\n"
        "➡ [Tutoriels interactifs](https://www.codecademy.com/)\n\n"
        "**Astuce :** Si tu cherches une notion précise, essaie de taper son nom "
        "(ex: « fonction », « promesse », « variable »). 🤗"
    )


# ─────────────────────────────────────────────
#  AIDE — extraction depuis le contenu
# ─────────────────────────────────────────────

def _extraire_extrait(contenu, question, max_len=400):
    """Extrait le passage le plus pertinent du contenu markdown."""
    if not contenu:
        return ''
    clean = re.sub(r'```[\s\S]*?```', '', contenu)
    clean = re.sub(r'#{1,6}\s+', '', clean)
    clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean)
    clean = re.sub(r'\*([^*]+)\*', r'\1', clean)
    lignes = [l.strip() for l in clean.split('\n') if l.strip()]
    mots_question = set(_tokeniser(question))
    if not mots_question:
        return ' '.join(lignes[:3])[:max_len]

    # Trouver les lignes contenant le plus de mots de la question
    lignes_scored = []
    for i, ligne in enumerate(lignes):
        mots_ligne = set(_tokeniser(ligne))
        score = len(mots_question & mots_ligne)
        if score > 0:
            lignes_scored.append((score, i, ligne))
    lignes_scored.sort(key=lambda x: -x[0])
    meilleures = [l[2] for l in lignes_scored[:5]]
    return ' '.join(meilleures)[:max_len] if meilleures else ''


def _extraire_code(contenu, question):
    """Extrait un bloc de code pertinent du contenu."""
    if not contenu:
        return ''
    blocs = re.findall(r'```(\w*)\n(.*?)```', contenu, re.DOTALL)
    if not blocs:
        return ''
    mots_q = set(_tokeniser(question))
    scored = []
    for lang, code in blocs:
        mots_code = set(_tokeniser(code))
        score = len(mots_q & mots_code)
        scored.append((score, lang, code.strip()))
    scored.sort(key=lambda x: -x[0])
    if scored:
        _, lang, code = scored[0]
        return f'```{lang}\n{code}\n```'
    return ''


def _generer_erreurs(question, titre_lecon):
    """Génère des erreurs fréquentes génériques liées au sujet."""
    q = question.lower()
    t = titre_lecon.lower()
    if any(m in q + t for m in ['fonction', 'function', 'return']):
        return (
            "- Oublier le mot-clé `return` → la fonction retourne `undefined`\n"
            "- Appeler une fonction sans parenthèses → on passe la référence, pas le résultat\n"
            "- Déclarer une fonction à l'intérieur d'un bloc conditionnel"
        )
    if any(m in q + t for m in ['promesse', 'promise', 'async', 'await']):
        return (
            "- Oublier le `await` devant une promesse → on récupère une promesse, pas la valeur\n"
            "- Ne pas entourer de `try/catch` les appels `async`\n"
            "- Créer un enchaînement de `.then()` illisible"
        )
    if any(m in q + t for m in ['variable', 'let', 'const', 'var']):
        return (
            "- Utiliser `var` qui a une portée de fonction (préférer `let`/`const`)\n"
            "- Déclarer une variable sans l'initialiser\n"
            "- Essayer de réaffecter une constante `const`"
        )
    if any(m in q + t for m in ['boucle', 'for', 'while', 'loop']):
        return (
            "- Boucle infinie si la condition de sortie n'est jamais atteinte\n"
            "- Oublier l'incrémentation dans un `for`\n"
            "- Modifier un tableau pendant qu'on le parcourt"
        )
    return (
        "- Vérifie la syntaxe (parenthèses, accolades, points-virgules)\n"
        "- Assure-toi que les variables existent avant de les utiliser\n"
        "- Consulte les cours de la plateforme pour revoir les bases"
    )


def _generer_conseil(titre_lecon, niveau_etudiant):
    conseils_generaux = (
        "Pratique régulièrement avec les exercices associés à cette leçon. "
        "La programmation s'apprend en codant !"
    )
    if niveau_etudiant == 'debutant':
        return (
            "Ne saute pas les étapes. Assure-toi de bien comprendre chaque notion "
            "avant de passer à la suivante. Refais les exercices plusieurs fois si nécessaire."
        )
    if niveau_etudiant == 'intermediaire':
        return (
            "Essaie d'expliquer ce concept à quelqu'un d'autre — c'est le meilleur moyen "
            "de vérifier que tu l'as bien compris. Continue avec les exercices avancés."
        )
    if niveau_etudiant == 'avance':
        return (
            "Approfondis en lisant le code source de bibliothèques populaires qui utilisent "
            "ce concept. Tu peux aussi contribuer à des projets open source."
        )
    return conseils_generaux

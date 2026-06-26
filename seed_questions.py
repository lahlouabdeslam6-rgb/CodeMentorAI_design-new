import os, sys
sys.path.insert(0, os.path.dirname(__file__))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
import django; django.setup()
from core.models import QuestionExamen

formations = ['JavaScript', 'Python', 'Java', 'PHP', 'React', 'Laravel', 'C++']

QUESTIONS = {
    'JavaScript': {
        'debutant': [
            ("Quelle est la bonne façon de déclarer une variable en JavaScript ?", ["var x = 5;", "variable x = 5;", "int x = 5;", "x := 5;"], 0),
            ("Quelle méthode ajoute un élément à la fin d'un tableau ?", ["push()", "pop()", "shift()", "unshift()"], 0),
            ("Quel opérateur teste l'égalité stricte ?", ["===", "==", "=", "!="], 0),
            ("Comment écrire un commentaire sur une seule ligne ?", ["// commentaire", "/* commentaire */", "# commentaire", "-- commentaire"], 0),
            ("Quelle est la valeur de typeof null ?", ["object", "null", "undefined", "boolean"], 0),
        ],
        'intermediaire': [
            ("Quel mot-clé déclare une variable à portée de bloc ?", ["let", "var", "int", "global"], 0),
            ("Que retourne [1,2,3].map(x => x*2) ?", ["[2,4,6]", "[1,2,3,1,2,3]", "[1,4,9]", "undefined"], 0),
            ("Comment cloner un objet shallow ?", ["{...obj}", "clone(obj)", "obj.copy()", "Object.clone(obj)"], 0),
            ("Quelle est la différence entre null et undefined ?", ["null est assigné, undefined est par défaut", "ils sont identiques", "null est un nombre", "undefined est un objet"], 0),
            ("Que fait la méthode .reduce() ?", ["Réduit un tableau à une valeur", "Supprime des éléments", "Ajoute des éléments", "Trie le tableau"], 0),
        ],
        'avance': [
            ("Qu'est-ce qu'une closure ?", ["Fonction avec accès à la portée parente", "Fonction sans paramètres", "Fonction asynchrone", "Fonction fléchée"], 0),
            ("Que retourne Promise.all() ?", ["Une promesse résolue quand toutes le sont", "La première promesse résolue", "La dernière promesse", "Un tableau de promesses"], 0),
            ("Qu'est-ce que le hoisting ?", ["Les déclarations remontées en haut de la portée", "Une boucle infinie", "Un type de donnée", "Une méthode de tableau"], 0),
            ("Comment fonctionne le event loop ?", ["File d'attente des callbacks exécutée après la stack", "Exécution parallèle", "Exécution synchrone", "File d'attente prioritaire"], 0),
            ("Qu'est-ce qu'un Proxy en JS ?", ["Objet qui intercepte les opérations d'un autre objet", "Un serveur intermédiaire", "Une fonction de rappel", "Un type de promesse"], 0),
        ],
    },
    'Python': {
        'debutant': [
            ("Comment afficher du texte en Python ?", ["print()", "echo()", "console.log()", "write()"], 0),
            ("Quel type est mutable ?", ["list", "tuple", "str", "int"], 0),
            ("Comment définir une fonction ?", ["def ma_fonction():", "function ma_fonction():", "func ma_fonction():", "define ma_fonction():"], 0),
            ("Quelle structure pour une boucle ?", ["for i in range():", "foreach i in range():", "loop i in range():", "for i to range():"], 0),
            ("Quelle est la sortie de print(2 ** 3) ?", ["8", "6", "9", "5"], 0),
        ],
        'intermediaire': [
            ("Qu'est-ce qu'un décorateur ?", ["Fonction qui modifie une autre fonction", "Un type de données", "Une classe spéciale", "Un module"], 0),
            ("Comment gérer les exceptions ?", ["try/except", "try/catch", "try/finally", "try/error"], 0),
            ("Que fait len('abc') ?", ["Retourne 3", "Retourne 'abc'", "Retourne ['a','b','c']", "Retourne 0"], 0),
            ("Quelle est la différence entre liste et tuple ?", ["Liste mutable, tuple immuable", "Liste immuable, tuple mutable", "Pas de différence", "Tuple est plus lent"], 0),
            ("Que retourne {}.get('cle', 'def') ?", ["'def'", "{}", "None", "Erreur"], 0),
        ],
        'avance': [
            ("Qu'est-ce qu'un générateur ?", ["Fonction qui produit une séquence avec yield", "Une fonction lambda", "Un décorateur", "Un module standard"], 0),
            ("Comment fonctionne le GIL ?", ["Verrou global qui limite un thread à la fois", "Garantit la concurrence", "Accélère l'exécution", "Gère la mémoire"], 0),
            ("Qu'est-ce que la POO en Python ?", ["Classes, héritage, polymorphisme", "Uniquement des fonctions", "Pas de classes", "Du typage statique"], 0),
            ("Que fait @staticmethod ?", ["Définit une méthode statique", "Définit une classe", "Importe un module", "Crée une instance"], 0),
            ("Qu'est-ce que __init__ ?", ["Le constructeur d'une classe", "Le destructeur", "Un import", "Une méthode privée"], 0),
        ],
    },
    'Java': {
        'debutant': [
            ("Comment déclarer une classe en Java ?", ["class MaClasse {}", "Class MaClasse {}", "new MaClasse {}", "classe MaClasse {}"], 0),
            ("Quel est le point d'entrée d'un programme Java ?", ["public static void main(String[] args)", "public void main()", "static main()", "public main(String[] args)"], 0),
            ("Comment déclarer une variable entière ?", ["int x = 5;", "integer x = 5;", "x = 5;", "Int x = 5;"], 0),
            ("Quel mot-clé pour l'héritage ?", ["extends", "inherits", "implements", "super"], 0),
            ("Quelle structure pour une condition ?", ["if (x > 0) {}", "if x > 0 {}", "if x > 0 then {}", "when (x > 0) {}"], 0),
        ],
        'intermediaire': [
            ("Qu'est-ce qu'une interface ?", ["Contrat que les classes implémentent", "Une classe abstraite", "Un type primitif", "Une bibliothèque"], 0),
            ("Comment gérer les exceptions ?", ["try/catch/finally", "try/except", "try/finally", "catch/try"], 0),
            ("Quelle est la différence entre = et == ?", ["= affectation, == comparaison", "= comparaison, == affectation", "identique", "= déclaration, == affectation"], 0),
            ("Qu'est-ce que le polymorphisme ?", ["Même méthode, comportements différents", "Plusieurs classes", "Un type unique", "Une boucle"], 0),
            ("Que fait final sur une variable ?", ["Rend la constante immuable", "Supprime la variable", "La rend publique", "L'initialise à 0"], 0),
        ],
        'avance': [
            ("Qu'est-ce que le garbage collector ?", ["Libère automatiquement la mémoire inutilisée", "Nettoie le code", "Gère les threads", "Optimise les requêtes"], 0),
            ("Comment fonctionne synchronized ?", ["Verrouille l'accès à une méthode/bloc", "Exécute en parallèle", "Supprime les threads", "Met en pause le programme"], 0),
            ("Qu'est-ce qu'une annotation en Java ?", ["Métadonnée pour le compilateur", "Un commentaire", "Une variable", "Une classe"], 0),
            ("Que fait JVM ?", ["Exécute le bytecode Java", "Compile le code source", "Gère les fichiers", "Indexe la base de données"], 0),
            ("Qu'est-ce que Spring Boot ?", ["Framework d'applications Java", "Un IDE", "Une base de données", "Un serveur web"], 0),
        ],
    },
    'PHP': {
        'debutant': [
            ("Comment démarrer un script PHP ?", ["<?php", "<script>", "<?", "<?php ?>"], 0),
            ("Comment afficher du texte ?", ["echo 'texte';", "print('texte')", "write('texte')", "console.log('texte')"], 0),
            ("Comment déclarer une variable ?", ["$var = 'valeur';", "var = 'valeur';", "String var = 'valeur';", "v $var = 'valeur';"], 0),
            ("Quel symbole pour concaténer ?", [".", "+", "&", ","], 0),
            ("Comment définir une fonction ?", ["function maFonction() {}", "def maFonction() {}", "func maFonction() {}", "create function maFonction() {}"], 0),
        ],
        'intermediaire': [
            ("Qu'est-ce que PDO ?", ["Accès base de données sécurisé", "Un template", "Un framework", "Un type de variable"], 0),
            ("Comment démarrer une session ?", ["session_start()", "start_session()", "Session::start()", "session_begin()"], 0),
            ("Quelle superglobale pour $_GET ?", ["\$_GET['key']", "\$_POST['key']", "\$_REQUEST['key']", "\$_SERVER['key']"], 0),
            ("Que fait isset() ?", ["Vérifie si une variable existe", "Supprime une variable", "Définit une variable", "Compte les variables"], 0),
            ("Comment gérer les exceptions ?", ["try/catch", "try/except", "try/finally", "catch/try"], 0),
        ],
        'avance': [
            ("Qu'est-ce que Composer ?", ["Gestionnaire de dépendances PHP", "Un framework", "Un serveur", "Une base de données"], 0),
            ("Comment fonctionne l'autoloading ?", ["Charge automatiquement les classes", "Importe tous les fichiers", "Exécute au démarrage", "Compile le code"], 0),
            ("Qu'est-ce que MVC ?", ["Modèle-Vue-Contrôleur", "Un type de base de données", "Un serveur", "Une fonction"], 0),
            ("Que fait Laravel Eloquent ?", ["ORM pour interagir avec la BDD", "Un moteur de templates", "Un système de fichiers", "Un outil de debug"], 0),
            ("Qu'est-ce que le DI Container ?", ["Gère les dépendances des classes", "Stocke les données", "Affiche les erreurs", "Optimise les requêtes"], 0),
        ],
    },
    'React': {
        'debutant': [
            ("Qu'est-ce que JSX ?", ["Extension syntaxique JavaScript pour HTML", "Un type de fichier", "Une bibliothèque", "Un framework CSS"], 0),
            ("Comment créer un composant ?", ["function MonComp() { return <div/>; }", "class MonComp {}", "createComponent('MonComp')", "<MonComp/>"], 0),
            ("Qu'est-ce qu'un state ?", ["Donnée interne d'un composant", "Une variable globale", "Une fonction", "Un type de props"], 0),
            ("Comment importer un composant ?", ["import Comp from './Comp';", "require Comp from './Comp';", "include Comp from './Comp';", "use Comp from './Comp';"], 0),
            ("Quelle commande pour créer une app React ?", ["npx create-react-app", "npm react-app", "npx react init", "npm create react"], 0),
        ],
        'intermediaire': [
            ("Qu'est-ce que useState ?", ["Hook pour gérer l'état", "Un composant", "Une props", "Une méthode de cycle"], 0),
            ("Comment passer des données parent → enfant ?", ["Via les props", "Via le state", "Via le context", "Via refs"], 0),
            ("Qu'est-ce que useEffect ?", ["Hook pour les effets de bord", "Un gestionnaire d'état", "Un composant", "Une librairie"], 0),
            ("Que fait le Virtual DOM ?", ["Optimise les mises à jour du DOM réel", "Crée un DOM parallèle", "Supprime le DOM", "Ralentit le rendu"], 0),
            ("Quand utiliser useCallback ?", ["Mémoriser une fonction", "Mémoriser une valeur", "Gérer un formulaire", "Faire une requête API"], 0),
        ],
        'avance': [
            ("Qu'est-ce que Redux ?", ["Gestion d'état globale prévisible", "Un framework CSS", "Un compilateur", "Un serveur"], 0),
            ("Comment fonctionne le Context API ?", ["Partage des données sans props drilling", "Gère le routing", "Optimise le rendu", "Gère les formulaires"], 0),
            ("Qu'est-ce que Suspense ?", ["Gère le chargement asynchrone", "Un hook d'état", "Un composant HOC", "Une méthode de cycle"], 0),
            ("Que fait React.memo ?", ["Mémorise un composant pour éviter re-rendu", "Crée un composant", "Supprime un composant", "Clone un composant"], 0),
            ("Qu'est-ce que le code splitting ?", ["Divise le code en bundles chargés à la demande", "Sépare les fichiers CSS", "Divise les tests", "Optimise les images"], 0),
        ],
    },
    'Laravel': {
        'debutant': [
            ("Quelle commande crée un projet Laravel ?", ["composer create-project laravel/laravel", "npm create laravel", "php artisan new", "laravel new"], 0),
            ("Où sont définies les routes ?", ["routes/web.php", "config/routes.php", "app/routes.php", "views/routes.php"], 0),
            ("Quel moteur de templates ?", ["Blade", "Twig", "Smarty", "PHP pur"], 0),
            ("Comment créer un contrôleur ?", ["php artisan make:controller", "php create controller", "artisan new controller", "npm run controller"], 0),
            ("Qu'est-ce qu'une migration ?", ["Gère le schéma de la base de données", "Un fichier de config", "Un template", "Une route"], 0),
        ],
        'intermediaire': [
            ("Qu'est-ce que Eloquent ?", ["ORM de Laravel", "Un moteur de templates", "Un gestionnaire de fichiers", "Un outil de test"], 0),
            ("Comment valider des données ?", ["\$request->validate()", "\$this->check()", "\$data->verify()", "\$input->test()"], 0),
            ("Qu'est-ce que le service container ?", ["Gère les dépendances et injections", "Stocke les sessions", "Gère les routes", "Optimise les requêtes"], 0),
            ("Que fait php artisan migrate ?", ["Exécute les migrations", "Crée un modèle", "Lance le serveur", "Compile les assets"], 0),
            ("Comment définir une relation 1:N ?", ["hasMany() / belongsTo()", "hasOne() / hasMany()", "belongsTo() / belongsToMany()", "hasMany() / hasMany()"], 0),
        ],
        'avance': [
            ("Qu'est-ce que le Service Provider ?", ["Point d'entrée pour enregistrer des services", "Un type de route", "Un modèle", "Un contrôleur"], 0),
            ("Comment fonctionne le système d'events ?", ["Écoute et réagit aux événements de l'app", "Gère les requêtes HTTP", "Stocke les logs", "Optimise les vues"], 0),
            ("Qu'est-ce que le Eloquent Serialization ?", ["Convertit les modèles en JSON/tableaux", "Sauvegarde en base", "Affiche les vues", "Gère les sessions"], 0),
            ("Que sont les middlewares ?", ["Filtres appliqués avant les requêtes", "Des routes spéciales", "Des modèles", "Des contrôleurs"], 0),
            ("Qu'est-ce que le task scheduler ?", ["Planifie des tâches cron via Artisan", "Gère les files d'attente", "Optimise les requêtes", "Gère les événements"], 0),
        ],
    },
    'C++': {
        'debutant': [
            ("Comment inclure une bibliothèque ?", ["#include <iostream>", "import <iostream>", "using iostream;", "include <iostream>"], 0),
            ("Quel est le point d'entrée ?", ["int main() {}", "void main() {}", "main() {}", "public void main() {}"], 0),
            ("Comment afficher à l'écran ?", ["std::cout << texte;", "print(texte)", "echo texte", "console.log(texte)"], 0),
            ("Comment déclarer une variable entière ?", ["int x = 5;", "integer x = 5;", "x = 5;", "Int x = 5;"], 0),
            ("Qu'est-ce qu'un pointeur ?", ["Variable qui stocke une adresse mémoire", "Une référence", "Un type spécial", "Un entier long"], 0),
        ],
        'intermediaire': [
            ("Qu'est-ce qu'une classe ?", ["Modèle pour créer des objets", "Un type primitif", "Une fonction", "Une bibliothèque"], 0),
            ("Comment fonctionne l'héritage ?", ["class Fille : public Mere {}", "class Fille extends Mere {}", "class Fille inherits Mere {}", "Fille : Mere {}"], 0),
            ("Qu'est-ce que le polymorphisme ?", ["Même interface, comportements différents", "Plusieurs classes identiques", "Un type unique", "Une boucle spéciale"], 0),
            ("Que fait le mot-clé virtual ?", ["Permet la redéfinition dans les classes filles", "Rend la classe abstraite", "Supprime la méthode", "Optimise l'exécution"], 0),
            ("Comment gérer la mémoire dynamique ?", ["new et delete", "malloc et free", "alloc et dealloc", "create et destroy"], 0),
        ],
        'avance': [
            ("Qu'est-ce que le RAII ?", ["Ressource acquise à l'initialisation, libérée à la destruction", "Un type de pointeur", "Une bibliothèque", "Un mot-clé"], 0),
            ("Qu'est-ce qu'un template ?", ["Code générique pour types multiples", "Un modèle de classe", "Une macro", "Une fonction spéciale"], 0),
            ("Comment fonctionne le move semantics ?", ["Transfère les ressources sans copie", "Copie les données", "Supprime les données", "Échange les pointeurs"], 0),
            ("Que fait std::unique_ptr ?", ["Pointeur intelligent exclusif", "Pointeur partagé", "Pointeur brut", "Pointeur automatique"], 0),
            ("Qu'est-ce que le STL ?", ["Bibliothèque standard de templates et conteneurs", "Un compilateur", "Un IDE", "Un système de fichiers"], 0),
        ],
    },
}

existing = QuestionExamen.objects(formation_nom__ne='JavaScript').count()
if existing > 0:
    print(f'{existing} questions existantes avec formation_nom. Suppression...')
    QuestionExamen.objects(formation_nom__ne='JavaScript').delete()

count_js = QuestionExamen.objects(formation_nom='JavaScript').count()
print(f'{count_js} questions JavaScript existantes.')

nb_created = 0
for formation_nom, niveaux in QUESTIONS.items():
    for difficulte, qs in niveaux.items():
        for question, options, correct_idx in qs:
            q = QuestionExamen(formation_nom=formation_nom,
                                 question=question,
                                 options=options,
                                 reponse_correcte=correct_idx,
                                 difficulte=difficulte).save()
            nb_created += 1

print(f'{nb_created} questions créées au total.')
print('Seed questions terminé !')

---
name: gen-tests
description: A partir d'une spec Markdown, choisit les repos concernes (Horizon, Stream ou les deux), puis produit une matrice de tracabilite, un CSV de test cases importable dans Testiny et une fiche d'explication de la fonctionnalite. Utiliser avec /gen-tests <chemin-spec.md>.
---

# gen-tests

Entree : un fichier de spec Markdown. Les repos sont choisis automatiquement (etape 1).
Sortie : `out/<slug>/` contenant `feature.json` (source de verite), puis, generes par script :
`testiny.csv`, `matrice_tracabilite.csv`, `explication.md`.

Ne jamais ecrire les CSV a la main : ils sont produits par `scripts/export.py` a partir de `feature.json`.
Format de `feature.json` : `schema/FORMAT.md`. Registre des repos : `config/repos.json`.

## Etapes

1. **Lire la spec en entier**, choisir un `slug` court, extraire 5 a 10 mots-cles propres a la fonctionnalite (noms de champs, de commandes, d'endpoints, de concepts : ex. `claim`, `oidc`, `mapping`).
2. **Choisir les repos** :
   ```bash
   python3 scripts/select_repos.py <spec.md> --keywords mot1,mot2,mot3
   ```
   Le script croise la section Product Scope (cases cochees) et une recherche de mots-cles dans le code local. Interpreter le resultat :
   - Une fonctionnalite peut toucher Horizon, Stream ou les deux : garder tous les repos pertinents, ecarter ceux sans lien reel (lire quelques fichiers cites avant de decider).
   - `to_clone` ou `scope_without_repo` non vide : le dire a l'utilisateur et proposer `gh repo clone` a cote de qa-trace, puis mettre a jour `config/repos.json` (`status: local`). Ne pas deviner le comportement serveur a partir d'un client.
   - Les repos `e2e` servent a trouver les tests deja ecrits pour la fonctionnalite (eviter les doublons, reprendre le vocabulaire et les dossiers) ; ils ne definissent pas le comportement produit.
   - Ne jamais lire `../openssl` ni aucun fichier de cles, mots de passe ou `.env`.
   Annoncer en une ou deux lignes les repos retenus et pourquoi, puis continuer sans attendre sauf ambiguite reelle.
3. **Extraire les exigences** dans `requirements`. Reprendre les IDs de la spec (`US-1`, `FR-2`, `AC-3`, `ACT-1`). Pour le non-fonctionnel, creer `NFR-1`... (une exigence atomique chacune). Ne pas inventer d'exigence absente de la spec. `source` = section de la spec.
4. **Analyser le code** des repos retenus : pour chaque exigence, trouver classes, endpoints, validations, commandes CLI, tests e2e existants, et renseigner `code` avec `repo/chemin/fichier:ligne`. Verifier le comportement reel (valeurs par defaut, messages d'erreur, codes HTTP, noms de privileges) pour preciser les resultats attendus. Si le code contredit la spec, l'ecrire dans `findings`. Renseigner `repos` dans `feature.json`.
5. **Rediger l'explication** (`explanation`), en francais, pour quelqu'un qui ne connait pas la fonctionnalite :
   - `summary` : ce que fait la fonctionnalite (3 a 5 phrases).
   - `ecosystem_role` : sa place dans l'ecosysteme (composants, acteurs, amont et aval ; Horizon, Stream, CLI le cas echeant).
   - `example` : deroule numerote concret avec des personnages fictifs et des valeurs realistes (style : "Camille demande ... Horizon contacte ...").
   - `limits` : hors perimetre, limites volontaires.
6. **Concevoir les test cases** (`tests`) en privilegiant peu de tests riches plutot que beaucoup de tests fins. Les tests sont executes a la main : chaque test coute du temps de preparation.
   - **Un test = un scenario** qui enchaine plusieurs verifications autour d'une meme preparation (memes preconditions, meme configuration). Regrouper les variantes (valeurs limites, majuscules/minuscules, plusieurs utilisateurs) en etapes d'un seul test, pas en tests separes.
   - **Ne separer** que si la preparation, l'environnement, le role de l'utilisateur ou le domaine d'echec different (ex. droits d'acces, mise a niveau, import/export, performance, audit).
   - **Cible** : environ un test pour deux ou trois exigences, soit 10 a 20 tests pour une spec de taille moyenne ; au-dela, fusionner. Chaque FR, AC, NFR et ACT doit rester couvert par au moins un test (la validation le verifie).
   - Ne pas dupliquer ce que les tests unitaires du repo couvrent deja (mentionner la reference dans `code`), sauf pour le parcours utilisateur de bout en bout.
   - Un test = un objectif verifiable, relie a au moins une exigence (`req`). Couvrir : nominal, limites, erreurs, droits d'acces, compatibilite ascendante, import/export, regression sur le voisin hors perimetre.
   - Etapes : paires `[action, resultat attendu]`, valeurs concretes. Preconditions : phrases courtes, une par ligne logique (elles deviennent des puces).
   - `folder` : chemin separe par ` / ` (devient ` > ` dans Testiny). `priority` P1/P2/P3. `type` : Functional, Regression, Security, Performance, Usability. `automation` : Manual par defaut (Automatable ou Automated seulement sur demande).
   - Comportement non specifie : tag `needs-clarification` et entree dans `open_questions`. Ne pas inventer le resultat attendu.
   - Langue des tests : celle de la spec, sauf consigne contraire. Valeurs fictives uniquement.
7. **Valider puis exporter** :
   ```bash
   python3 scripts/export.py out/<slug>/feature.json
   ```
   Corriger `feature.json` jusqu'a zero erreur. Signaler les avertissements.
8. **Conclure** par un court resume : repos utilises, nombre d'exigences et de tests, trous de couverture, questions ouvertes, ecarts spec/code, repos manquants.

## Regles

- Faits (spec, code) et hypotheses restent separes : les hypotheses vont dans `open_questions`.
- Les documents produits sont des brouillons generes par IA : relecture humaine requise avant import dans Testiny.
- Ne pas modifier `config/testiny_mapping.json` sans demande.

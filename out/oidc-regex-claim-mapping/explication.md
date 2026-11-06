# Support regex matching for OIDC claim-to-Role/Team mapping

Horizon 2.12.0 | test.md

## Ce que fait la fonctionnalite

Horizon associe les valeurs d'un claim OIDC (par exemple la liste des groupes d'un utilisateur) a des Roles et des Teams. Jusqu'en 2.10, chaque valeur devait etre declaree dans une entree distincte, avec une egalite stricte. Cette fonctionnalite ajoute, par entree, un type de correspondance : Static (comportement actuel, egalite exacte) ou Regex (la valeur doit satisfaire l'expression reguliere sur toute sa longueur). Une seule entree peut ainsi couvrir tous les sous-groupes d'une arborescence. Lorsque plusieurs entrees correspondent a une valeur, l'utilisateur recoit l'union de leurs Roles et Teams.

## Son role dans l'ecosysteme

Le mapping de claims se situe au moment de la connexion : l'IdP externe (Keycloak, Entra ID, Okta...) emet un jeton contenant les groupes de l'utilisateur, Horizon-Core en extrait les valeurs, les compare aux entrees du mapping configure sur le fournisseur d'identite OIDC du tenant, et en deduit les Roles et Teams de la session. Ces Roles et Teams determinent ensuite ce que l'utilisateur peut faire (demander, renouveler, approuver, administrer) sur tous les modules. La fonctionnalite concerne le coeur de la plateforme (pas un module de licence pki, clm ou dcv). Le persona principal est l'administrateur metier, qui configure le mapping. Les comptes de service et le fournisseur d'identite local ne sont pas touches.

## Exemple d'utilisation

Le deroule

1. Camille, administratrice metier, configure le fournisseur OIDC du tenant dans Security, Access Management, Identity providers. Son annuaire contient les groupes app-team-frontend, app-team-backend et app-team-platform.
2. Avant 2.12, Camille devait creer trois entrees identiques, une par groupe, et en ajouter une a chaque nouveau sous-groupe.
3. Avec 2.12, elle ajoute une seule entree, choisit le type Regex, saisit la valeur app-team-.* et selectionne la Team Dev-Certificats.
4. Elle enregistre. Horizon verifie que l'expression est valide ; si elle avait saisi app-team-[, l'enregistrement serait refuse avec un message citant l'entree fautive.
5. Karim se connecte. Son jeton contient le groupe app-team-backend. Horizon compare la valeur a l'expression sur toute sa longueur : elle correspond, Karim obtient la Team Dev-Certificats.
6. Le mois suivant, l'IdP cree le groupe app-team-security. Sans aucune action de Camille, un utilisateur de ce groupe obtient la meme Team a sa prochaine connexion.
7. Un utilisateur du groupe x-app-team-frontend n'obtient rien : la correspondance porte sur la valeur entiere, pas sur un fragment.

## Limites et hors perimetre

- Une entree Regex cible uniquement des Roles et Teams existants et nommes explicitement ; le nom du Role ou de la Team ne peut pas etre deduit du texte capture.
- Pas de syntaxe glob (un simple *) : uniquement des expressions regulieres.
- Aucun changement a la regle d'extraction des valeurs, au fournisseur local, ni aux regles de claims des comptes de service.
- Un motif trop large peut sur-attribuer des droits : la validation a l'enregistrement controle la syntaxe, pas la pertinence metier du motif.

## Ecarts constates entre spec et code

- Le code (OidcClaimMapping.scala:22) fait une egalite stricte sur entry.claim : aucune notion de type de correspondance n'existe encore. La fonctionnalite est donc entierement a creer, la spec decrit bien l'etat actuel (comportement 'Static').
- Le code contient un mode de synchronisation (synchronizationMode : roles_teams, roles, teams) absent de la spec. En mode Replace, un utilisateur qui ne correspond plus a aucune entree perd ses Roles/Teams ; en mode roles, les entrees ne peuvent referencer aucune Team (et inversement). Les tests regex doivent couvrir ces modes (TC-07, NFR-5).
- Une entree doit referencer au moins un Role ou une Team (ClaimMappingEntry.scala) et 'mapping.entries' ne peut pas etre vide : cas limites a tester avec Regex (TC-05).
- Un Role ou une Team reference par une entree du mapping ne peut pas etre supprime (Role.scala:108, Team.scala:118). Ce garde-fou doit aussi valoir pour les entrees Regex (TC-05).
- Les erreurs de validation existantes (Role(s)/Team(s) referenced in claim mapping do not exist) citent les noms manquants mais pas l'entree ; la spec exige que l'erreur de regex nomme l'entree fautive (FR-6). Format du message a definir.
- Le dialecte de regex n'est pas fixe par la spec ; horizon etant en Scala/JVM, java.util.regex est le candidat naturel (a confirmer avec le Backend).

## Questions ouvertes

- ReDoS : quel mecanisme (timeout d'evaluation, moteur lineaire, limite de longueur du motif) et quelle limite ? (Technical Open Question 1 de la spec). Conditionne TC-14.
- Valeur de regex vide : rejet a l'enregistrement ou acceptation ? La spec ne le precise pas (TC-04).
- Dialecte de regex (Java, RE2, JavaScript) non precise : conditionne la syntaxe acceptee (flags inline, lookahead, classes Unicode).
- Seuils de performance au login non definis (TC-14).
- Mode de synchronisation : la spec ne le mentionne pas ; confirmer que le comportement Replace s'applique a l'identique aux entrees Regex (NFR-5).

---

Brouillon genere par IA, a relire par un humain avant diffusion ou import.

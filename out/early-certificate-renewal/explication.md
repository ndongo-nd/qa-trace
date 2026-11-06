# Allow manual certificate renewal outside the standard renewal period

Horizon 2.12.0 | Allow manual certificate renewal outside the standard renewal period.md

## Ce que fait la fonctionnalite

Aujourd'hui, Horizon refuse de renouveler un certificat géré tant que sa période de renouvellement n'est pas ouverte (erreur WEBRA-RENEW-005 « Certificate not in its renewal period »), et aucun opérateur ne peut forcer ce renouvellement. La fonctionnalité ajoute un renouvellement anticipé : un opérateur autorisé peut renouveler un certificat avant l'ouverture de sa fenêtre, seul ou en lot, depuis l'interface (inventaire RA, My Certificates) ou l'API REST. Seule la vérification de la période est levée : la validité et le statut du certificat restent contrôlés. Le certificat renouvelé reste sur le même profil et le même connecteur PKI, conserve ses métadonnées techniques tierces, et l'opération est tracée dans l'événement d'audit LIFECYCLE-RENEW.

## Son role dans l'ecosysteme

Le renouvellement est une action du cycle de vie (CLM) exécutée par Horizon-Core sur un certificat géré, en s'appuyant sur le profil, le connecteur PKI (DigiCert, Sectigo...) et les connecteurs tiers de déploiement (par exemple F5). Le renouvellement anticipé répond à deux situations opérationnelles : une révocation de masse décidée par une autorité de certification, où il faut réémettre des centaines de certificats immédiatement, et une migration de connecteur PKI, où l'on repointe le profil vers la nouvelle autorité puis on renouvelle d'un coup. Les acteurs concernés sont l'opérateur RA (acteur principal), l'administrateur métier (qui décide qui détient la capacité) et le service principal (scripts via l'API). Le renouvellement automatique, planifié ou en libre-service reste régi par la période de renouvellement. Les droits de renouvellement existent déjà par profil (renew, renew_api, request_renew, approve_renew) ; le choix du mécanisme d'autorisation du renouvellement anticipé est une question ouverte de la spec.

## Exemple d'utilisation

Le deroule

1. Une autorité de certification annonce la révocation prochaine d'un lot de certificats. Camille, opérateur RA, doit réémettre immédiatement 12 certificats du profil Web-Prod, dont aucun n'est encore dans sa fenêtre de renouvellement.
2. Camille ouvre l'inventaire des certificats dans Horizon RA, filtre sur le profil Web-Prod et l'émetteur concerné, puis coche les 12 certificats, comme elle le ferait pour une révocation en masse.
3. Elle choisit Renew et confirme explicitement qu'il s'agit d'un renouvellement anticipé.
4. Horizon traite chaque certificat indépendamment. Dix sont renouvelés sur le même profil et le même connecteur, avec le même DN, les mêmes SAN et les mêmes étiquettes. Un certificat est déjà révoqué : il est refusé avec la raison « révoqué », sans bloquer les autres. Un autre est déjà expiré et refusé de la même manière.
5. Les certificats renouvelés conservent leurs métadonnées techniques tierces : celui qui était déployé dans la partition F5 Common/prod sera redéployé au même endroit.
6. Plus tard, Louis, administrateur métier, consulte le journal d'audit : chaque événement LIFECYCLE-RENEW de Camille indique que le renouvellement a eu lieu hors période de renouvellement.
7. Un utilisateur final sans la capacité qui tente la même action sur son propre certificat est rejeté, et son certificat n'est pas renouvelé.

## Limites et hors perimetre

- Le renouvellement automatique ou planifié n'est pas modifié ; il reste gouverné par la période de renouvellement.
- Le profil et le connecteur PKI ne changent pas lors du renouvellement : pour migrer de connecteur, on repointe d'abord le profil puis on renouvelle.
- Pas de période de renouvellement distincte par connecteur.
- Un certificat révoqué, expiré ou non renouvelable le reste : seule la période est contournée.
- Pas de renouvellement anticipé en libre-service pour l'utilisateur final.
- Le mécanisme d'autorisation (réutiliser approve_renew avec approbation obligatoire, ou nouveau droit dédié) n'est pas tranché.

## Ecarts constates entre spec et code

- Un contournement de la période existe déjà dans le code : un certificat portant la métadonnée AUTOMATION_POLICY saute la vérification (WebRARenewRequest.scala:755-759). C'est le seul contournement actuel, conforme à la spec. Le renouvellement anticipé ne doit pas élargir ce contournement (TC-07).
- L'erreur WEBRA-RENEW-005 contient en détail la date de début de période (« period starts: ... ») ; elle est aussi listée dans RequestController.scala:56. Elle doit rester identique pour les non autorisés.
- Aucun renouvellement en lot n'existe côté interface : la révocation en lot existe (BulkMultipleRevocationPopup.vue, MultipleRevocation.vue, sélection dans MyCertificates.vue et SearchCertificates.vue) et sert de modèle, comme le dit la spec.
- Les droits de renouvellement existent par profil (renew, renew_api, request_renew, approve_renew : CertificateProfile.scala:188-253, LifecyclePermission.scala:36-39). Aucun droit de type renouvellement forcé n'existe.
- Les métadonnées de renouvellement générées ne contiennent que PKI_CONNECTOR et PREVIOUS_CERTIFICATE_ID (WebRARenewRequest.scala:990-994). La conservation des données tierces (Certificate.thirdPartyData) n'est pas visible dans ce fichier : à vérifier avec le Backend avant de valider TC-02.
- Un profil sans période de renouvellement suit une branche distincte (WebRARenewRequest.scala:293) : le comportement exact du refus « renouvellement non activé » est à confirmer pour TC-05.

## Questions ouvertes

- Mécanisme d'autorisation (Technical Open Question 1 de la spec) : réutiliser approve_renew avec approbation obligatoire, ou créer un droit dédié (par exemple renew_force) ? Conditionne ACT-1, ACT-3, TC-06 et TC-08.
- Le renouvellement anticipé exige-t-il toujours l'approbation d'un opérateur RA, en particulier en lot ? (même question ouverte)
- Forme de l'indicateur de renouvellement anticipé dans l'API (paramètre, en-tête, champ du corps) et format de la réponse pour plusieurs certificats.
- Format du rapport par certificat d'un renouvellement en lot et libellés d'interface (bouton, confirmation).
- Seuil de performance du renouvellement en lot et existence d'un indicateur de progression (NFR-2, TC-11).
- Traitement du certificat précédent (« standard renew handling ») : dépend du profil ; à confirmer pour le renouvellement anticipé.
- Les certificats en lot sans droit individuel : rejet par certificat ou rejet global ? (ACT-2 mentionne une autorisation par certificat).

---

Brouillon genere par IA, a relire par un humain avant diffusion ou import.

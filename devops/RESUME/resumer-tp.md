# DevOps et Cloud Computing — Résumé des TD et TP

Mise à jour du 24 novembre 2026. Méthodes de résolution, étapes pratiques et pièges des travaux dirigés et pratiques. Le [résumé des cours](resumer.md) conserve les chapitres théoriques. Les ajouts pédagogiques sont distingués des observations présentes dans les supports.

## TP1 et TP2 — Ce qu'il faut savoir expliquer

### TP1 : VM locale, réseau, SSH et snapshot

Le laboratoire demande deux VM Linux, l'allocation de vCPU/RAM/disque, une duplication avec identités distinctes, des communications entre hôte et invités, puis un retour à un snapshot. Le nom affiché par l'hyperviseur peut différer du hostname interne.

| Mode réseau | Communication typique | Point à retenir |
| --- | --- | --- |
| NAT | Sortie via traduction d'adresses | Une entrée depuis l'extérieur demande généralement une redirection |
| Bridged | VM participante du réseau local | Adressage et filtrage du LAN s'appliquent |
| Host-only | Hôte et VM sur un réseau privé | Pas d'accès Internet par défaut |
| Réseau interne | VM entre elles | Hôte non connecté directement par défaut |

Ces descriptions ne constituent pas une garantie de sécurité ; les règles de filtrage et la configuration réelle restent à vérifier.

```sh
hostname
whoami
ip a
sudo systemctl status ssh
ssh utilisateur@ADRESSE_VM
```

Les trois premières commandes permettent d'identifier la machine distante. `ssh localhost` teste le serveur local, sans prouver que le réseau entre machines fonctionne. Après restauration du snapshot, constater l'état réel du système ; arrêter un service n'est pas la même chose que restaurer un état antérieur.

### TP2 : VM IaaS et serveur web

Chaîne à comprendre : choisir image/région/taille → créer la VM → restreindre les accès réseau → se connecter en SSH → installer Nginx → vérifier le service et l'accès HTTP → contrôler les ressources restantes.

```sh
sudo apt update
sudo apt install -y nginx
sudo systemctl enable --now nginx
sudo systemctl status nginx --no-pager
curl -I http://localhost
```

Un service actif localement peut rester inaccessible depuis un navigateur à cause du pare-feu, du réseau ou d'une mauvaise adresse. Le TP demande SSH depuis l'IP autorisée et HTTP selon la règle de l'enseignante. Arrêter une VM peut laisser des disques, adresses ou snapshots facturables : vérifier les ressources effectivement créées.

Cette section résume les énoncés ; elle ne prétend pas qu'un nouveau déploiement cloud a été effectué pour rédiger cette fiche.

## TP3 et TP4 — Codespaces et OpenStack

### TP3 : environnement de développement GitHub Codespaces

Le sujet porte le titre « TP2 » mais est distribué comme TP3. Chaîne : créer un dépôt → ouvrir un Codespace 2 cœurs → explorer Linux (`whoami`, `hostname`, `uname -a`, `df -h`, `free -h`, `uptime`) → installer et lancer Nginx → exposer le port 80 par redirection de port → observer l'usage → arrêter ou supprimer le Codespace.

```sh
sudo apt-get update
sudo apt-get install -y nginx
sudo nginx
curl -I http://localhost
```

| Caractéristique cloud | Observation dans Codespaces |
| --- | --- |
| Libre-service à la demande | Création du Codespace sans intervention humaine |
| Accès réseau large | Éditeur et page Nginx accessibles depuis un navigateur |
| Mutualisation | Matériel, hyperviseur et réseau gérés par GitHub |
| Provisionnement rapide | Environnement prêt en quelques minutes ; type de machine modifiable |
| Service mesuré | Page de facturation : heures-cœur et Go-mois de stockage |

Le port redirigé reste **privé** sauf demande explicite. Un Codespace arrêté ne consomme plus de calcul, mais son stockage reste compté : supprimer ceux qui ne servent plus.

### TP4 : installation d'OpenStack avec DevStack

Sur Ubuntu Server 24.04 dédiée (recommandation de classe : 4 vCPU, 16 Go RAM, 80 Go disque, virtualisation imbriquée si possible) : mettre à jour le système → créer l'utilisateur `stack` avec sudo sans mot de passe → cloner DevStack → écrire `local.conf` → lancer `./stack.sh` en tant que `stack`, jamais avec sudo.

```sh
source openrc admin admin
openstack service list
openstack image list
openstack network list
```

| Composant | Rôle |
| --- | --- |
| Keystone | Identité et authentification |
| Nova | Instances de calcul |
| Neutron | Réseaux, sous-réseaux, routage, groupes de sécurité |
| Glance | Images de VM |
| Cinder | Volumes bloc |
| Horizon | Tableau de bord web (`http://<IP>/dashboard`) |
| Placement | Inventaire et allocation des ressources de calcul |

DevStack sert au développement et à l'enseignement, pas à la production : il modifie la configuration système et réseau.

## TD1 — Architecture, stockage et services

### Plateforme de commerce en ligne

Une architecture en couches sépare interface utilisateur, traitement métier et persistance. Le **back end** comprend les services côté serveur ; la logique métier et l'accès aux données en font partie, ce ne sont pas nécessairement quatre serveurs distincts.

| Couche / ressource | Proposition pour le cas du TD | Justification |
| --- | --- | --- |
| Front end | Interface web | Interaction avec les utilisateurs |
| Logique métier | Commandes et paiements | Règles et traitements applicatifs |
| Données structurées | Base relationnelle, telle que RDS dans l'exemple AWS | Relations, intégrité et transactions |
| Images | Stockage objet, tel que S3 dans l'exemple | Stockage et distribution de fichiers avec métadonnées |

Le besoin de 50 000 utilisateurs simultanés exige un dimensionnement et des mesures ; ce nombre seul ne permet pas de déduire une taille de VM. La disponibilité nécessite plusieurs instances, un routage vers les instances saines et une stratégie de reprise des données. Une sauvegarde permet une restauration ; elle ne remplace pas un basculement automatique.

Les microservices permettent de faire évoluer certains composants séparément, mais ajoutent échanges réseau et exploitation distribuée. Leur choix doit être justifié par les besoins et l'équipe ; plusieurs fonctions métier ne rendent pas un monolithe automatiquement inadapté.

### Ressources virtuelles et contention

Pour trois départements, une VM par département fournit une séparation logique sur le serveur physique. L'hyperviseur attribue et ordonnance les ressources. Un invité trop consommateur peut dégrader les autres : prévoir limites, réservations et surveillance adaptées. La panne du seul hôte reste un risque commun.

**Migration** : déplacer une VM vers un autre hôte. **Réplication** : maintenir une copie selon la stratégie prévue, utilisable notamment pour une reprise. Une copie ne reste pas synchronisée spontanément ; il faut un mécanisme de réplication.

### Stockage fichier, objet, bloc et VFS

| Notion | Fonction |
| --- | --- |
| Partage de fichiers | Accès à une arborescence avec un protocole et des droits |
| SMB / NFS | Protocoles de partage de fichiers, fréquemment associés à Windows / Unix mais pas exclusifs à ces OS |
| Stockage objet | Accès à des objets identifiés, avec données et métadonnées |
| Stockage bloc | Volumes vus comme blocs par un système, qui peut y créer un système de fichiers |
| VFS | Abstraction d'accès aux systèmes de fichiers au niveau du système d'exploitation |

Pour des postes Windows et Linux, vérifier le protocole, les clients, les identités et les permissions réellement compatibles. Dire seulement « virtualisation de fichiers » ne résout pas ces exigences. Un VFS n'est pas une garantie automatique de chemins réseau identiques après déplacement des fichiers.

Le stockage objet convient au scénario d'images proposé ; le choix final dépend aussi des applications et contraintes d'accès. Pour protéger les données, distinguer **accès non autorisé** (identités, autorisations, chiffrement) et **perte de données** (sauvegardes, versions, réplication et essais de restauration). Un pare-feu ou le chiffrement ne suffit pas à restaurer des données effacées.

### FaaS et traitement d'images

Le traitement événementiel peut suivre : dépôt de l'image dans un stockage → notification de création d'objet → fonction de traitement → résultat stocké. Le déclencheur cloud est l'événement configuré après le dépôt, pas le simple clic sur un bouton de l'interface.

Le modèle FaaS évite de gérer directement les serveurs d'exécution. Le coût dépend de la tarification du service, notamment invocations, durée et ressources, avec d'autres coûts possibles ; il n'est pas limité universellement au seul temps d'exécution. Le cold start peut ajouter de la latence ; une capacité préinitialisée, quand le service la propose, constitue un compromis de coût et de délai. Le TD ne fournit pas de tarifs à mémoriser.

### SOA, SOAP et REST

Des services Java, Python et Node.js peuvent coopérer grâce à des contrats d'interface et des formats/protocoles communs. Le couplage faible limite certaines dépendances ; il ne signifie pas absence de dépendances.

**SOAP** est un protocole de messages utilisant XML. **REST** est un style d'architecture fondé notamment sur des ressources et des interactions définies ; REST n'impose pas JSON, même si ce format est courant dans les exemples web.

Une panne de notification ne doit pas nécessairement arrêter un paiement, mais cela dépend de l'implémentation. Une notification asynchrone avec reprise et gestion des erreurs limite la propagation ; un appel synchrone mal géré peut au contraire bloquer le flux. L'indépendance annoncée dans un schéma ne suffit pas à garantir la résilience.

## Révision active — Pratique

5. **Pourquoi comparer curl local et accès navigateur distant ?** Ils ne testent pas le même chemin réseau.

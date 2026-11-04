# Internet of Things — Résumé de révision

Synthèse du chapitre 1 et du TD1 disponibles au 4 novembre 2026. Enseignante : Ameur Imane. Le cours annonce des protocoles approfondis au chapitre 2, mais aucun fichier de ce chapitre n'est actuellement présent ; la fiche reste centrée sur l'introduction fournie.

## Chapitre 1 — Définition, objets et chaîne de valeur

### Définir l'IoT

L'**Internet des objets** relie des objets physiques identifiables, dotés de capacités de mesure, de traitement et de communication, à des services qui exploitent leurs données ou commandent leurs actions. L'IoT est un concept et un écosystème, pas un appareil ou une technologie radio unique.

Trois visions se complètent : **Things** identifie les objets, **Internet** les relie et **Semantic** donne un sens partagé à leurs données. Une mesure sans identité, unité ou contexte peut être difficile à interpréter.

| Bloc | Fonction | Exemple |
| --- | --- | --- |
| Capteur / actionneur | Mesurer / agir | Humidité du sol / vanne |
| Calcul et mémoire | Exécuter le firmware et traiter | Microcontrôleur |
| Communication | Échanger des données et commandes | Radio ou interface filaire |
| Alimentation | Fournir l'énergie | Batterie, secteur ou énergie récupérée |

Le firmware est le logiciel de l'objet. Un objet connecté peut échanger ; un objet dit intelligent ajoute une logique de traitement ou d'adaptation. Une intelligence peut être locale ou distante : ces deux notions ne sont donc pas synonymes.

### De la mesure à l'action

```text
Mesure → transmission → stockage / traitement → analyse → décision → action
```

Exemple d'irrigation : 32 % est une donnée ; « sol sec à cet endroit » est une information contextualisée ; « irrigation nécessaire » résulte d'une règle ou d'une analyse ; ouvrir la vanne est l'action. L'intérêt du système vient du service rendu, pas de l'accumulation de mesures seule.

Un identifiant peut être MAC, IP, EPC/RFID, URI ou identifiant applicatif selon la couche. Un objet derrière une passerelle n'a pas nécessairement sa propre adresse IP publique. Le cloud est une option d'architecture, pas une obligation pour toute décision IoT.

## Chapitre 1 — Huit caractéristiques et contraintes

| Caractéristique | Sens | Exemple : caméras urbaines |
| --- | --- | --- |
| Connectivité | Échanges réseau | Envoi d'événements à une plateforme |
| Identification | Reconnaître la source | Identifiant de chaque caméra |
| Perception | Mesure du monde | Capture d'image ou de mouvement |
| Intelligence | Traitement utile | Détection d'événements |
| Hétérogénéité | Matériels et protocoles variés | Marques et réseaux différents |
| Scalabilité | Gérer la croissance | Passer de 500 à davantage de caméras |
| Autonomie | Fonctionner sans intervention constante | Redémarrage ou configuration automatiques |
| Sécurité | Protéger objets et échanges | Contrôle d'accès et mises à jour |

La mobilité et les arrivées/départs d'objets rendent le système dynamique. Une passerelle peut agréger et traduire certains protocoles pour relier des équipements hétérogènes.

Les limites de CPU, RAM, énergie, débit et coût orientent le design. Elles favorisent protocoles légers, transmissions adaptées et périodes de sommeil. Les valeurs matérielles du cours sont des exemples, pas une définition de tous les objets connectés.

## Chapitre 1 — M2M et domaines d'application

### M2M ou IoT ?

Le **M2M** désigne des échanges entre machines, souvent organisés autour d'un service dédié. Dans la comparaison pédagogique du cours, l'IoT étend cette logique à un écosystème de services et de données réutilisées.

| Critère | M2M classique du cours | IoT |
| --- | --- | --- |
| Organisation | Solution verticale dédiée | Plateforme partageant des données et services |
| Interconnexion | Souvent propriétaire | Combinaison de réseaux et d'interfaces |
| Exploitation des données | Usage ciblé | Plusieurs applications et analyses |
| Exemple | Compteur vers serveur de facturation | Compteur vers plateforme et applications multiples |

Il s'agit de tendances d'architecture : les catégories peuvent se recouvrir. La présence d'une liaison cellulaire ne suffit pas à trancher ; examiner qui échange, avec quelle plateforme et pour quels usages.

### Domaines et contraintes dominantes

| Domaine | Scénario | Contrainte à justifier |
| --- | --- | --- |
| Maison | Présence → éclairage automatisé | Vie privée et compatibilité |
| Ville | Capteurs → disponibilité du stationnement | Déploiement à grande échelle |
| Santé connectée | Mesure → alerte et suivi | Fiabilité, confidentialité et délai |
| Agriculture | Humidité → irrigation | Portée radio et autonomie |
| Industrie | Vibrations → maintenance prédictive | Robustesse, continuité et temps de réponse |
| Transport / énergie | Suivi de flotte ou compteurs | Couverture, mobilité et volumes de données |

La même architecture ne convient pas à tous les domaines. Un dispositif sur batterie privilégie l'autonomie ; une commande industrielle peut d'abord exiger un délai maîtrisé.

## Chapitre 1 — WSN, cloud, edge et analyse

### Réseaux de capteurs sans fil

Un **WSN** regroupe des nœuds capteurs qui mesurent, traitent et transmettent. Un nœud peut aussi relayer les messages de ses voisins vers un collecteur, le **sink**, puis une passerelle vers d'autres services.

```text
Capteur → traitement local → un ou plusieurs sauts radio → sink → passerelle
```

| Topologie | Avantage | Limite |
| --- | --- | --- |
| Étoile | Simple, collecte directe | Dépendance au centre et à sa portée |
| Arbre | Organisation hiérarchique | Dépendance aux branches et relais |
| Maillage | Chemins alternatifs possibles | Routage et gestion énergétique plus complexes |

### IaaS, PaaS et SaaS

**IaaS** fournit des ressources d'infrastructure ; le client gère notamment OS et applications. **PaaS** fournit une plateforme pour le code ; **SaaS** fournit une application utilisable. Pour l'IoT, ces services peuvent faciliter stockage, calcul et tableaux de bord. Le choix ne supprime pas la responsabilité sur les accès et les données.

### Edge, fog et cloud

L'edge traite sur l'objet ou à proximité ; le fog organise des traitements intermédiaires ; le cloud apporte stockage et analyse globale. Traiter localement réduit certaines transmissions et peut permettre un service en cas de coupure. Cela demande aussi ressources locales, maintenance et cohérence de données.

### Big Data : les cinq V

| V | Sens | Exemple IoT |
| --- | --- | --- |
| Volume | Quantité | Historique de milliers de capteurs |
| Velocity | Vitesse d'arrivée | Flux continus de mesures |
| Variety | Diversité | Images, positions, températures et événements |
| Veracity | Fiabilité | Capteur mal calibré ou mesure manquante |
| Value | Utilité | Réduction d'une panne ou d'une consommation |

Les analyses sont **descriptives** (ce qui s'est passé), **diagnostiques** (pourquoi), **prédictives** (ce qui pourrait se passer) ou **prescriptives** (quelle action choisir).

## Chapitre 1 — Protocoles et conception embarquée

### Choisir une communication

Le choix combine portée, débit, énergie, mobilité, topologie et environnement. Les noms de technologies ne suffisent pas à déterminer la performance d'une installation.

| Besoin | Technologie évoquée par le cours |
| --- | --- |
| Proximité et basse consommation | Bluetooth LE |
| Débit élevé, alimentation adaptée | Wi-Fi ou Ethernet |
| Réseau domestique maillé | Zigbee ou Thread |
| Faible débit, longue portée, autonomie | LoRaWAN |
| Mobilité et couverture opérateur | Technologies cellulaires selon le besoin |

Le NFC correspond à une très courte portée. Toutes les communications BLE ne sont pas des réseaux maillés. Le choix d'une radio et celui du protocole applicatif sont deux décisions différentes.

Pile simplifiée : application **HTTP / MQTT / CoAP** → transport **TCP / UDP** → réseau **IP et adaptations** → liaison / support physique. Le support cite IPv6 et 6LoWPAN ; les détails des protocoles sont annoncés pour la suite, sans être développés ici.

### Système embarqué et temps réel

Un système embarqué réalise une fonction dédiée avec des contraintes de mémoire, calcul, énergie, taille ou délai. Il peut être bare metal ou utiliser un RTOS. Une exigence **temps réel dur** traite le retard comme une défaillance ; en **temps réel souple**, le retard dégrade le service. Temps réel ne veut pas seulement dire « rapide ».

### Top-down, bottom-up et codesign

Top-down part des besoins pour choisir architecture et composants ; bottom-up construit à partir de composants disponibles ; une approche mixte fait converger les deux. Le **codesign matériel/logiciel** partitionne les fonctions puis les développe et les intègre avec des itérations.

Pour un bracelet connecté : capteur et conversion en matériel ; filtrage, règles et protocole en logiciel ; accélération cryptographique matérielle si les contraintes le justifient. La répartition cherche un compromis de performance, consommation, coût et évolutivité ; elle n'impose pas toute fonction rapide en matériel.

## Chapitre 1 — Défis, fiabilité et protection

| Défi | Conséquence d'une mauvaise prise en compte | Réponse de conception évoquée |
| --- | --- | --- |
| Sécurité | Contrôle non autorisé ou compromission | Authentification, protection des échanges et mises à jour |
| Vie privée | Déduction d'habitudes ou exposition de données | Limiter la collecte et les accès |
| Interopérabilité | Silos et intégration difficile | Interfaces et sémantique partagées |
| Énergie | Batterie épuisée trop tôt | Veille et transmissions adaptées |
| Scalabilité | Saturation réseau, calcul ou stockage | Architecture et traitement de proximité |
| Fiabilité | Pertes de données ou d'actions | Reconnexion, surveillance et reprise |

Le cours utilise **Mirai, 2016**, comme exemple d'appareils insuffisamment protégés enrôlés pour un déni de service distribué. La leçon est de gérer les identifiants, les accès et la durée de maintenance du firmware ; le chiffrement seul ne corrige pas une authentification faible.

La fiabilité et la confidentialité doivent être examinées à chaque niveau : objet, liaison, passerelle, plateforme et application. Une passerelle commune peut aussi devenir une dépendance critique.

## TD1 — Méthodes de réponse et fiche de calcul

### Démarche pour un cas concret

1. Définir l'objet et le service attendu.
2. Identifier capteurs, actionneurs, calcul, communication et énergie.
3. Dessiner le parcours de la donnée et le retour de commande.
4. Justifier technologie et emplacement de traitement avec une contrainte dominante.
5. Expliquer sécurité, panne et évolution du nombre d'objets.

Une ampoule mesurant sa consommation possède une fonction de mesure électrique ; l'éclairage commandé est l'action. Une flotte de vélos alimentant plusieurs applications illustre l'écosystème IoT ; un distributeur envoyant une alerte au fournisseur illustre M2M et peut aussi appartenir à une plateforme IoT.

### Autonomie théorique de la station météo

```text
Capacité = 3 000 mAh
Courant moyen = 0,15 mA
Autonomie = capacité / courant = 20 000 h
Autonomie_années = 20 000 / 8 760 ≈ 2,28 ans
```

Le calcul suppose le courant moyen représentatif et toute la capacité utilisable. Vieillissement, température, autodécharge et pertes réduisent souvent l'autonomie réelle. Il faut distinguer courant actif, courant de veille et moyenne sur le cycle.

### Questions avec réponses courtes

1. **IoT impose-t-il du cloud ?** Non, des décisions peuvent être locales.
2. **Le sink est-il un capteur particulier de température ?** Non, c'est un rôle de collecte dans le réseau.
3. **Pourquoi MQTT et Wi-Fi ne sont-ils pas deux alternatives du même niveau ?** Le premier est applicatif, le second concerne l'accès réseau.
4. **Quelle contrainte pour un airbag ?** Temps réel dur dans le scénario étudié.
5. **Quel V concerne des mesures peu fiables ?** Veracity.
6. **Que faut-il justifier pour choisir LoRaWAN ?** Besoin de portée et d'autonomie, avec un débit compatible.
7. **Pourquoi la batterie seule ne donne-t-elle pas l'autonomie ?** Il faut connaître le courant moyen et les conditions d'utilisation.

Sources : `COURS/IOT Course 1.pdf` (86 pages : définitions p. 5–29, caractéristiques p. 30–35, M2M p. 36–41, applications p. 42–55, technologies p. 56–72, défis p. 73–85) et `TD/TD1_IoT.pdf` (2 pages). Les projections de marché et débits publicitaires ne sont pas repris comme faits de révision.

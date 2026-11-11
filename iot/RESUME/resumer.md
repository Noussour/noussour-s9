# Internet of Things — Résumé de révision

Synthèse du chapitre 1 et des TD1 et TD2 disponibles au 7 novembre 2026. Enseignante : Ameur Imane. Le cours annonce des protocoles approfondis au chapitre 2, mais aucun fichier de ce chapitre n'est actuellement présent ; la fiche reste centrée sur l'introduction et les exercices fournis.

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

## Chapitre 2 — Architecture d'un nœud IoT

### Blocs matériels

| Bloc | Rôle | Exemples |
| --- | --- | --- |
| Capteurs | Mesurer l'environnement | Température, humidité, lumière, mouvement |
| Microcontrôleur | Lire, traiter, décider | CPU, Flash, RAM, GPIO, ADC |
| Actionneurs (via driver) | Agir sur le monde physique | Moteur, relais, pompe, buzzer |
| Connectivité | Relier à la passerelle et au cloud | Wi-Fi, BLE, LoRa, Zigbee |
| Alimentation | Alimenter tous les blocs | Batterie, secteur, solaire |

Modèle à retenir : **SENSE → PROCESS → COMMUNICATE → ACT**. Les données montent vers le cloud ; les commandes redescendent vers les actionneurs.

### Capteurs

Chaîne : grandeur physique → transducteur → conditionnement → ADC → valeur numérique.

| Analogique | Numérique |
| --- | --- |
| Tension continue (ex. 0–3,3 V), ADC nécessaire | Données discrètes, traitement interne |
| LM35, LDR, humidité du sol, MQ-2 | DHT22, BME280, DS18B20 (I²C, SPI, UART, 1-Wire) |

Caractéristiques : étendue, sensibilité, exactitude, résolution, temps de réponse, consommation. **Exactitude ≠ fidélité** : un capteur répétable peut rester faux et demander un étalonnage.

### Actionneurs

Ils convertissent une commande en effet physique : LED (lumière), moteur (rotation), relais (commutation), buzzer (son), pompe, vanne. Ne jamais piloter un moteur ou un relais directement par une broche GPIO : utiliser un driver et une diode de roue libre.

## Chapitre 2 — Microcontrôleurs et connectivité

| Carte | Cœur | Connectivité | Usage |
| --- | --- | --- | --- |
| Arduino Uno | ATmega328P, 8 bits, 16 MHz | Aucune | Apprentissage |
| ESP32 | Double cœur 32 bits, 240 MHz | Wi-Fi + Bluetooth | La plupart des projets IoT |
| Raspberry Pi Pico W | RP2040, 133 MHz | Wi-Fi | Bas coût, MicroPython |
| STM32 | ARM Cortex-M 32 bits | Par modules | Industriel, basse consommation |
| Raspberry Pi 4 | Microprocesseur, Linux | Wi-Fi, Ethernet, BT | Passerelle, vision, IA en périphérie |

Interfaces : **GPIO** (entrée/sortie numérique), **ADC** (tension → nombre), **PWM** (puissance moyenne : luminosité, vitesse moteur), **I²C** (SDA + SCL, bus partagé), **SPI** (MOSI, MISO, SCLK, CS, rapide), **UART** (TX/RX, point à point : GPS, GSM).

| Technologie | Profil | Cas typique |
| --- | --- | --- |
| Wi-Fi | Débit élevé, portée locale | Maison, caméra |
| BLE | Courte portée, très basse consommation | Montre, bracelet |
| Zigbee | Maillage basse consommation | Maison connectée, nombreux capteurs |
| LoRa / LoRaWAN | Longue portée, faible débit | Capteur agricole à plusieurs km |
| NB-IoT | Cellulaire basse consommation | Compteurs |
| 4G / 5G | Grande zone, débit élevé | Véhicules, vidéo |

Exemple fil rouge : capteur d'humidité du sol + ESP32 ; si humidité < 30 % alors relais → pompe ON, sinon OFF ; mesures envoyées par MQTT vers un tableau de bord. Le simulateur Wokwi permet de tester ESP32, Arduino et STM32 sans matériel.

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

## TD2 — Composants, acquisition et énergie

### Identifier les blocs d'un système

Pour ESP32 + DHT22 + LED + Wi-Fi : le DHT22 mesure température et humidité (entrée), l'ESP32 traite, la LED matérialise une sortie et le Wi-Fi assure la communication. L'alimentation fournit l'énergie à l'ensemble. Le schéma fonctionnel devient : capteur → MCU → décision → LED, avec échanges réseau vers le service.

| Composant | Grandeur / événement | Nature de l'information utile |
| --- | --- | --- |
| DHT22 | Température et humidité | Mesures codées numériquement |
| LDR | Éclairement | Variation de résistance, convertie en tension dans un montage analogique |
| PIR | Mouvement détecté par variation infrarouge | Signal de détection généralement numérique sur le module étudié |
| HC-SR04 | Distance | Durée d'une impulsion numérique à mesurer, pas directement un nombre de mètres |
| MQ-2 | Réponse à certains gaz / fumée | Sortie analogique, et éventuellement sortie à seuil sur un module équipé |

Le type de module et son interface doivent être identifiés avant de programmer l'acquisition. Un capteur de mouvement ne garantit pas la détection d'une présence immobile.

### Courant moyen sur un cycle

Le TD précise que les phases ne se recouvrent pas. Dans chaque minute : 10 mA pendant 2 s, 20 mA pendant 3 s, puis 0,1 mA pendant 55 s.

```text
I_moyen = somme(I_i × t_i) / T
        = (10 × 2 + 20 × 3 + 0,1 × 55) / 60
        = 1,425 mA
Autonomie = 3000 / 1,425 ≈ 2105,26 h ≈ 87,72 jours
```

Ce résultat théorique suppose les courants représentatifs, les phases exclusives et la capacité utilisable. Si plusieurs composants consomment simultanément, il faut calculer le courant total de chaque phase avant de pondérer. Réduire la consommation de veille, le temps actif et les transmissions peut améliorer l'autonomie.

### ADC 12 bits et tension d'entrée

Un potentiomètre produit une tension analogique variable ; l'ADC la code numériquement. Pour 12 bits : **4096 codes, de 0 à 4095**. Dans l'hypothèse idéale 0–3,3 V de l'énoncé :

```text
Code ≈ Vin / 3,3 × 4095
Vin = 1,65 V → 2047,5 → environ 2048 après arrondi
```

Cette approximation du TD n'est pas une calibration d'un ESP32 réel. Plage, atténuation, référence et erreurs de conversion doivent être considérées lors d'une mesure effective.

## TD2 — Réseaux, serrure, parking et actionneurs

### Topologies et panne

A : les capteurs parlent directement à une passerelle → **étoile**. B : des voisins relaient → organisation multi-saut, **maillage dans le scénario du TD**. C : deux appareils communiquent directement → **point à point**.

Le maillage peut offrir des chemins alternatifs si sa connectivité le permet ; avoir des relais ne garantit pas à lui seul une redondance. Une passerelle unique en panne interrompt le service central associé, même si certains capteurs continuent de mesurer localement.

### Serrure connectée

Le lecteur RFID lit un identifiant, le MCU applique une règle d'autorisation puis pilote le verrou via un driver adapté. Le logiciel doit gérer lecture, autorisation, commande et cas de refus. Une liste d'identifiants illustre la logique du TD ; lire un identifiant ne constitue pas à lui seul une authentification forte contre la copie.

Le driver ou relais commute la charge selon ses caractéristiques électriques. Son rôle ne tient pas seulement à une différence de tension : courant nécessaire et protection de la commande comptent aussi.

### Parking de 20 places

Architecture : détection par place → microcontrôleur / collecte → réseau adapté → serveur → tableau de bord. Un choix de capteur doit permettre de détecter un véhicule stationné, par exemple selon distance ou présence magnétique ; la réponse « capteur de mouvement » seule est insuffisante pour une voiture immobile.

Le tableau de bord doit distinguer **libre, occupé et inconnu / capteur en défaut**. Ne pas transformer automatiquement une absence de mesure en place libre. La portée Wi-Fi dépend du site réel ; sommeil et transmissions sur changement d'état sont des pistes de réduction énergétique.

### Choisir le composant de commande

| Besoin | Composant / principe |
| --- | --- |
| Ouvrir une arrivée d'eau | Électrovanne et commande électrique adaptée |
| Régler la vitesse d'un moteur DC | Driver moteur commandé en PWM |
| Commander une pompe ON/OFF | Relais ou dispositif de commutation adapté à la charge |
| Positionner un bras à un angle | Actionneur de position, par exemple servomoteur, avec commande adaptée |
| Faire varier la luminosité d'une LED | PWM et circuit de LED adapté |

Le corrigé écrit « DWM » pour la vitesse moteur : lire **PWM** dans ce contexte. Un relais commute une alimentation ; il n'est pas lui-même une vanne ni un dispositif de positionnement.

### Questions de révision du TD2

1. **Le HC-SR04 fournit-il directement une distance numérique en mètres ?** Non : le logiciel exploite la durée d'impulsion de la mesure.
2. **Pourquoi pondérer les courants par leur durée ?** Les phases n'occupent pas la même part du cycle.
3. **Que signifie absence de mesure d'une place de parking ?** État inconnu à traiter, pas preuve de disponibilité.
4. **PWM est-il un moteur ?** Non : c'est un principe de commande ; un driver et la charge restent nécessaires.

Sources : `COURS/Chapter1-Introduction-IoT.pdf` (86 pages : définitions p. 5–29, caractéristiques p. 30–35, M2M p. 36–41, applications p. 42–55, technologies p. 56–72, défis p. 73–85), `COURS/Chapter2-Components-Sensors.pdf` (43 pages : nœud IoT, capteurs, actionneurs, microcontrôleurs, connectivité), `TD/TD1.pdf` (2 pages) et `TD/TD2-sol.pdf` (4 pages, huit exercices corrigés). Les projections de marché et débits publicitaires ne sont pas repris comme faits de révision.

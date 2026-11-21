# TP4 — Installation et vérification d'OpenStack avec DevStack

Date d'exécution : {{date}}. Le rapport décrit une installation réellement effectuée sur une VM Azure dédiée et les vérifications enregistrées. Les captures Horizon proviennent du navigateur ; les extraits CLI proviennent des journaux d'exécution. Aucune illustration de terminal simulé n'est utilisée.

## 1. Objectif et adaptation de l'environnement

Le sujet `TP4.pdf` demande Ubuntu 24.04, la préparation d'un utilisateur stack, l'installation de DevStack, un accès authentifié à Horizon et des vérifications avec la CLI OpenStack. Le but est de disposer d'un environnement de laboratoire pour explorer les services et préparer les exercices de réseau et d'instances.

Azure héberge ici la VM Ubuntu ; OpenStack est installé à l'intérieur. Une VM Azure seule ne constitue donc pas la réalisation du TP. Le choix du cloud remplace uniquement l'hyperviseur local VMware/VirtualBox proposé par l'énoncé.

| Paramètre | Configuration effectivement retenue |
| --- | --- |
| Abonnement | Azure for Students, actif lors du déploiement |
| Groupe de ressources | rg-devops-tp4-20261110 |
| VM | tp4-openstack |
| Région | Poland Central |
| Taille | Standard_D2s_v3 : 2 vCPU, 8 Go de RAM |
| Système | Ubuntu Server 24.04.5 LTS |
| Disque système | 80 Gio demandés ; environ 77 Gio de système de fichiers |
| Swap | 4 Gio, ajouté pour les pointes de consommation |
| Virtualisation | KVM disponible dans la VM Azure |
| Accès d'administration | SSH par clé, limité à l'IPv4 du poste de travail |
| Accès Horizon | Tunnel SSH local ; aucune ouverture publique du port HTTP |

La recommandation de l'enseignante est 4+ vCPU, 16 Go et 80 Go. À la demande de réduction du coût, le laboratoire utilise 2 vCPU et 8 Go. Il s'agit d'un compromis pédagogique, adapté aux vérifications réalisées, avec moins de marge pour lancer plusieurs instances. Le swap est plus lent que la RAM.

## 2. Préparation d'Ubuntu et utilisateur stack

Les opérations sont automatisées par les scripts fournis. La préparation est exécutée avec sudo ; le déploiement DevStack est exécuté ensuite sous le compte ordinaire stack.

```sh
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl wget
sudo useradd -s /bin/bash -d /opt/stack -m stack
sudo chmod +x /opt/stack
echo "stack ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/stack
sudo -u stack -i
```

Le compte stack possède le répertoire `/opt/stack` et les permissions sudo sans mot de passe requises par le TP sur cette machine jetable. `visudo` valide le fichier ajouté. Ces permissions concernent le compte de laboratoire ; elles ne sont pas appliquées au poste Windows.

Les contrôles de préparation ont relevé deux processeurs logiques, environ 7,7 Gio de RAM utilisable, 4 Gio de swap et la présence de `/dev/kvm`. Le commit DevStack retenu est :

```text
{{devstack_commit}}
```

Extrait réel de préparation :

{{preflight_excerpt}}

## 3. Téléchargement et configuration DevStack

Le dépôt officiel est cloné dans `/opt/stack/devstack`. Le fichier local.conf contient les paramètres ci-dessous ; la valeur du mot de passe a été générée aléatoirement et n'est pas publiée.

```ini
[[local|localrc]]
ADMIN_PASSWORD=<valeur_privee_generee>
DATABASE_PASSWORD=$ADMIN_PASSWORD
RABBIT_PASSWORD=$ADMIN_PASSWORD
SERVICE_PASSWORD=$ADMIN_PASSWORD
HOST_IP=10.44.1.4
LIBVIRT_TYPE=kvm
LOGFILE=/opt/stack/logs/stack.sh.log
LOG_COLOR=False
```

Le mot de passe est alphanumérique. Il est conservé sur la VM avec des permissions restrictives, et dans le dossier local privé exclu de Git. HOST_IP désigne l'adresse privée de la VM, pas son adresse publique Azure. Les réseaux Azure et OpenStack sont distincts.

La configuration minimale et l'usage d'un compte non-root suivent le sujet et le [guide officiel DevStack](https://docs.openstack.org/devstack/latest/). La documentation précise également que cet outil modifie fortement le système : cette installation utilise une VM dédiée.

## 4. Installation et preuve de fin d'exécution

```sh
cd /opt/stack/devstack
./stack.sh
```

L'installation tourne sous stack, avec journal conservé sur la VM. Le script ajoute un marqueur de fin uniquement si stack.sh se termine avec succès. Une simple présence de fichiers ou un écran de progression ne suffirait pas à conclure à une installation réussie.

Résultat de l'installation : **{{installation_result}}**.

{{installation_excerpt}}

## 5. Accès réel au tableau de bord Horizon

Le tableau de bord est consulté depuis Microsoft Edge à travers un tunnel SSH lié à 127.0.0.1. Le réseau Azure autorise l'administration SSH depuis le poste ; il n'expose pas Horizon à tout Internet.

```sh
ssh -i <cle_privee> -N -L 127.0.0.1:18080:127.0.0.1:80 azureuser@<IP_AZURE>
```

Ouvrir ensuite `http://127.0.0.1:18080/dashboard/`. La connexion utilise admin, le mot de passe généré et le domaine Default si celui-ci est demandé.

Résultat navigateur : **{{horizon_result}}**.

![Page de connexion Horizon réellement chargée dans Edge](evidence/02-horizon-login.png)

![Tableau de bord après authentification admin ; capture réelle](evidence/03-horizon-authenticated.png)

{{extra_horizon_images}}

La présence du formulaire prouve l'accès HTTP ; la seconde capture et la vérification de navigation prouvent une authentification réussie. Les mots de passe ne sont pas capturés dans les images fournies.

## 6. Vérifications OpenStack en ligne de commande

L'environnement d'administration est chargé avec `source openrc admin admin`. La commande de jeton est exécutée en ne conservant que son expiration : l'identifiant secret du jeton est volontairement absent du rapport.

```sh
cd /opt/stack/devstack
source openrc admin admin
openstack token issue -c expires -f value
openstack service list
openstack image list
openstack flavor list
openstack network list
openstack server list
```

Le sujet autorise certaines listes vides. Un catalogue enregistré ne prouve pas à lui seul que chaque processus fonctionne : le script vérifie aussi les services compute et les agents réseau.

{{cli_results}}

Ces résultats proviennent de `scripts/verify-openstack.sh` exécuté sur la VM, et sont conservés dans `evidence/02-openstack-verification.txt`.

## 7. Rôle des composants identifiés dans le TP

| Composant | Rôle | Exemple de contrôle |
| --- | --- | --- |
| Keystone | Identités et authentification | Émission d'un jeton après chargement openrc |
| Nova | Gestion des instances de calcul | server list ; compute service list |
| Neutron | Réseaux, sous-réseaux, routage et règles | network list ; network agent list |
| Glance | Catalogue des images | image list |
| Cinder | Volumes bloc | Présence du service dans le catalogue ; usage dans les prochains labs |
| Horizon | Interface web | Connexion admin réelle dans Edge |
| Placement | Inventaire et allocation des ressources de calcul | Présence dans le catalogue |

Les contrôles du TP4 établissent l'installation et l'accès aux services. Ils ne constituent pas une campagne exhaustive de tests de toutes les fonctions OpenStack ni la réalisation anticipée des deux labs suivants.

## 8. Difficultés rencontrées et corrections

| Difficulté réelle | Diagnostic et correction |
| --- | --- |
| CLI Azure non authentifiée | Connexion par code appareil, validée par l'utilisateur |
| Résolution du service de connexion momentanément en échec | Contrôle DNS, puis nouvelle tentative de connexion réussie |
| Taille indisponible en France Central | Consultation des restrictions et quotas ; choix d'une région autorisée avec capacité disponible |
| Réduction du budget | Passage à 2 vCPU et 8 Go, complétés par du swap |
| Exposition du tableau de bord | Utilisation d'un tunnel SSH ; aucune ouverture HTTP publique |

{{additional_troubleshooting}}

Les premiers objets réseau sans VM de France Central restent dans le groupe de laboratoire. Ils ne représentent pas une seconde VM en fonctionnement. Aucune ressource n'a été supprimée, conformément à la consigne de l'utilisateur.

## 9. Coût, conservation et accès ultérieur

Tarifs publics indicatifs relevés pendant le travail, en USD, hors taxes et hors éventuels avantages de l'abonnement :

| Ressource | Tarif public relevé |
| --- | --- |
| Calcul Standard_D2s_v3 Linux, Poland Central | 0,115 USD par heure |
| Disque Standard SSD E10 LRS | 9,60 USD par mois ; 80 Gio demandés relèvent du palier 128 Gio |
| Adresse IPv4 publique Standard | 0,005 USD par heure |
| Transactions du disque | Facturation séparée selon les opérations |

Avec une approximation mensuelle de 730 heures, le total de base est d'environ **0,133 USD/heure**, soit **3,20 USD par jour** si la VM reste allumée. Ce n'est pas une facture ni une mesure du solde de crédit. Les opérations disque et transferts éventuels s'ajoutent selon l'usage.

Après la vérification complète (installation, Horizon, CLI), toutes les ressources Azure du TP (groupe `rg-devops-tp4-20261110` : VM, disque, IP publique, NIC, VNet, NSG) ont été supprimées ; `az group exists` retourne `false` (voir `evidence/08-azure-cleanup.txt`). L'environnement n'est plus accessible et ne génère plus de coût ; les journaux et captures du rapport font foi.

## 10. Checklist finale et pièces fournies

{{checklist}}

Le dossier fournit le rapport Markdown/PDF, les scripts de préparation et vérification, les journaux sélectionnés, les captures Horizon et un manifeste de provenance avec empreintes SHA-256. Les secrets et clés privées ne font pas partie des livrables.

Sources : sujet local `TP4.pdf` (6 pages), [DevStack Quick Start](https://docs.openstack.org/devstack/latest/), [DevStack dans une VM](https://docs.openstack.org/devstack/latest/guides/single-vm.html), [CLI OpenStack](https://docs.openstack.org/python-openstackclient/latest/) et API publique Azure Retail Prices. Les captures et sorties observées sont datées dans les fichiers de preuve.

# TP4 — OpenStack / DevStack sur Ubuntu 24.04

Ce dossier accompagne le sujet `../TP4_Openstack.pdf`.

- `scripts/prepare-ubuntu.sh` : préparation d'une VM Ubuntu dédiée, utilisateur stack et configuration.
- `scripts/install-devstack.sh` : lancement de DevStack comme utilisateur stack.
- `scripts/verify-openstack.sh` : vérifications CLI sans afficher de jeton ni de mot de passe.
- `build_report.py` : génération du rapport PDF à partir du Markdown et des captures.

Les scripts modifient le système invité. Ils sont destinés à une VM de laboratoire
dédiée. Le mot de passe d'administration est généré dans la VM, stocké hors du
dépôt et exclu des journaux destinés au rapport.

## Procédure dans la VM

```sh
sudo bash prepare-ubuntu.sh
# Redémarrer si la préparation indique REBOOT_REQUIRED, puis se reconnecter.
sudo -u stack -H bash install-devstack.sh
sudo -u stack -H bash verify-openstack.sh
```

Ne pas exécuter stack.sh en root. Ne pas réexécuter la préparation sur une
installation déjà configurée : le script refuse d'écraser local.conf.

Le choix d'une VM réduite à 2 vCPU et 8 Go de RAM vise à limiter le coût.
Un swap de 4 Go complète la mémoire ; il ne remplace pas la vitesse de la RAM.
Le mode KVM est utilisé si disponible, sinon QEMU.

## Références

- [DevStack Quick Start](https://docs.openstack.org/devstack/latest/)
- [DevStack dans une VM](https://docs.openstack.org/devstack/latest/guides/single-vm.html)
- [OpenStack CLI](https://docs.openstack.org/python-openstackclient/latest/)

Les résultats d'exécution et les modalités d'accès seront renseignés après
vérification effective de l'environnement. Les ressources Azure sont conservées
jusqu'à une demande explicite de suppression de l'utilisateur.

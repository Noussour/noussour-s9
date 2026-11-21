"""Assemble the report only from completed, recorded lab checks."""
from pathlib import Path
import json
import re

BASE=Path(__file__).resolve().parent
EVIDENCE=BASE/'evidence'


def main():
    install=json.loads((EVIDENCE/'installation-verification.json').read_text(encoding='utf-8'))
    horizon=json.loads((EVIDENCE/'horizon-verification.json').read_text(encoding='utf-8'))
    cli=(EVIDENCE/'02-openstack-verification.txt').read_text(encoding='utf-8')
    preflight=(EVIDENCE/'01-ubuntu-preparation.txt').read_text(encoding='utf-8')
    assert install['exit_code']==0 and install['completion_marker']
    assert horizon['login_success']
    assert 'TP4 CLI verification completed successfully.' in cli
    commit=re.findall(r'^[0-9a-f]{40}$',preflight,re.M)[-1]
    memory=preflight[preflight.index('2\n'):preflight.index('uid=')].strip()
    images=[]
    for filename,caption in [('04-horizon-services.png','Catalogue des services affiché dans Horizon'),
                              ('05-horizon-networks.png','Réseaux visibles depuis Horizon')]:
        if (EVIDENCE/filename).exists():
            images.append(f'![{caption} ; capture réelle](evidence/{filename})')
    checklist='''| Élément du sujet | Résultat observé |
| --- | --- |
| Ubuntu et accès Internet | Vérifiés : système, installation des paquets et dépôts |
| Utilisateur stack | Créé, sudo sans mot de passe contrôlé |
| Dépôt DevStack | Cloné ; commit enregistré |
| local.conf | Créé avec secrets générés et HOST_IP privé |
| stack.sh | Terminé avec code 0 et marqueur de succès |
| Horizon | Connexion admin réussie dans Edge |
| Catalogue et commandes CLI | Exécutés avec succès ; journaux fournis |
| Préparation des prochains labs | Environnement installé ; les scénarios des labs 1 et 2 restent à réaliser |'''
    fields={
        'date':install['verified_at_utc'],
        'devstack_commit':commit,
        'preflight_excerpt':'```text\n'+memory+'\n```',
        'installation_result':'stack.sh terminé avec le code 0 ; marqueur de fin présent',
        'installation_excerpt':'```text\n'+install['summary'].strip()+'\n```',
        'horizon_result':'authentification admin réussie ; captures et métadonnées enregistrées',
        'extra_horizon_images':'\n\n'.join(images),
        'cli_results':'```text\n'+cli.strip()+'\n```',
        'additional_troubleshooting':install.get('additional_troubleshooting',''),
        'checklist':checklist,
    }
    source=(BASE/'rapport-source.md').read_text(encoding='utf-8')
    for key,value in fields.items():
        source=source.replace('{{'+key+'}}',value)
    assert not re.search(r'\{\{[a-z_]+\}\}',source)
    (BASE/'rapport.md').write_text(source,encoding='utf-8')
    print('Report assembled from completed installation, CLI and Horizon checks.')


if __name__=='__main__':
    main()

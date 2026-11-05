# Version simple — Java et outils du TD/TP

## Code Java : seulement deux classes

- `Reservation.java` : menu, tableau de places et operations synchronisees.
- `TestReservation.java` : deux threads tentent de reserver la derniere place.

```sh
javac -encoding UTF-8 -d out Reservation.java TestReservation.java
java -cp out Reservation
java -cp out TestReservation
```

Le menu demande un numero de reservant positif, puis la place souhaitee de 1
a 5. Une seule place par reservant. Au numero du reservant, 0 quitte le menu.
Au choix de la place, 0 annule la reservation de ce reservant. Une place
annulee peut etre reservee de nouveau. Le menu reste utilisable si la salle
est complete, pour permettre une annulation.

`synchronized` protege ensemble la verification et la modification du tableau.
Le test utilise deux threads et un signal commun ; exactement un client doit
reussir. Ce test reste distinct de la verification formelle des modeles.

## Verification demandee dans le TP

Lire [preuve-tp.md](preuve-tp.md) : contrats, invariants, correspondance entre
Java et modeles, proprietes, contre-exemples et limites.

| Travail | Outil / fichier |
| --- | --- |
| Etats et transitions | PlantUML : `modeles/reservation.puml` |
| Ressource partagee et conflit | PIPE : `modeles/reservation-pipe.xml`, PNML standard aussi fourni |
| Surete et vivacite | NuSMV : `modeles/reservation-correcte.smv` |
| Double reservation incorrecte | NuSMV : `modeles/reservation-incorrecte.smv` |
| Role de l'equite | NuSMV : `modeles/reservation-sans-equite.smv` |
| Confirmation avant echeance | PRISM : `modeles/reservation-probabiliste.pm` et `.pctl` |

Avec NuSMV et PRISM installes et disponibles dans le PATH :

```text
NuSMV modeles/reservation-correcte.smv
NuSMV modeles/reservation-incorrecte.smv
NuSMV modeles/reservation-sans-equite.smv
prism modeles/reservation-probabiliste.pm modeles/reservation-probabiliste.pctl -explicit -const D=5
java -jar chemin/plantuml.jar -tpng modeles/reservation.puml -o ../figures
```

Adapter les chemins a l'installation. Sous Windows, le lanceur PRISM peut
exiger un lancement depuis son dossier bin et des chemins absolus de modeles.

Les sorties reellement obtenues avec NuSMV 2.7.1 et PRISM 4.11 sont dans
`resultats/`. `figures/reservation.png` a ete genere par PlantUML.
Le modele incorrect doit produire deux invariants `false` et des traces de
contre-exemple ; la variante sans equite doit refuter les deux vivacites.

Pour PIPE : ouvrir `modeles/reservation-pipe.xml`, activer l'animation, puis
tirer ConfirmerA. ConfirmerB devient impossible tant que A n'a pas annule.
Comparer ConfirmerA -> RefuserB et ConfirmerA -> AnnulerA -> ConfirmerB.
L'import et l'animation dans l'interface PIPE restent a effectuer : les logs
Petri livres viennent de l'explorateur du corrige complet, pas de PIPE.

La verification formelle repose sur les outils demandes et leurs fichiers de
modeles. La classe supplementaire `VerificationFormelle.java` a ete retiree.

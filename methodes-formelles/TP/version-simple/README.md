# Version simple — deux classes Java

- `Reservation.java` : salle de 5 places et menu dans le terminal.
- `TestReservation.java` : deux clients tentent de reserver la derniere place.

Depuis ce dossier, avec un JDK installe :

```sh
javac -encoding UTF-8 -d out Reservation.java TestReservation.java
java -cp out Reservation
java -cp out TestReservation
```

Dans le menu, entrer un numero de reservant positif puis une place entre 1 et 5.
Entrer 0 au numero du reservant pour quitter. Chaque reservant ne peut avoir
qu'une place. Les numeros de places commencent a 1.

Le test reserve d'abord les places 1 et 2. Deux threads demandent ensuite la
place 3 a partir d'un meme signal `CountDownLatch`. La methode `synchronized`
protege ensemble la verification et l'attribution : un seul client reussit.
L'identite du gagnant depend de l'ordonnancement et peut varier.

Le resultat attendu est `TEST REUSSI : une confirmation et un refus.`
Le test leve `AssertionError` si le resultat est incorrect, meme sans `-ea`.

Cette version simplifiee traite la reservation et le conflit sur la derniere
place. Le corrige complet avec annulation, automates et modeles formels reste
dans `../solution-mimobn/`.

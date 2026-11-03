# Fiche de révision — Méthodes formelles pour GL

## Les distinctions essentielles

- Test : observer le résultat d'un scénario.
- Vérification : contrôler la conformité à la spécification.
- Validation : contrôler l'adéquation au besoin réel.
- Modèle : abstraction utile à la propriété étudiée.
- Sûreté : rien de mauvais n'arrive.
- Vivacité : quelque chose d'attendu finit par arriver.
- Invariant : propriété vraie dans tous les états atteignables concernés.
- Équité : éviter la négligence indéfinie d'un processus ou d'une action éligible.

## Quel outil pour quel problème ?

| Problème | Famille / technique |
| --- | --- |
| Préconditions/postconditions d'un programme | Hoare |
| États et transitions | Automates / systèmes de transitions |
| Communication entre composants | Automates communicants |
| Concurrence et ressources | Petri |
| Composition de comportements | Algèbres de processus |
| Évolution et propriétés de traces/chemins | LTL / CTL |
| Vérification automatique d'un modèle | Model checking |
| Données et invariants | Types abstraits / Z |
| Probabilités | Markov / modèles probabilistes |

## Hoare : les formules

```text
{P} C {Q} : si P et si C termine normalement, alors Q.
Correction totale = correction partielle + terminaison.

Affectation : {Q[E/x]} x := E {Q}
Séquence : {P} C1 {R}, {R} C2 {Q} ⇒ {P} C1 ; C2 {Q}
Condition : prouver C1 sous P ∧ B et C2 sous P ∧ ¬B.
Conséquence : renforcer P, affaiblir Q.

wp(x := E,Q) = Q[E/x]
wp(C1 ; C2,Q) = wp(C1,wp(C2,Q))
wp(if B then C1 else C2,Q)
  = (B ⇒ wp(C1,Q)) ∧ (¬B ⇒ wp(C2,Q))
```

Calculer à rebours : `x:=x+3` et `Q : x>7` donnent `x+3>7`, donc `x>4`. Préciser la convention de terminaison de `wp` ; le support donne une lecture partielle à la page 21.

## Automates et transitions

```text
A = (Q,Σ,δ,q0,F)
Déterministe : au plus une transition par état/symbole.
Déterministe complet : δ : Q × Σ → Q.
Non-déterministe ne signifie pas probabiliste.

STE : A = ⟨S,S0,E,R⟩ ; R inclus dans S × E × S.
ST : T = (S,→,S0).
Trace : suite de transitions autorisées.
Accessibilité : s0 →* s, y compris zéro transition.
État interdit D : D ∉ Reach(S0).
```

## Exemple de réservation

```text
EnAttente --[placesDisponibles > 0]--> Confirmee
EnAttente --[placesDisponibles = 0]--> Rejetee
0 ≤ placesDisponibles ≤ capacite
placesDisponibles + reservationsConfirmees = capacite
```

Adapter la conservation si le modèle inclut des annulations, places bloquées ou réservations temporaires. Un système bloqué peut respecter une propriété de sûreté sans respecter une propriété de vivacité.

## Trois pièges du support

1. Retrait bancaire : utiliser `m ≤ s` ; la page 32 du chapitre 1 inverse ce signe.
2. Valeur absolue : si `x=0`, alors `y=0` ; la garantie est `y≥0`.
3. Une trace est valide relativement au modèle choisi, pas dans tous les modèles possibles.

// Reservation avec defaillances et retards (chaine de Markov a temps discret).
// Un pas = une unite de temps.
// A chaque pas, la demande en attente est soit traitee, soit retardee, soit perdue
// (panne : elle doit etre renvoyee, ce qui coute un pas).
// Pendant ce temps, d'autres clients peuvent prendre les places restantes.

dtmc

const int N = 2;              // places libres au depart
const double p_retard = 0.2;  // la demande est retardee d'un pas
const double p_echec  = 0.1;  // panne : la demande est perdue et doit etre renvoyee
const double p_autre  = 0.3;  // un autre client prend une place pendant ce pas

formula p_ok = 1 - p_retard - p_echec;   // la demande est traitee a ce pas

// Etats de la demande
const int ATTENTE   = 0;
const int CONFIRMEE = 1;
const int REFUSEE   = 2;
const int PANNE     = 3;   // demande perdue, renvoi au pas suivant

module reservation
  etat   : [0..3] init ATTENTE;
  libres : [0..N] init N;

  // Demande traitee, retardee ou perdue. Un autre client peut prendre une place.
  [] etat = ATTENTE & libres > 0 ->
        p_ok                 : (etat' = CONFIRMEE) & (libres' = libres - 1)
      + p_retard * (1 - p_autre) : true
      + p_retard * p_autre       : (libres' = libres - 1)
      + p_echec  * (1 - p_autre) : (etat' = PANNE)
      + p_echec  * p_autre       : (etat' = PANNE) & (libres' = libres - 1);

  // Plus de place : la demande est refusee.
  [] etat = ATTENTE & libres = 0 -> (etat' = REFUSEE);

  // Renvoi apres une panne (un autre client peut encore prendre une place).
  [] etat = PANNE & libres > 0 ->
        (1 - p_autre) : (etat' = ATTENTE)
      + p_autre       : (etat' = ATTENTE) & (libres' = libres - 1);
  [] etat = PANNE & libres = 0 -> (etat' = ATTENTE);

  // Etats finaux
  [] etat = CONFIRMEE | etat = REFUSEE -> true;
endmodule

label "confirmee" = etat = CONFIRMEE;
label "refusee"   = etat = REFUSEE;

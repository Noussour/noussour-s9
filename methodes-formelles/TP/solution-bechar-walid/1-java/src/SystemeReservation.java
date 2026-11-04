/**
 * Systeme de reservation sequentiel pour un evenement de capacite fixe.
 *
 * Invariant :
 *   0 <= placesLibres <= capacite
 *   placesLibres + nbConfirmees == capacite   (aucune place perdue ni attribuee deux fois)
 *
 * Les preconditions, postconditions et l'invariant sont verifies a chaque appel.
 * Une violation leve une IllegalStateException.
 */
public class SystemeReservation {
    private final int capacite;
    private int placesLibres;
    private int nbConfirmees = 0;

    public SystemeReservation(int capacite) {
        exiger(capacite > 0, "la capacite doit etre positive");
        this.capacite = capacite;
        this.placesLibres = capacite;
        verifierInvariant();
    }

    /**
     * Pre  : d != null et d est EN_ATTENTE.
     * Post : si une place etait libre, d est CONFIRMEE et placesLibres a diminue de 1,
     *        sinon d est REFUSEE et placesLibres n'a pas change.
     */
    public void reserver(Demande d) {
        // Preconditions
        exiger(d != null, "pre : la demande ne doit pas etre nulle");
        exiger(d.getEtat() == Etat.EN_ATTENTE, "pre : la demande doit etre EN_ATTENTE");
        verifierInvariant();
        int avant = placesLibres;

        if (placesLibres > 0) {
            placesLibres--;
            nbConfirmees++;
            d.setEtat(Etat.CONFIRMEE);
        } else {
            d.setEtat(Etat.REFUSEE);
        }

        // Postconditions
        if (avant > 0) {
            exiger(d.getEtat() == Etat.CONFIRMEE && placesLibres == avant - 1,
                   "post : une place etait libre, la demande doit etre confirmee");
        } else {
            exiger(d.getEtat() == Etat.REFUSEE && placesLibres == avant,
                   "post : aucune place libre, la demande doit etre refusee");
        }
        verifierInvariant();
    }

    /**
     * Pre  : d est EN_ATTENTE ou CONFIRMEE.
     * Post : d est ANNULEE. Si elle etait confirmee, sa place est liberee.
     */
    public void annuler(Demande d) {
        exiger(d != null, "pre : la demande ne doit pas etre nulle");
        exiger(d.getEtat() == Etat.EN_ATTENTE || d.getEtat() == Etat.CONFIRMEE,
               "pre : seule une demande en attente ou confirmee peut etre annulee");
        verifierInvariant();
        int avant = placesLibres;
        boolean etaitConfirmee = d.getEtat() == Etat.CONFIRMEE;

        if (etaitConfirmee) {
            placesLibres++;
            nbConfirmees--;
        }
        d.setEtat(Etat.ANNULEE);

        exiger(d.getEtat() == Etat.ANNULEE, "post : la demande doit etre annulee");
        exiger(placesLibres == (etaitConfirmee ? avant + 1 : avant),
               "post : la place doit etre liberee si la demande etait confirmee");
        verifierInvariant();
    }

    public int getPlacesLibres() { return placesLibres; }
    public int getCapacite() { return capacite; }

    private void verifierInvariant() {
        exiger(placesLibres >= 0 && placesLibres <= capacite,
               "invariant : 0 <= placesLibres <= capacite");
        exiger(placesLibres + nbConfirmees == capacite,
               "invariant : placesLibres + nbConfirmees == capacite");
    }

    private static void exiger(boolean condition, String message) {
        if (!condition) throw new IllegalStateException(message);
    }
}

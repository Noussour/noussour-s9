/** Une demande de reservation faite par un client. */
public class Demande {
    private final String client;
    private Etat etat = Etat.EN_ATTENTE;

    public Demande(String client) {
        this.client = client;
    }

    public String getClient() { return client; }
    public Etat getEtat() { return etat; }

    // Seul le systeme de reservation change l'etat d'une demande.
    void setEtat(Etat etat) { this.etat = etat; }

    @Override
    public String toString() { return client + " : " + etat; }
}

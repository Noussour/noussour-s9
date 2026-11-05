import java.util.Scanner;

public class Reservation {
    // 0 = place libre ; sinon, numero du reservant.
    private final int[] places;

    public Reservation(int capacite) {
        if (capacite <= 0) {
            throw new IllegalArgumentException("La capacite doit etre positive.");
        }
        places = new int[capacite];
    }

    // Le meme verrou protege le controle ET l'attribution de la place.
    public synchronized boolean reserver(int reservant, int siege) {
        if (reservant <= 0 || siege < 1 || siege > places.length) {
            return false;
        }
        if (places[siege - 1] != 0) {
            return false;
        }
        for (int numero : places) {
            if (numero == reservant) {
                return false; // Une seule place par reservant.
            }
        }
        places[siege - 1] = reservant;
        return true;
    }

    public synchronized int placesLibres() {
        int total = 0;
        for (int numero : places) {
            if (numero == 0) {
                total++;
            }
        }
        return total;
    }

    public synchronized boolean annuler(int reservant) {
        if (reservant <= 0) {
            return false;
        }
        for (int i = 0; i < places.length; i++) {
            if (places[i] == reservant) {
                places[i] = 0;
                return true;
            }
        }
        return false;
    }

    public synchronized void afficherPlaces() {
        for (int i = 0; i < places.length; i++) {
            System.out.println("Place " + (i + 1) + " : "
                    + (places[i] == 0 ? "libre" : "reservant " + places[i]));
        }
    }

    public static void main(String[] args) {
        Reservation salle = new Reservation(5);
        Scanner clavier = new Scanner(System.in);
        System.out.println("Reservation de 5 places (une place par reservant).");

        while (true) {
            salle.afficherPlaces();
            if (salle.placesLibres() == 0) {
                System.out.println("Complet ! Une annulation reste possible.");
            }
            System.out.print("Numero du reservant (0 pour quitter) : ");
            if (!clavier.hasNext()) {
                return;
            }
            if (!clavier.hasNextInt()) {
                System.out.println("Entrez un nombre entier.");
                clavier.next();
                continue;
            }
            int reservant = clavier.nextInt();
            if (reservant == 0) {
                return;
            }
            if (reservant < 0) {
                System.out.println("Le numero du reservant doit etre positif.");
                continue;
            }

            System.out.print("Numero de la place (1 a 5, 0 pour annuler) : ");
            if (!clavier.hasNext()) {
                return;
            }
            if (!clavier.hasNextInt()) {
                System.out.println("Entrez un nombre entier.");
                clavier.next();
                continue;
            }
            int siege = clavier.nextInt();
            if (siege == 0) {
                System.out.println(salle.annuler(reservant)
                        ? "Reservation annulee." : "Aucune reservation pour ce numero.");
            } else if (siege < 1 || siege > 5) {
                System.out.println("La place doit etre entre 1 et 5.");
            } else if (salle.reserver(reservant, siege)) {
                System.out.println("Reservation confirmee.");
            } else {
                System.out.println("Refus : place occupee ou reservant deja inscrit.");
            }
        }
    }
}

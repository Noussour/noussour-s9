import java.util.concurrent.CountDownLatch;

public class TestReservation {
    public static void main(String[] args) throws InterruptedException {
        Reservation salle = new Reservation(3);
        if (!salle.reserver(1, 1) || !salle.reserver(2, 2)) {
            throw new AssertionError("Preparation impossible.");
        }
        System.out.println("Il reste une seule place : la place 3.");

        boolean[] resultats = new boolean[2];
        CountDownLatch prets = new CountDownLatch(2);
        CountDownLatch depart = new CountDownLatch(1);
        Thread[] clients = new Thread[2];

        for (int i = 0; i < clients.length; i++) {
            final int index = i;
            clients[i] = new Thread(() -> {
                prets.countDown();
                try {
                    depart.await(); // Les deux clients attendent le meme signal.
                    resultats[index] = salle.reserver(index + 3, 3);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            });
            clients[i].start();
        }

        prets.await();
        depart.countDown(); // Lancer les deux tentatives concurrentes.
        for (Thread client : clients) {
            client.join(); // Attendre les resultats avant de les verifier.
        }

        System.out.println("Reservant 3 : " + (resultats[0] ? "confirme" : "refuse"));
        System.out.println("Reservant 4 : " + (resultats[1] ? "confirme" : "refuse"));
        salle.afficherPlaces();
        if (resultats[0] == resultats[1] || salle.placesLibres() != 0) {
            throw new AssertionError("Il faut exactement une confirmation.");
        }
        System.out.println("TEST REUSSI : une confirmation et un refus.");
    }
}

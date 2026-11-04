import java.util.*;
import java.util.concurrent.*;

public final class ReservationTests {
    private static int checks;
    private static void check(boolean condition, String message) {
        checks++;
        if (!condition) throw new AssertionError(message);
    }
    private static void invalid(Runnable action) {
        try { action.run(); throw new AssertionError("Exception attendue"); }
        catch (IllegalArgumentException | NullPointerException expected) { checks++; }
    }
    private static void conserved(ReservationSystem system) {
        var state = system.snapshot();
        check(state.available() + state.confirmed() == state.capacity(), "Conservation");
        Set<Integer> seats = new HashSet<>();
        Set<String> users = new HashSet<>();
        for (var request : state.requests()) if (request.status() == ReservationSystem.Status.CONFIRMEE) {
            check(seats.add(request.seat()), "Place attribuee deux fois");
            check(users.add(request.user()), "Utilisateur avec deux reservations actives");
        }
    }

    private static void sequential() {
        var system = new ReservationSystem(2);
        var pending = system.submit("A");
        check(pending.status() == ReservationSystem.Status.EN_ATTENTE, "Etat initial");
        var a = system.process(pending.id());
        var b = system.reserve("B");
        check(a.status() == ReservationSystem.Status.CONFIRMEE && a.seat() == 1, "A confirme");
        check(b.status() == ReservationSystem.Status.CONFIRMEE && b.seat() == 2, "B confirme");
        check(system.reserve(" A ").reason() == ReservationSystem.Reason.DEJA_RESERVE, "Doublon utilisateur");
        check(system.reserve("C").reason() == ReservationSystem.Reason.COMPLET, "Complet");
        conserved(system);
        check(system.cancel(a.id()), "Annulation confirmee");
        check(!system.cancel(a.id()), "Annulation idempotente");
        check(system.snapshot().available() == 1, "Une seule place rendue");
        check(system.process(a.id()).status() == ReservationSystem.Status.ANNULEE, "Annulee terminale");
        check(system.reserve("D").seat() == 1, "Reutilisation apres annulation");
        var waiting = system.submit("E");
        check(system.cancel(waiting.id()), "Annuler avant traitement");
        check(system.snapshot().available() == 0, "Annulation en attente sans liberation");
        conserved(system);
        var zero = new ReservationSystem(0);
        check(zero.reserve("A").status() == ReservationSystem.Status.REFUSEE, "Capacite nulle");
        conserved(zero);
        invalid(() -> new ReservationSystem(-1));
        invalid(() -> system.submit("  "));
        invalid(() -> system.submit(null));
        invalid(() -> system.process(999));
        invalid(() -> system.cancel(999));
        System.out.println("SEQUENTIEL : les quatre etats, refus, doublons et annulations verifies.");
    }

    private static void concurrentReservations(String firstUser, String secondUser, int capacity) throws Exception {
        var system = new ReservationSystem(capacity);
        var start = new CyclicBarrier(3);
        var workers = Executors.newFixedThreadPool(2);
        try {
            Callable<ReservationSystem.Decision> first = () -> { start.await(5, TimeUnit.SECONDS); return system.reserve(firstUser); };
            Callable<ReservationSystem.Decision> second = () -> { start.await(5, TimeUnit.SECONDS); return system.reserve(secondUser); };
            var a = workers.submit(first);
            var b = workers.submit(second);
            start.await(5, TimeUnit.SECONDS);
            var ra = a.get(5, TimeUnit.SECONDS);
            var rb = b.get(5, TimeUnit.SECONDS);
            int count = (ra.status() == ReservationSystem.Status.CONFIRMEE ? 1 : 0)
                      + (rb.status() == ReservationSystem.Status.CONFIRMEE ? 1 : 0);
            check(count == 1, "Une confirmation attendue pour cette concurrence");
            conserved(system);
        } finally { workers.shutdownNow(); }
    }

    public static void main(String[] args) throws Exception {
        sequential();
        for (int i = 0; i < 100; i++) concurrentReservations("A", "B", 1);
        for (int i = 0; i < 100; i++) concurrentReservations("A", "A", 2);
        System.out.println("CONCURRENCE : 100 courses derniere place + 100 courses meme utilisateur reussies.");
        var broken = BrokenReservationRace.run();
        check(broken.available() == 0 && broken.confirmations() == 2 && broken.distinctSeats() == 1,
              "Le contre-exemple deterministe doit reproduire la double attribution");
        System.out.println("CONTRE-EXEMPLE : available=" + broken.available() + ", confirmations="
            + broken.confirmations() + ", distinctSeats=" + broken.distinctSeats());
        System.out.println("TOTAL : " + checks + " verifications explicites reussies (sans option -ea).");
    }
}

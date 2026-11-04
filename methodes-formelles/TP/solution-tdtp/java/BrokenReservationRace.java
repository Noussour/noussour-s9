import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

/** Contre-exemple intentionnel : ne pas utiliser cette classe en production. */
public final class BrokenReservationRace {
    public record Result(int available, int confirmations, int distinctSeats) {}

    public static Result run() throws Exception {
        AtomicInteger available = new AtomicInteger(1);
        AtomicInteger confirmations = new AtomicInteger();
        ConcurrentMap<String, Integer> assigned = new ConcurrentHashMap<>();
        CountDownLatch bothRead = new CountDownLatch(2);
        ExecutorService workers = Executors.newFixedThreadPool(2);
        try {
            Future<?> first = workers.submit(() -> book("A", available, confirmations, assigned, bothRead));
            Future<?> second = workers.submit(() -> book("B", available, confirmations, assigned, bothRead));
            first.get(5, TimeUnit.SECONDS);
            second.get(5, TimeUnit.SECONDS);
            return new Result(available.get(), confirmations.get(),
                              (int) assigned.values().stream().distinct().count());
        } finally { workers.shutdownNow(); }
    }

    private static void book(String user, AtomicInteger available, AtomicInteger confirmations,
                             ConcurrentMap<String, Integer> assigned, CountDownLatch bothRead) {
        int observed = available.get(); // lecture separee de la decision/attribution
        bothRead.countDown();
        try {
            if (!bothRead.await(5, TimeUnit.SECONDS)) throw new IllegalStateException("Timeout");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException(e);
        }
        if (observed > 0) {
            assigned.put(user, 1); // meme derniere place pour A et B
            available.set(observed - 1); // deux ecritures de 0, et non un decrementation atomique
            confirmations.incrementAndGet();
        }
    }
}

import java.util.*;

/** Modele Java 17 : chaque operation publique observe un etat coherent. */
public final class ReservationSystem {
    public enum Status { EN_ATTENTE, CONFIRMEE, REFUSEE, ANNULEE }
    public enum Reason { AUCUNE, COMPLET, DEJA_RESERVE }
    public record Decision(long id, String user, Status status,
                           Integer seat, Reason reason) {}
    public record Snapshot(int capacity, int available, List<Decision> requests) {
        public long confirmed() {
            return requests.stream().filter(r -> r.status() == Status.CONFIRMEE).count();
        }
    }

    private final int capacity;
    private final NavigableSet<Integer> freeSeats = new TreeSet<>();
    private final Map<Long, Decision> requests = new LinkedHashMap<>();
    private final Map<String, Long> activeByUser = new HashMap<>();
    private long nextId;

    public ReservationSystem(int capacity) {
        if (capacity < 0) throw new IllegalArgumentException("Capacite negative");
        this.capacity = capacity;
        for (int i = 0; i < capacity; i++) freeSeats.add(i + 1);
        checkInvariants();
    }

    public synchronized Decision submit(String user) {
        Objects.requireNonNull(user, "Utilisateur absent");
        user = user.strip();
        if (user.isEmpty()) throw new IllegalArgumentException("Utilisateur vide");
        long id = Math.incrementExact(nextId);
        Decision request = new Decision(id, user, Status.EN_ATTENTE, null, Reason.AUCUNE);
        requests.put(id, request);
        nextId = id;
        checkInvariants();
        return request;
    }

    public synchronized Decision process(long id) {
        Decision old = requireRequest(id);
        if (old.status() != Status.EN_ATTENTE) return old;
        Decision result;
        if (activeByUser.containsKey(old.user())) {
            result = new Decision(id, old.user(), Status.REFUSEE, null, Reason.DEJA_RESERVE);
        } else if (freeSeats.isEmpty()) {
            result = new Decision(id, old.user(), Status.REFUSEE, null, Reason.COMPLET);
        } else {
            int seat = freeSeats.pollFirst();
            result = new Decision(id, old.user(), Status.CONFIRMEE, seat, Reason.AUCUNE);
            activeByUser.put(old.user(), id);
        }
        requests.put(id, result);
        checkInvariants();
        return result;
    }

    /** Le verrou est reentrant : soumission et decision forment une operation atomique. */
    public synchronized Decision reserve(String user) {
        return process(submit(user).id());
    }

    public synchronized boolean cancel(long id) {
        Decision old = requireRequest(id);
        if (old.status() == Status.ANNULEE || old.status() == Status.REFUSEE) return false;
        if (old.status() == Status.CONFIRMEE) {
            freeSeats.add(old.seat());
            activeByUser.remove(old.user(), id);
        }
        requests.put(id, new Decision(id, old.user(), Status.ANNULEE, null, Reason.AUCUNE));
        checkInvariants();
        return true;
    }

    public synchronized Snapshot snapshot() {
        return new Snapshot(capacity, freeSeats.size(), List.copyOf(requests.values()));
    }

    private Decision requireRequest(long id) {
        Decision value = requests.get(id);
        if (value == null) throw new IllegalArgumentException("Demande inconnue : " + id);
        return value;
    }

    private void checkInvariants() {
        Set<Integer> occupied = new HashSet<>();
        Set<String> users = new HashSet<>();
        int count = 0;
        for (Decision request : requests.values()) {
            if (request.status() == Status.CONFIRMEE) {
                count++;
                require(request.seat() != null && request.seat() >= 1 && request.seat() <= capacity);
                require(occupied.add(request.seat()) && users.add(request.user()));
                require(!freeSeats.contains(request.seat()));
                require(Objects.equals(activeByUser.get(request.user()), request.id()));
            } else require(request.seat() == null);
        }
        require(count == activeByUser.size());
        require(freeSeats.size() + count == capacity);
        require(freeSeats.stream().allMatch(s -> s >= 1 && s <= capacity));
    }

    private static void require(boolean condition) {
        if (!condition) throw new IllegalStateException("Invariant de reservation viole");
    }
}

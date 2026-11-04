/** Scenarios de test du systeme de reservation sequentiel. */
public class Main {
    private static int reussis = 0;
    private static int total = 0;

    public static void main(String[] args) {
        System.out.println("== Scenario : capacite 2, quatre clients ==");
        SystemeReservation sys = new SystemeReservation(2);
        Demande a = new Demande("A");
        Demande b = new Demande("B");
        Demande c = new Demande("C");
        Demande d = new Demande("D");

        sys.reserver(a);
        sys.reserver(b);
        sys.reserver(c);
        afficher(sys, a, b, c);
        test("A et B confirmees", a.getEtat() == Etat.CONFIRMEE && b.getEtat() == Etat.CONFIRMEE);
        test("C refusee (plus de place)", c.getEtat() == Etat.REFUSEE);
        test("0 place libre", sys.getPlacesLibres() == 0);

        sys.annuler(a);
        test("A annulee, une place liberee", a.getEtat() == Etat.ANNULEE && sys.getPlacesLibres() == 1);

        sys.reserver(d);
        afficher(sys, a, b, c, d);
        test("D obtient la place liberee", d.getEtat() == Etat.CONFIRMEE && sys.getPlacesLibres() == 0);

        System.out.println("\n== Violations de preconditions (doivent etre rejetees) ==");
        testRejet("reserver une demande deja confirmee", () -> sys.reserver(b));
        testRejet("reserver une demande refusee", () -> sys.reserver(c));
        testRejet("annuler une demande refusee", () -> sys.annuler(c));
        testRejet("annuler deux fois", () -> sys.annuler(a));
        testRejet("capacite nulle", () -> new SystemeReservation(0));

        System.out.println("\n" + reussis + "/" + total + " tests reussis");
        if (reussis != total) System.exit(1);
    }

    private static void afficher(SystemeReservation sys, Demande... demandes) {
        for (Demande d : demandes) System.out.println("  " + d);
        System.out.println("  places libres = " + sys.getPlacesLibres() + "/" + sys.getCapacite());
    }

    private static void test(String nom, boolean ok) {
        total++;
        if (ok) reussis++;
        System.out.println((ok ? "[OK]    " : "[ECHEC] ") + nom);
    }

    private static void testRejet(String nom, Runnable action) {
        try {
            action.run();
            test(nom + " -> non rejete", false);
        } catch (IllegalStateException e) {
            test(nom + " -> rejete (" + e.getMessage() + ")", true);
        }
    }
}

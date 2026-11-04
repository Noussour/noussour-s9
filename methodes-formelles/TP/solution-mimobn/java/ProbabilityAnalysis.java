import java.math.*;

/** Calcul exact, en Java, de la DTMC a trois etats du fichier PRISM. */
public final class ProbabilityAnalysis {
    public static void main(String[] args) {
        BigDecimal p = new BigDecimal("0.70");
        BigDecimal f = new BigDecimal("0.05");
        BigDecimal r = BigDecimal.ONE.subtract(p).subtract(f);
        BigDecimal pending = BigDecimal.ONE, confirmed = BigDecimal.ZERO, failed = BigDecimal.ZERO;
        System.out.println("D,confirmation,defaillance,attente");
        for (int d = 0; d <= 10; d++) {
            BigDecimal closed = p.multiply(BigDecimal.ONE.subtract(r.pow(d)))
                .divide(BigDecimal.ONE.subtract(r), MathContext.DECIMAL128);
            if (closed.subtract(confirmed).abs().compareTo(new BigDecimal("1e-30")) > 0)
                throw new AssertionError("Desaccord recurrence / formule fermee");
            if (confirmed.add(failed).add(pending).compareTo(BigDecimal.ONE) != 0)
                throw new AssertionError("Masse probabiliste non conservee");
            System.out.println(d + "," + confirmed.toPlainString() + ","
                + failed.toPlainString() + "," + pending.toPlainString());
            confirmed = confirmed.add(pending.multiply(p));
            failed = failed.add(pending.multiply(f));
            pending = pending.multiply(r);
        }
        System.out.println("Limite confirmation=" + p.divide(p.add(f), MathContext.DECIMAL128));
        System.out.println("Limite defaillance=" + f.divide(p.add(f), MathContext.DECIMAL128));
    }
}

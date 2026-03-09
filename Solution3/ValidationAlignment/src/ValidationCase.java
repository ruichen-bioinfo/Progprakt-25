public class ValidationCase {

    private final String header;
    private final PairAlignment candidate;
    private final PairAlignment reference;

    public ValidationCase(String header, PairAlignment candidate, PairAlignment reference) {
        this.header = header;
        this.candidate = candidate;
        this.reference = reference;
    }

    public String getHeader() {
        return header;
    }

    public PairAlignment getCandidate() {
        return candidate;
    }

    public PairAlignment getReference() {
        return reference;
    }
}
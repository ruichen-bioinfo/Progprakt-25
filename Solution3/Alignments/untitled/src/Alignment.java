public class Alignment {

    private final String id1;
    private final String id2;
    private final String aligned1;
    private final String aligned2;
    private final int score;
    private final int startI;
    private final int endI;
    private final int startJ;
    private final int endJ;
    private final Sequence seq1;
    private final Sequence seq2;

    public Alignment(String id1, String id2, String aligned1, String aligned2, int score, int startI, int endI, int startJ, int endJ, Sequence seq1, Sequence seq2) {
        this.id1 = id1;
        this.id2 = id2;
        this.aligned1 = aligned1;
        this.aligned2 = aligned2;
        this.score = score;
        this.startI = startI;
        this.endI = endI;
        this.startJ = startJ;
        this.endJ = endJ;
        this.seq1 = seq1;
        this.seq2 = seq2;

    }

    public String getId1() {
        return id1;
    }

    public String getId2() {
        return id2;
    }

    public String getAligned1() {
        return aligned1;
    }

    public String getAligned2() {
        return aligned2;
    }

    public int getScore() {
        return score;
    }
    public int getStartI() {
        return startI;
    }
    public int getEndI() {
        return endI;
    }
    public int getStartJ() {
        return startJ;
    }
    public int getEndJ() {
        return endJ;
    }
    public String getSeq1() {
        return seq1.getSequence();
    }
    public String getSeq2() {
        return seq2.getSequence();
    }
}
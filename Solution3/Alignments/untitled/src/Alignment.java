public class Alignment {

    private final String id1;
    private final String id2;
    private final String aligned1;
    private final String aligned2;
    private final int score;

    public Alignment(String id1, String id2, String aligned1, String aligned2, int score){
        this.id1 = id1;
        this.id2 = id2;
        this.aligned1 = aligned1;
        this.aligned2 = aligned2;
        this.score = score;
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
}
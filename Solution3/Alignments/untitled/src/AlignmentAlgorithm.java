public abstract class AlignmentAlgorithm {

    protected Sequence seq1;
    protected Sequence seq2;
    protected Matrix scoringMatrix;
    protected Alignment result;

    public AlignmentAlgorithm(Sequence seq1, Sequence seq2, Matrix scoringMatrix) {
        this.seq1 = seq1;
        this.seq2 = seq2;
        this.scoringMatrix = scoringMatrix;
    }

    public Alignment getResult() {
        return result;
    }
    protected int score(int i, int j) {
        return scoringMatrix.score(seq1.charAt(i), seq2.charAt(j));
    }

    public void align(){
        initMatrix();
        fillMatrix();
        traceback();
    }
    public abstract void initMatrix();
    public abstract void fillMatrix();
    public abstract void traceback();
}

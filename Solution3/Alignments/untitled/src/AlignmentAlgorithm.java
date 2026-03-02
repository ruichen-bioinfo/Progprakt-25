public abstract class AlignmentAlgorithm {

    protected Sequence seq1;
    protected Sequence seq2;
    protected Matrix scoringMatrix;

    public AlignmentAlgorithm(Sequence seq1, Sequence seq2) {
        this.seq1 = seq1;
        this.seq2 = seq2;
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

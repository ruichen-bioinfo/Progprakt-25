public abstract class AlignmentAlgorithm {

    protected Sequence seq1;
    protected Sequence seq2;
    protected Matrix scoringMatrix;
    protected Alignment result;
    protected GapPenalty gapPenalty;

    public AlignmentAlgorithm(Sequence seq1, Sequence seq2, Matrix scoringMatrix, GapPenalty gapPenalty) {
        this.seq1 = seq1;
        this.seq2 = seq2;
        this.scoringMatrix = scoringMatrix;
        this.gapPenalty = gapPenalty;
    }

    public Alignment getResult() {
        return result;
    }
    protected double score(int i, int j) {
        return scoringMatrix.score(seq1.charAt(i), seq2.charAt(j));
    }

    public void align(){
        initMatrix();
        fillMatrix();
        traceback();
    }
    protected abstract void initMatrix();
    protected abstract void fillMatrix();
    protected abstract void traceback();
}

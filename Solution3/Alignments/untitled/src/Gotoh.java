public abstract class Gotoh extends AlignmentAlgorithm {
    public Gotoh(Sequence seq1, Sequence seq2, Matrix matrix, GapPenalty gapPenalty) {
        super(seq1, seq2, matrix, gapPenalty);
    }
    protected int[][] M;
    protected int[][] I;
    protected int[][] D;

    @Override
    protected void fillMatrix(){


    }
}

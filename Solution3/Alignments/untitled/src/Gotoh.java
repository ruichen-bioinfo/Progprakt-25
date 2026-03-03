public abstract class Gotoh extends AlignmentAlgorithm {
    public Gotoh(Sequence seq1, Sequence seq2, Matrix matrix) {
        super(seq1, seq2, matrix);
    }
    protected int[][] M1;
    protected int[][] M2;
    protected int[][] M3;
}

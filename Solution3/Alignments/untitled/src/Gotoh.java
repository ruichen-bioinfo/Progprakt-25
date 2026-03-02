public abstract class Gotoh extends AlignmentAlgorithm {
    public Gotoh(Sequence seq1, Sequence seq2) {
        super(seq1, seq2);
    }
    protected Matrix M1 = new Matrix(seq1.getLength(), seq2.getLength());
    protected Matrix M2 = new Matrix(seq2.getLength(), seq1.getLength());
    protected Matrix M3 = new Matrix(seq1.getLength(), seq2.getLength());
}

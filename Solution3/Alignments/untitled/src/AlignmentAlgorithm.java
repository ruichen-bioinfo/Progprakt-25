public abstract class AlignmentAlgorithm {

    protected Sequence seq1;
    protected Sequence seq2;

    public AlignmentAlgorithm(Sequence seq1, Sequence seq2) {
        this.seq1 = seq1;
        this.seq2 = seq2;
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

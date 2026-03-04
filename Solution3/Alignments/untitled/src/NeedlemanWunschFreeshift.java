public class NeedlemanWunschFreeshift extends NeedlemanWunsch {
    public NeedlemanWunschFreeshift(Sequence seq1, Sequence seq2, Matrix scoringMatrix, GapPenalty gapPenalty) {
        super(seq1, seq2, scoringMatrix, gapPenalty);
    }

    @Override
    protected void initMatrix() {

    }

    @Override
    protected void traceback() {

    }

    @Override
    protected int computeCellValue(int i, int j) {
        return 0;
    }
}

public class GotohGlobal extends Gotoh {
    public GotohGlobal(Sequence seq1, Sequence seq2, Matrix scoringMatrix, GapPenalty gapPenalty) {
        super(seq1, seq2, scoringMatrix, gapPenalty);
    }

    @Override
    public void initMatrix() {
        int negInf = Integer.MIN_VALUE / 2;

        M[0][0] = 0;
        I[0][0] = negInf;
        D[0][0] = negInf;

        for (int i = 1; i <= seqLen; i++){
            M[i][0] = negInf;
            D[i][0] = negInf;
            I[i][0] = gapopen + i * gapextend;
        }

        for (int j = 1; j <= seqLen2; j++){
            M[0][j] = negInf;
            D[0][j] = gapopen + j * gapextend;
            I[0][j] = negInf;
        }

    }
    @Override
    protected int adjust(int value){
        return Math.max(0, value);
    }

    @Override
    public void traceback() {

    }

}

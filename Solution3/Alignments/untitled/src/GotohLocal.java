public class GotohLocal extends Gotoh {
    public GotohLocal(Sequence seq1, Sequence seq2, Matrix scoringMatrix, GapPenalty gapPenalty) {
        super(seq1, seq2, scoringMatrix, gapPenalty);
    }


    @Override
    public void initMatrix() {
        int zero = 0;

        M[0][0] = 0;
        I[0][0] = zero;
        D[0][0] = zero;

        for (int i = 1; i <= seqLen; i++){
            M[i][0] = zero;
            D[i][0] = zero;
            I[i][0] = zero;
        }

        for (int j = 1; j <= seqLen2; j++){
            M[0][j] = zero;
            D[0][j] = zero;
            I[0][j] = zero;
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

public abstract class Gotoh extends AlignmentAlgorithm {
    protected int[][] M;
    protected int[][] I;
    protected int[][] D;
    protected int gapopen;
    protected int gapextend;
    protected int seqLen;
    protected int seqLen2;
    public Gotoh(Sequence seq1, Sequence seq2, Matrix matrix, GapPenalty gapPenalty) {
        super(seq1, seq2, matrix, gapPenalty);

        this.seqLen = seq1.getLength();
        this.seqLen2 = seq2.getLength();

        M = new int[seqLen+1][seqLen2+1];
        I = new int[seqLen+1][seqLen2+1];
        D = new int[seqLen+1][seqLen2+1];

        gapopen = gapPenalty.getOpen();
        gapextend = gapPenalty.getExtend();


    }




    @Override
    protected void fillMatrix(){

        for (int i = 1; i <= seqLen; i++) {
            for (int j = 1; j <= seqLen2; j++) {
                int score = scoringMatrix.score(seq1.charAt(i-1), seq2.charAt(j-1));
                int Mscore = Math.max(Math.max(I[i-1][j-1], D[i-1][j-1]), M[i-1][j-1]) + score;
                int Iscore = Math.max(I[i-1][j] + gapextend, M[i-1][j] + gapopen + gapextend);
                int Dscore = Math.max(D[i][j-1]+gapextend, M[i][j-1]+gapopen + gapextend);

                M[i][j] = adjust(Mscore);
                I[i][j] = adjust(Iscore);
                D[i][j] = adjust(Dscore);
            }
        }
    }

    protected int adjust(int value){
        return value;
    }


}

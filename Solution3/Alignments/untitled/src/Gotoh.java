public abstract class Gotoh extends AlignmentAlgorithm {
    public Gotoh(Sequence seq1, Sequence seq2, Matrix matrix, GapPenalty gapPenalty) {
        super(seq1, seq2, matrix, gapPenalty);
    }

    protected int seqLen = seq1.getLength();
    protected int seqLen2 = seq2.getLength();
    protected int[][] M = new int[seqLen+1][seqLen2+1];
    protected int[][] I = new int[seqLen+1][seqLen2+1];
    protected int[][] D = new int[seqLen+1][seqLen2+1];
    int gapextend = gapPenalty.getExtend();
    int gapopen = gapPenalty.getOpen();

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

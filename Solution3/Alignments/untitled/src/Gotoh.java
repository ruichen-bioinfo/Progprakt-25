public abstract class Gotoh extends AlignmentAlgorithm {
    protected double[][] M;
    protected double[][] I;
    protected double[][] D;
    protected double gapopen;
    protected double gapextend;
    protected int seqLen;
    protected int seqLen2;
    public Gotoh(Sequence seq1, Sequence seq2, Matrix matrix, GapPenalty gapPenalty) {
        super(seq1, seq2, matrix, gapPenalty);

        this.seqLen = seq1.getLength();
        this.seqLen2 = seq2.getLength();

        M = new double[seqLen+1][seqLen2+1];
        I = new double[seqLen+1][seqLen2+1];
        D = new double[seqLen+1][seqLen2+1];

        gapopen = gapPenalty.getOpen();
        gapextend = gapPenalty.getExtend();


    }




    @Override
    protected void fillMatrix(){

        for (int i = 1; i <= seqLen; i++) {
            for (int j = 1; j <= seqLen2; j++) {
                double score = scoringMatrix.score(seq1.charAt(i-1), seq2.charAt(j-1));

                I[i][j] = adjust(Math.max(
                        I[i-1][j] + gapextend,
                        M[i-1][j] + gapopen + gapextend
                ));

                D[i][j] = adjust(Math.max(
                        D[i][j-1] + gapextend,
                        M[i][j-1] + gapopen + gapextend
                ));

                M[i][j] = adjust(Math.max(
                        M[i-1][j-1] + score,
                        Math.max(I[i][j], D[i][j])
                ));

                //M[i][j] = adjust(Mscore);
                //I[i][j] = adjust(Iscore);
                //D[i][j] = adjust(Dscore);
            }
        }
    }

    protected double adjust(double value){
        return value;
    }

    public double[][] getM() {
        return M;
    }
    public double[][] getI() {
        return I;
    }
    public double[][] getD() {
        return D;
    }


}

public class GotohFreeshift extends Gotoh{
    public GotohFreeshift(Sequence seq1, Sequence seq2, Matrix scoringMatrix, GapPenalty gapPenalty) {
        super(seq1, seq2, scoringMatrix, gapPenalty);
    }

    @Override
    public void initMatrix() {

        double negInf = Double.NEGATIVE_INFINITY;

        M[0][0] = 0;
        I[0][0] = negInf;
        D[0][0] = negInf;

        for (int i = 1; i <= seqLen; i++) {
            M[i][0] = 0;
            I[i][0] = negInf;
            D[i][0] = negInf;
        }

        for (int j = 1; j <= seqLen2; j++) {
            M[0][j] = 0;
            I[0][j] = negInf;
            D[0][j] = negInf;
        }
    }



    static final double EPS = 1e-6;

    @Override
    public void traceback() {

        StringBuilder aligned1 = new StringBuilder();
        StringBuilder aligned2 = new StringBuilder();


        int state = 0;

        double maxscore = Double.NEGATIVE_INFINITY;

        int startI = 0;
        int startJ = 0;

        for (int i = 0; i <= seqLen; i++) {
            if (M[i][seqLen2] > maxscore) {
                maxscore = M[i][seqLen2];
                state = 0;
                startI = i;
                startJ = seqLen2;
            }
        }

        for (int j = 0; j <= seqLen2; j++) {
            if (M[seqLen][j] > maxscore) {
                maxscore = M[seqLen][j];
                state = 0;
                startI = seqLen;
                startJ = j;
            }
        }
        double Aliscore = maxscore;
        int i = startI;
        int j = startJ;

        while (i > 0 && j > 0){

            if (state == 0) {

                double score = scoringMatrix.score(seq1.charAt(i-1), seq2.charAt(j-1));

                if (i > 0 && j > 0 && Math.abs(M[i][j] - (M[i-1][j-1] + score))<EPS) {
                    aligned1.append(seq1.charAt(i-1));
                    aligned2.append(seq2.charAt(j-1));
                    i--;
                    j--;
                    state = 0;
                }
                else if (Math.abs(M[i][j] - I[i][j]) < EPS) {
                    state = 1;
                }
                else {
                    state = 2;
                }
            }

            else if (state == 1) {

                aligned1.append(seq1.charAt(i-1));
                aligned2.append('-');

                if (Math.abs(I[i][j] - (M[i-1][j] + gapopen + gapextend))< EPS) {
                    state = 0;
                } else {
                    state = 1;
                }

                i--;
            }

            else {

                aligned1.append('-');
                aligned2.append(seq2.charAt(j-1));

                if (Math.abs(D[i][j] - (M[i][j-1] + gapopen + gapextend))<EPS) {
                    state = 0;
                } else {
                    state = 2;
                }

                j--;
            }
        }

        aligned1.reverse();
        aligned2.reverse();


        this.result = new Alignment(
                seq1.getID(),
                seq2.getID(),
                aligned1.toString(),
                aligned2.toString(),
                Aliscore,
                i,
                startI,
                j,
                startJ,
                seq1,
                seq2,
                "F"
        );
    }

}


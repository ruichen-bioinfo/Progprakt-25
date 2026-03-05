public class GotohGlobal extends Gotoh {
    public GotohGlobal(Sequence seq1, Sequence seq2, Matrix scoringMatrix, GapPenalty gapPenalty) {
        super(seq1, seq2, scoringMatrix, gapPenalty);
    }

    @Override
    public void initMatrix() {

        int negInf = Integer.MIN_VALUE / 4;

        M[0][0] = 0;
        I[0][0] = negInf;
        D[0][0] = negInf;

        for (int i = 1; i <= seqLen; i++) {
            M[i][0] = gapopen + gapextend * i;
            I[i][0] = negInf;
            D[i][0] = negInf;
        }

        for (int j = 1; j <= seqLen2; j++) {
            M[0][j] = gapopen + gapextend * j;
            I[0][j] = negInf;
            D[0][j] = negInf;
        }
    }


    @Override
    public void traceback() {

        StringBuilder aligned1 = new StringBuilder();
        StringBuilder aligned2 = new StringBuilder();

        int i = seqLen;
        int j = seqLen2;

        int state; // 0 = M, 1 = I, 2 = D

        double max = Math.max(Math.max(M[i][j], I[i][j]), D[i][j]);



        if (max == M[i][j]) state = 0;
        else if (max == I[i][j]) state = 1;
        else state = 2;

        while (i > 0 || j > 0) {
            if (i == 0) {
                aligned1.append('-');
                aligned2.append(seq2.charAt(j-1));
                j--;
                state = 2;
                continue;
            }

            if (j == 0) {
                aligned1.append(seq1.charAt(i-1));
                aligned2.append('-');
                i--;
                state = 1;
                continue;
            }

            if (state == 0) {

                int score = scoringMatrix.score(seq1.charAt(i-1), seq2.charAt(j-1));

                if (i > 0 && j > 0 && M[i][j] == M[i-1][j-1] + score) {
                    aligned1.append(seq1.charAt(i-1));
                    aligned2.append(seq2.charAt(j-1));
                    i--;
                    j--;
                    state = 0;
                }
                else if (M[i][j] == I[i][j]) {
                    state = 1;
                }
                else {
                    state = 2;
                }
            }

            else if (state == 1) {

                aligned1.append(seq1.charAt(i-1));
                aligned2.append('-');

                if (I[i][j] == M[i-1][j] + gapopen + gapextend) {
                    state = 0;
                } else {
                    state = 1;
                }

                i--;
            }

            else {

                aligned1.append('-');
                aligned2.append(seq2.charAt(j-1));

                if (D[i][j] == M[i][j-1] + gapopen + gapextend) {
                    state = 0;
                } else {
                    state = 2;
                }

                j--;
            }
        }

        aligned1.reverse();
        aligned2.reverse();

        int score = Math.max(Math.max(M[seqLen][seqLen2], I[seqLen][seqLen2]), D[seqLen][seqLen2]);

        this.result = new Alignment(
                seq1.getID(),
                seq2.getID(),
                aligned1.toString(),
                aligned2.toString(),
                score,
                0,
                seqLen,
                0,
                seqLen2,
                seq1,
                seq2
        );
    }

}
//int Mscore = Math.max(Math.max(I[i-1][j-1], D[i-1][j-1]), M[i-1][j-1]) + score;
//int Iscore = Math.max(I[i-1][j] + gapextend, M[i-1][j] + gapopen + gapextend);
//int Dscore = Math.max(D[i][j-1]+gapextend, M[i][j-1]+gapopen + gapextend);

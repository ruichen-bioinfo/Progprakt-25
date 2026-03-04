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
    public void traceback() {
        StringBuilder aligned1 = new StringBuilder();
        StringBuilder aligned2 = new StringBuilder();
        int current = 0;
        int maxend = Math.max(Math.max(M[seqLen][seqLen2], D[seqLen][seqLen2]), I[seqLen][seqLen2]);
        if (M[seqLen][seqLen2] == maxend) {
            current = 1;
        }
        else if (D[seqLen][seqLen2] == maxend) {
            current = 3;
        }
        else {
            current = 2;
        }
        int i = seqLen;
        int j = seqLen2;
        while (i > 0 || j > 0) {
            if (i == 0) {
                aligned1.append('-');
                aligned2.append(seq2.charAt(j-1));
                j--;
                continue;
            }

            if (j == 0) {
                aligned1.append(seq1.charAt(i-1));
                aligned2.append('-');
                i--;
                continue;
            }

            if (current == 1){
                int score = scoringMatrix.score(seq1.charAt(i-1), seq2.charAt(j-1));
                if (M[i][j] == I[i-1][j-1] + score){
                    current = 2;

                }
                else if (M[i][j] == D[i-1][j-1] + score){
                    current = 3;

                }
                else {
                    current = 1;


                }
                aligned1.append(seq1.charAt(i-1));
                aligned2.append(seq2.charAt(j-1));
                i--;
                j--;
            }
            else if (current == 2){
                if (I[i][j] == I[i-1][j] + gapextend){
                    current = 2;

                }
                else {
                    current = 1;

                }
                aligned1.append(seq1.charAt(i-1));
                aligned2.append('-');
                i--;
            }
            else if (current == 3){
                if (D[i][j] == D[i][j-1] + gapextend){
                    current = 3;

                }
                else{
                    current = 1;
                }
                aligned1.append('-');
                aligned2.append(seq2.charAt(j-1));
                j--;

            }

        }
        aligned1.reverse();
        aligned2.reverse();
        int score = Math.max(Math.max(M[seqLen][seqLen2], I[seqLen][seqLen2]), D[seqLen][seqLen2]);
        this.result = new Alignment(seq1.getID(), seq2.getID(), aligned1.toString(), aligned2.toString(), score, 0, seqLen, 0, seqLen2);
    }

}
//int Mscore = Math.max(Math.max(I[i-1][j-1], D[i-1][j-1]), M[i-1][j-1]) + score;
//int Iscore = Math.max(I[i-1][j] + gapextend, M[i-1][j] + gapopen + gapextend);
//int Dscore = Math.max(D[i][j-1]+gapextend, M[i][j-1]+gapopen + gapextend);

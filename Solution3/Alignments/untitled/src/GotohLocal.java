public class GotohLocal extends Gotoh {
    public GotohLocal(Sequence seq1, Sequence seq2, Matrix scoringMatrix, GapPenalty gapPenalty) {
        super(seq1, seq2, scoringMatrix, gapPenalty);
    }
    protected String prefix1;
    protected String prefix2;
    protected String suffix1;
    protected String suffix2;

    @Override
    public void initMatrix() {
        int zero = 0;
        int neginf = Integer.MIN_VALUE / 2;

        M[0][0] = 0;
        I[0][0] = neginf;
        D[0][0] = neginf;

        for (int i = 1; i <= seqLen; i++){
            M[i][0] = zero;
            D[i][0] = neginf;
            I[i][0] = neginf;
        }

        for (int j = 1; j <= seqLen2; j++){
            M[0][j] = zero;
            D[0][j] = neginf;
            I[0][j] = neginf;
        }

    }

    @Override
    protected int adjust(int value){
        return Math.max(0, value);
    }




    @Override
    public void traceback() {
        StringBuilder aligned1 = new StringBuilder();
        StringBuilder aligned2 = new StringBuilder();
        int current = 0;
        int maxscore = Integer.MIN_VALUE;
        int currentscoreM = 0;
        int currentscoreD = 0;
        int currentscoreI = 0;
        int startI = 0;
        int startJ = 0;

        for (int i = 0; i <= seqLen; i++) {
            for (int j = 0; j <= seqLen2; j++) {
                if (M[i][j] > maxscore) {
                    maxscore = M[i][j];
                    current = 1;
                    startI = i;
                    startJ = j;
                }
                if (I[i][j] > maxscore){
                    maxscore = I[i][j];
                    current = 2;
                    startI = i;
                    startJ = j;
                }
                if (D[i][j] > maxscore){
                    maxscore = D[i][j];
                    current = 3;
                    startI = i;
                    startJ = j;
                }
            }
        }
        int Aliscore = maxscore;

        int i = startI;
        int j = startJ;
        int endI = 0;
        int endJ = 0;
        while (true) {
            if (current == 1 && M[i][j] == 0) break;
            if (current == 2 && I[i][j] == 0) break;
            if (current == 3 && D[i][j] == 0) break;
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
                if (M[i][j] == M[i-1][j-1] + score) {
                    current = 1;
                    aligned1.append(seq1.charAt(i-1));
                    aligned2.append(seq2.charAt(j-1));
                    i--;
                    j--;
                }
                else if (M[i][j] == D[i][j]) {
                    current = 3;
                }
                else {
                    current = 2;
                }

            }
            else if (current == 2){
                if (I[i][j] == I[i-1][j] + gapextend){
                    current = 2;
                }
                else if (I[i][j] == M[i-1][j] + gapopen + gapextend){
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
                else if (D[i][j] == M[i][j-1] + gapopen + gapextend){
                    current = 1;
                }
                aligned1.append('-');
                aligned2.append(seq2.charAt(j-1));
                j--;
            }



        }
        endJ = j;
        endI = i;
        aligned1.reverse();
        aligned2.reverse();
        String seq1string = seq1.getSequence();
        String seq2string = seq2.getSequence();
        String prefix1 = seq1string.substring(0,endI);
        String prefix2 = seq2string.substring(0,endJ);
        String suffix1 = seq1string.substring(startI,seqLen);
        String suffix2 = seq2string.substring(startJ,seqLen2);
        int alignstart1 = endI;
        int alignstart2 = endJ;
        int alignend1 = startI;
        int alignend2 = startJ;



        this.result = new Alignment(seq1.getID(), seq2.getID(), aligned1.toString(), aligned2.toString(), Aliscore, alignstart1, alignend1, alignstart2, alignend2, seq1, seq2);
        this.prefix1 = prefix1;
        this.prefix2 = prefix2;
        this.suffix1 = suffix1;
        this.suffix2 = suffix2;
    }
}

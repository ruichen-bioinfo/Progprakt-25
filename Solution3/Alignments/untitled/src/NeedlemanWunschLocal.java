public class NeedlemanWunschLocal extends NeedlemanWunsch {

    private int bestI;
    private int bestJ;

    public NeedlemanWunschLocal(Sequence seq1, Sequence seq2, Matrix scoringMatrix, GapPenalty gapPenalty) {
        super(seq1, seq2, scoringMatrix, gapPenalty);
    }

    @Override
    protected void initMatrix() {
        int n = seq1.getSequence().length();
        int m = seq2.getSequence().length();

        dp = new double[n + 1][m + 1];
        bestI = 0;
        bestJ = 0;
    }

    @Override
    protected double computeCellValue(int i, int j) {
        double diag = diag(i, j);
        double up = up(i, j);
        double left = left(i, j);

        double val = Math.max(0.0, Math.max(diag, Math.max(up, left)));

        if (val > dp[bestI][bestJ]) {
            bestI = i;
            bestJ = j;
        }

        return val;
    }

    @Override
    protected void traceback() {
        int i = bestI;
        int j = bestJ;

        StringBuilder a1 = new StringBuilder();
        StringBuilder a2 = new StringBuilder();

        while (i > 0 && j > 0 && dp[i][j] > 1e-12) {
            double cur = dp[i][j];
            if (eq(cur, dp[i - 1][j - 1] + score(i - 1, j - 1))) {
                a1.append(seq1.charAt(i - 1));
                a2.append(seq2.charAt(j - 1));
                i--;
                j--;
            } else if (eq(cur, dp[i - 1][j] + gap)) {
                a1.append(seq1.charAt(i - 1));
                a2.append('-');
                i--;
            } else {
                a1.append('-');
                a2.append(seq2.charAt(j - 1));
                j--;
            }
        }

        String aligned1 = a1.reverse().toString();
        String aligned2 = a2.reverse().toString();
        double finalScore = dp[bestI][bestJ];

        int startI = i;
        int startJ = j;
        int endI = bestI;
        int endJ = bestJ;


        result = new Alignment(seq1.getID(), seq2.getID(), aligned1, aligned2, finalScore, startI, endI, startJ, endJ, seq1, seq2, "L");
    }
}
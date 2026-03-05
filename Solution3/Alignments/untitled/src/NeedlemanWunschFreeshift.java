public class NeedlemanWunschFreeshift extends NeedlemanWunsch {

    private int bestI;
    private int bestJ;

    public NeedlemanWunschFreeshift(Sequence seq1, Sequence seq2, Matrix scoringMatrix, GapPenalty gapPenalty) {
        super(seq1, seq2, scoringMatrix, gapPenalty);
    }

    @Override
    protected void initMatrix() {
        int n = seq1.getSequence().length();
        int m = seq2.getSequence().length();

        dp = new int[n + 1][m + 1];

        // keine Strafe für führende Gaps
        for (int i = 0; i <= n; i++) dp[i][0] = 0;
        for (int j = 0; j <= m; j++) dp[0][j] = 0;

        bestI = n;
        bestJ = m;
    }

    @Override
    protected int computeCellValue(int i, int j) {
        int diag = diag(i, j);
        int up = up(i, j);
        int left = left(i, j);
        return Math.max(diag, Math.max(up, left));
    }

    @Override
    protected void fillMatrix() {
        super.fillMatrix();

        int n = seq1.getSequence().length();
        int m = seq2.getSequence().length();

        // bestes Ende liegt in letzter Zeile oder letzter Spalte
        int bestScore = Integer.MIN_VALUE;

        for (int j = 0; j <= m; j++) {
            if (dp[n][j] > bestScore) {
                bestScore = dp[n][j];
                bestI = n;
                bestJ = j;
            }
        }
        for (int i = 0; i <= n; i++) {
            if (dp[i][m] > bestScore) {
                bestScore = dp[i][m];
                bestI = i;
                bestJ = m;
            }
        }
    }

    @Override
    protected void traceback() {
        int i = bestI;
        int j = bestJ;

        StringBuilder a1 = new StringBuilder();
        StringBuilder a2 = new StringBuilder();

        // Traceback bis zum Rand
        while (i > 0 && j > 0) {
            if (dp[i][j] == dp[i - 1][j - 1] + score(i - 1, j - 1)) {
                a1.append(seq1.charAt(i - 1));
                a2.append(seq2.charAt(j - 1));
                i--;
                j--;
            } else if (dp[i][j] == dp[i - 1][j] + gap) {
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
        int finalScore = dp[bestI][bestJ];

        int startI = i;
        int startJ = j;
        int endI = bestI;
        int endJ = bestJ;

        result = new Alignment(seq1.getID(), seq2.getID(),
                aligned1, aligned2,
                finalScore,
                startI, endI, startJ, endJ,
                seq1, seq2);
    }
}
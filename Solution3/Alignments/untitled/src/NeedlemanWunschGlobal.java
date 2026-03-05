public class NeedlemanWunschGlobal extends NeedlemanWunsch {

    public NeedlemanWunschGlobal(Sequence seq1, Sequence seq2, Matrix scoringMatrix, GapPenalty gapPenalty) {
        super(seq1, seq2, scoringMatrix, gapPenalty);
    }

    @Override
    protected void initMatrix() {
        int n = seq1.getSequence().length();
        int m = seq2.getSequence().length();

        dp = new double[n + 1][m + 1];

        dp[0][0] = 0;
        for (int i = 1; i <= n; i++) dp[i][0] = dp[i - 1][0] + gap;
        for (int j = 1; j <= m; j++) dp[0][j] = dp[0][j - 1] + gap;
    }

    @Override
    protected double computeCellValue(int i, int j) {
        double diag = diag(i, j);
        double up = up(i, j);
        double left = left(i, j);
        return Math.max(diag, Math.max(up, left));
    }

    @Override
    protected void traceback() {
        int i = seq1.getSequence().length();
        int j = seq2.getSequence().length();

        StringBuilder a1 = new StringBuilder();
        StringBuilder a2 = new StringBuilder();

        while (i > 0 || j > 0) {
            if (i > 0 && j > 0 && dp[i][j] == dp[i - 1][j - 1] + score(i - 1, j - 1)) {
                a1.append(seq1.charAt(i - 1));
                a2.append(seq2.charAt(j - 1));
                i--;
                j--;
            } else if (i > 0 && dp[i][j] == dp[i - 1][j] + gap) {
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
        double finalScore = dp[seq1.getSequence().length()][seq2.getSequence().length()];

        int n = seq1.getSequence().length();
        int m = seq2.getSequence().length();

        int startI = 0, endI = n;
        int startJ = 0, endJ = m;

        result = new Alignment(seq1.getID(), seq2.getID(), aligned1, aligned2, finalScore,startI, endI, startJ, endJ, seq1, seq2,"G");
    }
}
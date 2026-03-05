public abstract class NeedlemanWunsch extends AlignmentAlgorithm {

    protected double[][] dp;
    protected final int gap; // linear gap

    public NeedlemanWunsch(Sequence seq1, Sequence seq2, Matrix scoringMatrix, GapPenalty gapPenalty) {
        super(seq1, seq2, scoringMatrix, gapPenalty);
        this.gap = gapPenalty.getExtend(); // NW nutzt nur einen konstanten gap
    }

    @Override
    protected void fillMatrix() {
        int n = seq1.getSequence().length();
        int m = seq2.getSequence().length();

        for (int i = 1; i <= n; i++) {
            for (int j = 1; j <= m; j++) {
                dp[i][j] = computeCellValue(i, j);
            }
        }
    }

    // i/j sind dp-Indizes (1..n / 1..m)
    protected abstract double computeCellValue(int i, int j);

    protected double diag(int i, int j) {
        return dp[i - 1][j - 1] + score(i - 1, j - 1);
    }

    protected double up(int i, int j) {
        return dp[i - 1][j] + gap;
    }

    protected double left(int i, int j) {
        return dp[i][j - 1] + gap;
    }
}
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

        dp = new int[n + 1][m + 1];
        bestI = 0;
        bestJ = 0;
    }

    @Override
    protected int computeCellValue(int i, int j) {
        int diag = diag(i, j);
        int up = up(i, j);
        int left = left(i, j);

        int val = Math.max(0, Math.max(diag, Math.max(up, left)));

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

        while (i > 0 && j > 0 && dp[i][j] > 0) {
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

        result = new Alignment(seq1.getID(), seq2.getID(), aligned1, aligned2, finalScore);
    }
}
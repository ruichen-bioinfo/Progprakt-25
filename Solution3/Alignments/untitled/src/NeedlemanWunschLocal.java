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

        int startI = i;
        int startJ = j;
        int endI = bestI;
        int endJ = bestJ;

        String s1 = seq1.getSequence();
        String s2 = seq2.getSequence();

        String pre1 = s1.substring(0, startI);
        String pre2 = s2.substring(0, startJ);
        String suf1 = s1.substring(endI);
        String suf2 = s2.substring(endJ);

        int preLen = Math.max(pre1.length(), pre2.length());
        int sufLen = Math.max(suf1.length(), suf2.length());

        StringBuilder full1 = new StringBuilder();
        StringBuilder full2 = new StringBuilder();

// Prefix auf gleiche Länge
        full1.append(pre1);
        full1.append(repeat('-', preLen - pre1.length()));

        full2.append(pre2);
        full2.append(repeat('-', preLen - pre2.length()));

// lokaler Teil
        full1.append(aligned1);
        full2.append(aligned2);

// Suffix auf gleiche Länge
        full1.append(suf1);
        full1.append(repeat('-', sufLen - suf1.length()));

        full2.append(suf2);
        full2.append(repeat('-', sufLen - suf2.length()));

        aligned1 = full1.toString();
        aligned2 = full2.toString();


        result = new Alignment(seq1.getID(), seq2.getID(), aligned1, aligned2, finalScore, startI, endI, startJ, endJ, seq1, seq2);
    }
    private static String repeat(char c, int n) {
        if (n <= 0) return "";
        char[] arr = new char[n];
        java.util.Arrays.fill(arr, c);
        return new String(arr);
    }
}
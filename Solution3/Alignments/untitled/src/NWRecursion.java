public class NWRecursion {

    private static final int MATCH = 3;
    private static final int MISMATCH = -2;
    private static final int GAP = -4;

    private static int s(char a, char b) {
        return (a == b) ? MATCH : MISMATCH;
    }

    // f(i,j): bester Score für x[0..i-1] vs y[0..j-1]
    public static int f(String x, String y, int i, int j) {
        if (i == 0 && j == 0) return 0;
        if (i == 0) return j * GAP;
        if (j == 0) return i * GAP;

        int diag = f(x, y, i - 1, j - 1) + s(x.charAt(i - 1), y.charAt(j - 1));
        int up   = f(x, y, i - 1, j) + GAP;
        int left = f(x, y, i, j - 1) + GAP;

        return Math.max(diag, Math.max(up, left));
    }
}
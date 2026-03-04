public class CheckScore {

    // berechnet den Score für ein fertiges Alignment (mit '-' als Gap)
    public static int score(Alignment ali, Matrix matrix, GapPenalty gapPenalty) {
        String a1 = ali.getAligned1();
        String a2 = ali.getAligned2();

        int total = 0;
        int i = 0;

        while (i < a1.length()) {
            char c1 = a1.charAt(i);
            char c2 = a2.charAt(i);

            // Gap-Run in seq2
            if (c2 == '-' && c1 != '-') {
                int len = 0;
                while (i < a1.length() && a2.charAt(i) == '-' && a1.charAt(i) != '-') {
                    len++;
                    i++;
                }
                total += gapPenalty.cost(len);
                continue;
            }

            // Gap-Run in seq1
            if (c1 == '-' && c2 != '-') {
                int len = 0;
                while (i < a1.length() && a1.charAt(i) == '-' && a2.charAt(i) != '-') {
                    len++;
                    i++;
                }
                total += gapPenalty.cost(len);
                continue;
            }

            // beide Buchstaben
            if (c1 != '-' && c2 != '-') {
                total += matrix.score(c1, c2);
            }
            // fall "--" wird ignoriert

            i++;
        }

        return total;
    }
}
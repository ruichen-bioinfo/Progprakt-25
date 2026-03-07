public class Output {

    public static void print(Alignment ali,String format) {
        if (format == null || "scores".equals(format)) {
            printScores(ali);
        } else if ("ali".equals(format)) {
            printAli(ali);
        } else if ("html".equals(format)) {
            printHtml(ali);
        } else throw new IllegalArgumentException("Unknown format " + format);
    }

    public static void printScores(Alignment ali) {
        System.out.println(ali.getId1() + " " + ali.getId2() + " " + ali.getScore());
    }
//test
public static void printAli(Alignment ali) {

    String seq1 = ali.getSeq1();
    String seq2 = ali.getSeq2();

    String mode = ali.getMode();

    String a1 = ali.getAligned1();
    String a2 = ali.getAligned2();

    int startI = ali.getStartI();
    int endI   = ali.getEndI();
    int startJ = ali.getStartJ();
    int endJ   = ali.getEndJ();

    String pre1 = seq1.substring(0, startI);
    String pre2 = seq2.substring(0, startJ);

    String suf1 = seq1.substring(endI);
    String suf2 = seq2.substring(endJ);

    StringBuilder full1 = new StringBuilder();
    StringBuilder full2 = new StringBuilder();

    if("L".equals(mode)) {

        full1.append(pre1);
        full2.append("-".repeat(pre1.length()));

        full1.append("-".repeat(pre2.length()));
        full2.append(pre2);

        full1.append(a1);
        full2.append(a2);

        full1.append(suf1);
        full2.append("-".repeat(suf1.length()));

        full1.append("-".repeat(suf2.length()));
        full2.append(suf2);
    }
    else {


        // Prefix ausgleichen
        int maxPre = Math.max(pre1.length(), pre2.length());
        full1.append("-".repeat(maxPre - pre1.length())).append(pre1);
        full2.append("-".repeat(maxPre - pre2.length())).append(pre2);

        // Alignment
        full1.append(a1);
        full2.append(a2);

        // Suffix ausgleichen
        int maxSuf = Math.max(suf1.length(), suf2.length());
        full1.append(suf1).append("-".repeat(maxSuf - suf1.length()));
        full2.append(suf2).append("-".repeat(maxSuf - suf2.length()));

    }

    System.out.println(">" + ali.getId1() + " " + ali.getId2() + " " + ali.getScore());
    System.out.println(ali.getId1() + ": " + full1);
    System.out.println(ali.getId2() + ": " + full2);
}

    public static void printHtml(Alignment ali) {

        String seq1 = ali.getSeq1();
        String seq2 = ali.getSeq2();

        String a1 = ali.getAligned1();
        String a2 = ali.getAligned2();

        int startI = ali.getStartI();
        int endI   = ali.getEndI();
        int startJ = ali.getStartJ();
        int endJ   = ali.getEndJ();

        String pre1 = seq1.substring(0, startI);
        String pre2 = seq2.substring(0, startJ);

        String suf1 = seq1.substring(endI);
        String suf2 = seq2.substring(endJ);

        StringBuilder full1 = new StringBuilder();
        StringBuilder full2 = new StringBuilder();

        int maxPre = Math.max(pre1.length(), pre2.length());
        full1.append("-".repeat(maxPre - pre1.length())).append(pre1);
        full2.append("-".repeat(maxPre - pre2.length())).append(pre2);

        full1.append(a1);
        full2.append(a2);

        int maxSuf = Math.max(suf1.length(), suf2.length());
        full1.append(suf1).append("-".repeat(maxSuf - suf1.length()));
        full2.append(suf2).append("-".repeat(maxSuf - suf2.length()));

        String f1 = full1.toString();
        String f2 = full2.toString();

        int matches = 0;
        for (int i = 0; i < f1.length(); i++) {
            char c1 = f1.charAt(i);
            char c2 = f2.charAt(i);
            if (c1 != '-' && c2 != '-' && c1 == c2) matches++;
        }

        int idPct = f1.length() == 0 ? 0 : (int)Math.round(100.0 * matches / f1.length());

        System.out.println("<html><body>");
        System.out.println("<h3>" + esc(ali.getId1()) + " vs " + esc(ali.getId2()) + "</h3>");

        System.out.println("<p>");
        System.out.println("Score: " + ali.getScore() + "<br>");
        System.out.println("Alignment length: " + f1.length() + "<br>");
        System.out.println("Matches: " + matches + "<br>");
        System.out.println("Identity: " + idPct + "%<br>");
        System.out.println("Start/End (i): " + startI + " .. " + endI + "<br>");
        System.out.println("Start/End (j): " + startJ + " .. " + endJ);
        System.out.println("</p>");

        System.out.println("<pre>");
        System.out.println(esc(f1));
        System.out.println(matchLine(f1, f2));
        System.out.println(esc(f2));
        System.out.println("</pre>");

        System.out.println("</body></html>");
    }

    private static String matchLine(String a1, String a2) {
        StringBuilder sb = new StringBuilder(a1.length());
        for (int i = 0; i < a1.length(); i++) {
            char c1 = a1.charAt(i);
            char c2 = a2.charAt(i);
            sb.append((c1 != '-' && c1 == c2) ? '|' : ' ');
        }
        return sb.toString();
    }
    private static String esc(String s) {
        if (s == null) return "";
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;");
    }
}

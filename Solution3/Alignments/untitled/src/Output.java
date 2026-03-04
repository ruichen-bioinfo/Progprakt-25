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

    public static void printAli(Alignment ali) {
        String seq1 = ali.getSeq1();
        String seq2 = ali.getSeq2();

        String a1 = ali.getAligned1();
        String a2 = ali.getAligned2();

        int startI = ali.getStartI();
        int endI   = ali.getEndI();
        int startJ = ali.getStartJ();
        int endJ   = ali.getEndJ();

        String prefix1 = seq1.substring(0, startI);
        String prefix2 = seq2.substring(0, startJ);

        int diff = prefix1.length() - prefix2.length();

        if (diff > 0) {
            prefix2 = "-".repeat(diff) + prefix2;
        } else if (diff < 0) {
            prefix1 = "-".repeat(-diff) + prefix1;
        }

        String suffix1 = seq1.substring(endI);
        String suffix2 = seq2.substring(endJ);

        diff = suffix1.length() - suffix2.length();

        if (diff > 0) {
            suffix2 = suffix2 + "-".repeat(diff);
        } else if (diff < 0) {
            suffix1 = suffix1 + "-".repeat(-diff);
        }

        String full1 = prefix1 + a1 + suffix1;
        String full2 = prefix2 + a2 + suffix2;

        System.out.println(">" + ali.getId1() + " " + ali.getId2() + " " + ali.getScore());
        System.out.println(ali.getId1() + ": " + full1);
        System.out.println(ali.getId2() + ": " + full2);
    }

    public static void printHtml(Alignment ali) {
        String a1 = ali.getAligned1();
        String a2 = ali.getAligned2();

        int matches = 0;
        int alignedLen = a1.length();
        for (int i = 0; i < alignedLen; i++) {
            char c1 = a1.charAt(i);
            char c2 = a2.charAt(i);
            if (c1 != '-' && c2 != '-' && c1 == c2) {
                matches++;
            }
        }
        int idPct = alignedLen == 0 ? 0 : (int) Math.round(100.0 * matches / alignedLen);

        System.out.println("<html><body>");
        System.out.println("<h3>" + ali.getId1() + " vs " + ali.getId2() + "</h3>");
        System.out.println("<p>");
        System.out.println("Score: " + ali.getScore() + "<br>");
        System.out.println("Alignment length: " + alignedLen + "<br>");
        System.out.println("Matches: " + matches + "<br>");
        System.out.println("Identity: " + idPct + "%<br>");
        System.out.println("Start/End (i): " + ali.getStartI() + " .. " + ali.getEndI() + "<br>");
        System.out.println("Start/End (j): " + ali.getStartJ() + " .. " + ali.getEndJ());
        System.out.println("</p>");

        System.out.println("<pre>");
        System.out.println(a1);
        System.out.println(matchLine(a1, a2));
        System.out.println(a2);
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

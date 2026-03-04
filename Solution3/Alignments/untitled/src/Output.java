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
        System.out.println(ali.getId1() + "" + ali.getId2() + "" + ali.getScore());
    }

    public static void printAli(Alignment ali) {
        System.out.println(">" + ali.getId1() + "" + ali.getId2() + "" + ali.getScore());
        System.out.println(ali.getId1() + ": " + ali.getAligned1());
        System.out.println(ali.getId2() + ": " + ali.getAligned2());
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

import java.io.*;
import java.util.*;

/**
 * validateGor - Validates GOR secondary structure predictions against reference structures.
 *
 * Usage:
 *   java -jar validateGor.jar -p <predictions> -r <seclib-file> -s <summary file> -d <detailed file> [-f <txt|html>]
 */
public class validateGor {

    // -------------------------------------------------------------------------
    // Data container for one protein entry
    // -------------------------------------------------------------------------
    static class ProteinEntry {
        String id;
        String sequence;
        String predicted;
        String reference;
    }

    // -------------------------------------------------------------------------
    // Validation scores for one protein
    // Scores are in range [0,100] (percentages). NaN means "no residues of that state".
    // -------------------------------------------------------------------------
    static class Scores {
        String id;
        double q3;
        double qH, qE, qC;       // NaN if no residues of that state in reference
        double sov;
        double sovH, sovE, sovC; // NaN if no residues of that state in reference
    }

    // -------------------------------------------------------------------------
    // Main
    // -------------------------------------------------------------------------
    public static void main(String[] args) {
        String predFile = null, refFile = null, summaryFile = null, detailedFile = null, format = "txt";
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "-p": predFile     = args[++i]; break;
                case "-r": refFile      = args[++i]; break;
                case "-s": summaryFile  = args[++i]; break;
                case "-d": detailedFile = args[++i]; break;
                case "-f": format       = args[++i]; break;
            }
        }
        if (predFile == null || refFile == null || summaryFile == null || detailedFile == null) {
            printHelp();
            System.exit(1);
        }

        try {
            Map<String, String[]> predictions = loadPredictions(predFile);
            Map<String, String[]> references  = loadSeclib(refFile);

            List<ProteinEntry> entries = matchEntries(predictions, references);
            if (entries.isEmpty()) {
                System.err.println("Warning: No matching IDs found between prediction and reference files.");
                System.exit(1);
            }

            List<Scores> allScores = new ArrayList<>();
            for (ProteinEntry e : entries) {
                Scores s = computeScores(e);
                s.id = e.id;
                allScores.add(s);
            }

            writeDetailed(entries, allScores, detailedFile, format);
            writeSummary(allScores, summaryFile);

            System.out.println("Validation complete. " + entries.size() + " proteins processed.");

        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }

    static void printHelp() {
        System.out.println("Usage: java -jar validateGor.jar -p <predictions> -r <seclib-file>");
        System.out.println("                                  -s <summary file> -d <detailed file>");
        System.out.println("                                  [-f <txt|html>]");
    }

    // -------------------------------------------------------------------------
    // File parsers
    // -------------------------------------------------------------------------

    /**
     * Parse predict.jar txt output.
     * Format per entry:
     *   >id
     *   AS <sequence>
     *   PS <predicted SS>
     */
    static Map<String, String[]> loadPredictions(String filename) throws IOException {
        Map<String, String[]> map = new LinkedHashMap<>();
        try (BufferedReader br = new BufferedReader(new FileReader(filename))) {
            String line;
            String id = null, seq = null, ps = null;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.startsWith(">")) {
                    if (id != null && seq != null && ps != null) map.put(id, new String[]{seq, ps});
                    id = line.substring(1).trim().split("\\s+")[0];
                    seq = null; ps = null;
                } else if (line.startsWith("AS ")) {
                    seq = line.substring(3).trim();
                } else if (line.startsWith("PS ")) {
                    ps = line.substring(3).trim();
                }
            }
            if (id != null && seq != null && ps != null) map.put(id, new String[]{seq, ps});
        }
        return map;
    }

    /**
     * Parse seclib reference file.
     * Format per entry:
     *   > id
     *   AS <sequence>
     *   SS <secondary structure>
     */
    static Map<String, String[]> loadSeclib(String filename) throws IOException {
        Map<String, String[]> map = new LinkedHashMap<>();
        try (BufferedReader br = new BufferedReader(new FileReader(filename))) {
            String line;
            String id = null, seq = null, ss = null;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.startsWith(">")) {
                    if (id != null && seq != null && ss != null) map.put(id, new String[]{seq, ss});
                    id = line.substring(1).trim().split("\\s+")[0];
                    seq = null; ss = null;
                } else if (line.startsWith("AS ")) {
                    seq = line.substring(3).trim();
                } else if (line.startsWith("SS ")) {
                    ss = line.substring(3).trim();
                }
            }
            if (id != null && seq != null && ss != null) map.put(id, new String[]{seq, ss});
        }
        return map;
    }

    static List<ProteinEntry> matchEntries(Map<String, String[]> predictions,
                                           Map<String, String[]> references) {
        List<ProteinEntry> entries = new ArrayList<>();
        for (String id : predictions.keySet()) {
            if (!references.containsKey(id)) {
                System.err.println("Warning: ID " + id + " not found in reference file, skipping.");
                continue;
            }
            String[] pred = predictions.get(id);
            String[] ref  = references.get(id);

            ProteinEntry e = new ProteinEntry();
            e.id        = id;
            e.sequence  = pred[0];
            e.predicted = pred[1];
            e.reference = ref[1];

            if (e.predicted.length() != e.reference.length()) {
                System.err.println("Warning: Length mismatch for " + id +
                        " (pred=" + e.predicted.length() + ", ref=" + e.reference.length() + "), skipping.");
                continue;
            }
            entries.add(e);
        }
        return entries;
    }

    // -------------------------------------------------------------------------
    // Score computation
    // -------------------------------------------------------------------------

    static Scores computeScores(ProteinEntry e) {
        // Strip positions where PS=='-': only evaluate predicted region
        StringBuilder mPred = new StringBuilder();
        StringBuilder mRef  = new StringBuilder();
        int n = Math.min(e.predicted.length(), e.reference.length());
        for (int i = 0; i < n; i++) {
            char p = e.predicted.charAt(i);
            if (p == '-') continue;
            mPred.append(p);
            mRef.append(e.reference.charAt(i));
        }
        String pred = mPred.toString();
        String ref  = mRef.toString();

        Scores s = new Scores();
        s.q3   = computeQ3(pred, ref);
        s.qH   = computeQstate(pred, ref, 'H');
        s.qE   = computeQstate(pred, ref, 'E');
        s.qC   = computeQstate(pred, ref, 'C');
        s.sov  = computeSOV(pred, ref, '\0');
        s.sovH = computeSOV(pred, ref, 'H');
        s.sovE = computeSOV(pred, ref, 'E');
        s.sovC = computeSOV(pred, ref, 'C');
        return s;
    }

    /** Q3: overall per-residue accuracy (0-100) */
    static double computeQ3(String pred, String ref) {
        int correct = 0;
        int total = Math.min(pred.length(), ref.length());
        for (int i = 0; i < total; i++) {
            if (pred.charAt(i) == ref.charAt(i)) correct++;
        }
        return total == 0 ? Double.NaN : 100.0 * correct / total;
    }

    /** Per-state accuracy (0-100). Returns NaN if no residues of that state in reference. */
    static double computeQstate(String pred, String ref, char state) {
        int correct = 0, total = 0;
        for (int i = 0; i < Math.min(pred.length(), ref.length()); i++) {
            if (ref.charAt(i) == state) {
                total++;
                if (pred.charAt(i) == state) correct++;
            }
        }
        return total == 0 ? Double.NaN : 100.0 * correct / total;
    }

    /**
     * SOV score (Zemla et al. 1999), result in [0,100].
     * Operates on gap-stripped sequences.
     * stateFilter=='\0' means all states combined.
     * Returns NaN if no residues of that state in reference.
     *
     *   SOV(i) = 100 * (1/N(i)) * sum_{S(i)} [ (minov+delta)/maxov * len(s1) ]
     *   N(i)   = sum of len(s1) for ALL ref segments of state i
     *   delta  = min( maxov-minov, minov, len(s1)/2, len(s2)/2 )
     */
    static double computeSOV(String pred, String ref, char stateFilter) {
        int n = Math.min(pred.length(), ref.length());
        List<int[]> refSegs  = getSegments(ref,  n);
        List<int[]> predSegs = getSegments(pred, n);

        double numerator   = 0.0;
        long   denominator = 0;

        for (int[] rs : refSegs) {
            char state = (char) rs[2];
            if (stateFilter != '\0' && state != stateFilter) continue;

            int rsLen = rs[1] - rs[0] + 1;
            boolean hasOverlap = false;

            for (int[] ps : predSegs) {
                if ((char) ps[2] != state) continue;
                int minov = Math.min(rs[1], ps[1]) - Math.max(rs[0], ps[0]) + 1;
                if (minov <= 0) continue;

                hasOverlap = true;
                int psLen = ps[1] - ps[0] + 1;
                int maxov = Math.max(rs[1], ps[1]) - Math.min(rs[0], ps[0]) + 1;
                int delta = Math.min(
                        Math.min(maxov - minov, minov),
                        Math.min(rsLen / 2, psLen / 2)
                );
                delta = Math.max(0, delta);
                numerator   += (double)(minov + delta) / maxov * rsLen;
                denominator += rsLen; // len(s1) counted once per overlapping pair
            }

            if (!hasOverlap) {
                denominator += rsLen; // S'(i): no overlapping pred seg
            }
        }

        return denominator == 0 ? Double.NaN : 100.0 * numerator / denominator;
    }

    /**
     * Extract segments from a secondary structure string.
     * Returns list of [start, end, stateChar] (inclusive, 0-based).
     * Skips '-' positions.
     */
    static List<int[]> getSegments(String ss, int n) {
        List<int[]> segs = new ArrayList<>();
        int i = 0;
        while (i < n) {
            char c = ss.charAt(i);
            if (c == '-') { i++; continue; }
            int start = i;
            while (i < n && ss.charAt(i) == c) i++;
            segs.add(new int[]{start, i - 1, c});
        }
        return segs;
    }

    // -------------------------------------------------------------------------
    // Output writers
    // -------------------------------------------------------------------------

    /** Format a score value: "-" if NaN, else "%.1f" */
    static String fmt(double v) {
        if (Double.isNaN(v)) return "  -  ";
        return String.format(Locale.US, "%5.1f", v);
    }

    static void writeDetailed(List<ProteinEntry> entries, List<Scores> allScores,
                              String filename, String format) throws IOException {
        try (PrintWriter pw = new PrintWriter(new FileWriter(filename))) {
            if (format.equals("html")) {
                writeDetailedHtml(entries, allScores, pw);
            } else {
                writeDetailedTxt(entries, allScores, pw);
            }
        }
    }

    static void writeDetailedTxt(List<ProteinEntry> entries, List<Scores> allScores,
                                 PrintWriter pw) {
        for (int i = 0; i < entries.size(); i++) {
            ProteinEntry e = entries.get(i);
            Scores s = allScores.get(i);
            // Match reference format: "> id  Q3  SOV  QH  QE  QC  SOV_H  SOV_E  SOV_C "
            pw.printf("> %s %s %s %s %s %s %s %s %s %n",
                    e.id,
                    fmt(s.q3), fmt(s.sov),
                    fmt(s.qH), fmt(s.qE), fmt(s.qC),
                    fmt(s.sovH), fmt(s.sovE), fmt(s.sovC));
            pw.println("AS " + e.sequence);
            pw.println("PS " + e.predicted);
            pw.println("SS " + e.reference);
            pw.println();
        }
    }

    static void writeDetailedHtml(List<ProteinEntry> entries, List<Scores> allScores,
                                  PrintWriter pw) {
        pw.println("<!DOCTYPE html><html><head><meta charset='UTF-8'>");
        pw.println("<title>GOR Validation Results</title>");
        pw.println("<style>");
        pw.println("body{font-family:monospace;background:#f5f5f5;padding:20px;}");
        pw.println("table{border-collapse:collapse;width:100%;margin-bottom:20px;}");
        pw.println("th,td{border:1px solid #ccc;padding:6px 10px;text-align:left;}");
        pw.println("th{background:#3a6ea5;color:white;}");
        pw.println("tr:nth-child(even){background:#eef2f7;}");
        pw.println(".H{color:#e74c3c;font-weight:bold;}.E{color:#2980b9;font-weight:bold;}.C{color:#27ae60;}");
        pw.println(".seq-block{background:#fff;border:1px solid #ddd;padding:10px;margin:10px 0;border-radius:4px;}");
        pw.println(".correct{background:#d5f5e3;}.wrong{background:#fadbd8;}");
        pw.println("</style></head><body>");
        pw.println("<h1>GOR Validation Results</h1>");
        pw.println("<p>Total proteins: " + entries.size() + "</p>");

        pw.println("<h2>Per-Protein Scores</h2>");
        pw.println("<table><tr><th>ID</th><th>Q3</th><th>SOV</th><th>QH</th><th>QE</th><th>QC</th><th>SOV_H</th><th>SOV_E</th><th>SOV_C</th></tr>");
        for (int i = 0; i < entries.size(); i++) {
            Scores s = allScores.get(i);
            pw.printf("<tr><td><a href='#%s'>%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>%n",
                    s.id, s.id,
                    fmt(s.q3), fmt(s.sov),
                    fmt(s.qH), fmt(s.qE), fmt(s.qC),
                    fmt(s.sovH), fmt(s.sovE), fmt(s.sovC));
        }
        pw.println("</table>");

        pw.println("<h2>Detailed Predictions</h2>");
        for (int i = 0; i < entries.size(); i++) {
            ProteinEntry e = entries.get(i);
            Scores s = allScores.get(i);
            pw.printf("<div class='seq-block' id='%s'>%n", e.id);
            pw.printf("<h3>%s &mdash; Q3=%s, SOV=%s</h3>%n", e.id, fmt(s.q3), fmt(s.sov));
            pw.println("<pre>");
            pw.print("AS "); pw.println(e.sequence);
            pw.print("PS ");
            for (int j = 0; j < e.predicted.length(); j++) {
                char p = e.predicted.charAt(j);
                char r = j < e.reference.length() ? e.reference.charAt(j) : '?';
                String cls = (p == r) ? "correct" : "wrong";
                pw.printf("<span class='%s %s'>%c</span>", cls, p, p);
            }
            pw.println();
            pw.print("SS ");
            for (char c : e.reference.toCharArray()) pw.printf("<span class='%c'>%c</span>", c, c);
            pw.println();
            pw.println("</pre></div>");
        }
        pw.println("</body></html>");
    }

    // -------------------------------------------------------------------------
    // Summary writer
    // -------------------------------------------------------------------------

    static void writeSummary(List<Scores> allScores, String filename) throws IOException {
        // Collect non-NaN arrays for each metric
        double[] q3   = extractValid(allScores, "q3");
        double[] sov  = extractValid(allScores, "sov");
        double[] qH   = extractValid(allScores, "qH");
        double[] qE   = extractValid(allScores, "qE");
        double[] qC   = extractValid(allScores, "qC");
        double[] sovH = extractValid(allScores, "sovH");
        double[] sovE = extractValid(allScores, "sovE");
        double[] sovC = extractValid(allScores, "sovC");

        // Compute total lengths
        // (just report N proteins)
        try (PrintWriter pw = new PrintWriter(new FileWriter(filename))) {
            pw.println();
            pw.println("Statistic for protein validation ");
            pw.println();
            pw.printf("Number of Proteins: %15d%n", allScores.size());
            pw.println();
            printStat(pw, "q3",     q3);
            printStat(pw, "qObs_H", qH);
            printStat(pw, "qObs_E", qE);
            printStat(pw, "qObs_C", qC);
            pw.println();
            printStat(pw, "SOV",   sov);
            printStat(pw, "SOV_H", sovH);
            printStat(pw, "SOV_E", sovE);
            printStat(pw, "SOV_C", sovC);
            pw.println();
        }
    }

    static void printStat(PrintWriter pw, String name, double[] vals) {
        if (vals.length == 0) {
            pw.printf("%-8s:\t\tMean:\t  -\tDev:\t  -\tMin:\t  -\tMax:\t  -\tMedian:\t  -%n", name);
            return;
        }
        double mean   = mean(vals);
        double stddev = stddev(vals, mean);
        double min    = min(vals);
        double max    = max(vals);
        double median = percentile(vals, 50);
        double q25    = percentile(vals, 25);
        double q75    = percentile(vals, 75);
        double q05    = percentile(vals, 5);
        double q95    = percentile(vals, 95);
        pw.printf(Locale.US,
                "%-8s:\tMean:\t%5.1f\tDev:\t%5.1f\tMin:\t%5.1f\tMax:\t%5.1f\tMedian:\t%5.1f\tQuantil_25:\t%5.1f\tQuantil_75:\t%5.1f\tQuantil_5:\t%5.1f\tQuantil_95:\t%5.1f%n",
                name, mean, stddev, min, max, median, q25, q75, q05, q95);
    }

    // -------------------------------------------------------------------------
    // Statistics helpers
    // -------------------------------------------------------------------------

    static double[] extractValid(List<Scores> scores, String field) {
        List<Double> list = new ArrayList<>();
        for (Scores s : scores) {
            double v = getField(s, field);
            if (!Double.isNaN(v)) list.add(v);
        }
        double[] arr = new double[list.size()];
        for (int i = 0; i < arr.length; i++) arr[i] = list.get(i);
        return arr;
    }

    static double getField(Scores s, String field) {
        return switch (field) {
            case "q3"   -> s.q3;
            case "sov"  -> s.sov;
            case "qH"   -> s.qH;
            case "qE"   -> s.qE;
            case "qC"   -> s.qC;
            case "sovH" -> s.sovH;
            case "sovE" -> s.sovE;
            case "sovC" -> s.sovC;
            default     -> Double.NaN;
        };
    }

    static double mean(double[] a) {
        double sum = 0; for (double v : a) sum += v;
        return a.length == 0 ? 0 : sum / a.length;
    }

    static double stddev(double[] a, double mean) {
        double sum = 0; for (double v : a) sum += (v - mean) * (v - mean);
        return a.length < 2 ? 0 : Math.sqrt(sum / (a.length - 1));
    }

    static double min(double[] a) {
        double m = Double.MAX_VALUE; for (double v : a) if (v < m) m = v; return m;
    }

    static double max(double[] a) {
        double m = -Double.MAX_VALUE; for (double v : a) if (v > m) m = v; return m;
    }

    static double percentile(double[] a, double p) {
        if (a.length == 0) return 0;
        double[] sorted = a.clone();
        Arrays.sort(sorted);
        double idx = (p / 100.0) * (sorted.length - 1);
        int lo = (int) idx;
        int hi = Math.min(lo + 1, sorted.length - 1);
        return sorted[lo] + (idx - lo) * (sorted[hi] - sorted[lo]);
    }
}
import java.io.*;
import java.util.*;

public class Train {
    // setup AA SS Window Centre point
    private static final String AA_ORDER = "ACDEFGHIKLMNPQRSTVWY";
    private static final String SS_ORDER = "HEC";
    private static final int WINDOW = 17; // -8 .. +8
    private static final int CENTER = 8;

    public static void main(String[] args) {
        String dbPath = null;
        String method = "gor3";
        String modelPath = null;

        // 1. params decrypte into arr
        for (int i = 0; i < args.length; i++) {
            if (args[i].equals("--db") && i+1 < args.length) dbPath = args[++i];
            if (args[i].equals("--method") && i+1 < args.length) method = args[++i];
            if (args[i].equals("--model") && i+1 < args.length) modelPath = args[++i];
        }

        if (dbPath == null || modelPath == null) {
            // error call for insruction
            System.err.println("Usage: java -jar train.jar --db <file> --method <gor1|gor3> --model <file>");
            System.exit(1);
        }

        // 2. DS
        // count[State][AA][WindowPos]
        double[][][] counts = new double[3][20][WINDOW];
        long[] stateCounts = new long[3]; // H, E, C count total
        long totalResidues = 0;

        try {
            BufferedReader br = new BufferedReader(new FileReader(dbPath));
            String line;
            String seq = null;
            String ss = null;

            // 3. read data
            while ((line = br.readLine()) != null) { //Read where there is something
                line = line.trim();
                if (line.startsWith("AS")) seq = line.substring(2).trim();
                if (line.startsWith("SS")) ss = line.substring(2).trim();
                
                // when reading a pair of AS and SS
                if (seq != null && ss != null) {
                    if (seq.length() == ss.length()) {
                        trainSequence(seq, ss, counts, stateCounts);
                        totalResidues += seq.length();
                    }
                    seq = null; ss = null;
                }
            }
            br.close();

            // 4. Save
            saveModel(modelPath, counts, stateCounts, totalResidues, method);

        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private static void trainSequence(String seq, String ss, double[][][] counts, long[] stateCounts) {
        int len = seq.length();
        for (int i = 0; i < len; i++) {
            char sChar = ss.charAt(i);
            int sIdx = SS_ORDER.indexOf(sChar);
            if (sIdx == -1) continue; // ignore non HEC

            stateCounts[sIdx]++;

            // sliding windows
            for (int w = 0; w < WINDOW; w++) {
                int seqIdx = i + (w - CENTER);
                if (seqIdx >= 0 && seqIdx < len) {
                    char aChar = seq.charAt(seqIdx);
                    int aIdx = AA_ORDER.indexOf(aChar);
                    if (aIdx != -1) { // ignore unnormal AS (B, Z, X)
                        counts[sIdx][aIdx][w]++;
                    }
                }
            }
        }
    }

    private static void saveModel(String path, double[][][] counts, long[] stateCounts, long total, String method) throws IOException {
        PrintWriter pw = new PrintWriter(new FileWriter(path));
        pw.println("METHOD=" + method);
        pw.println("TOTAL=" + total);
        pw.println("PRIORS=" + stateCounts[0] + "," + stateCounts[1] + "," + stateCounts[2]);
        
        for (int s = 0; s < 3; s++) {
            for (int a = 0; a < 20; a++) {
                for (int w = 0; w < WINDOW; w++) {
                    if (counts[s][a][w] > 0) {
                        // Format: State AA Pos Count
                        pw.printf("%c %c %d %.1f%n", SS_ORDER.charAt(s), AA_ORDER.charAt(a), w, counts[s][a][w]);
                    }
                }
            }
        }
        pw.close();
    }
}

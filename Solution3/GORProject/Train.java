import java.io.*;
import java.util.*;

public class Train {
    // amino acids and secondary structure order
    private static final String AA_ORDER = "ACDEFGHIKLMNPQRSTVWY";
    private static final String SS_ORDER = "HEC";
    private static final int WINDOW = 17; // for GOR III and IV
    private static final int CENTER = 8;

    public static void main(String[] args) {
        String dbPath = null;
        String method = "gor3";
        String modelPath = null;

        // simple arg parsing
        for (int i = 0; i < args.length; i++) {
            if (args[i].equals("--db") && i+1 < args.length) dbPath = args[++i];
            else if (args[i].equals("--method") && i+1 < args.length) method = args[++i];
            else if (args[i].equals("--model") && i+1 < args.length) modelPath = args[++i];
            else if (args[i].equals("--help")) {
                System.out.println("Usage: java -jar train.jar --db <seclib-file> --method <gor1|gor3|gor4> --model <model-file>");
                return;
            }
        }
        if (dbPath == null || modelPath == null) {
            System.out.println("Usage: java -jar train.jar --db <seclib-file> --method <gor1|gor3|gor4> --model <model-file>");
            System.exit(1);
        }

        // counts[state][aa][windowPos]
        double[][][] counts = new double[3][20][WINDOW];
        long[] stateCounts = new long[3]; // total per state
        long totalResidues = 0;

        try (BufferedReader br = new BufferedReader(new FileReader(dbPath))) {
            String line;
            String seq = null;
            String ss = null;

            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.startsWith("AS")) seq = line.substring(2).trim();
                else if (line.startsWith("SS")) ss = line.substring(2).trim();

                if (seq != null && ss != null) {
                    if (seq.length() == ss.length()) {
                        // pick training method
                        switch (method) {
                            case "gor1": trainGor1(seq, ss, counts, stateCounts); break;
                            case "gor3": trainGor3(seq, ss, counts, stateCounts); break;
                            case "gor4": trainGor4(seq, ss, counts, stateCounts); break;
                            default:
                                System.err.println("Unknown method: " + method);
                                System.exit(1);
                        }
                        totalResidues += seq.length();
                    }
                    seq = null; ss = null;
                }
            }
            // save model in matrix format (like example)
            saveModel(modelPath, counts, stateCounts, totalResidues, method);
        } catch (IOException e) {
            e.printStackTrace();
            System.exit(1);
        }
    }

    // GOR I: only count center position
    private static void trainGor1(String seq, String ss, double[][][] counts, long[] stateCounts) {
        int len = seq.length();
        for (int i = 0; i < len; i++) {
            int sIdx = SS_ORDER.indexOf(ss.charAt(i));
            if (sIdx == -1) continue; // ignore non H/E/C
            stateCounts[sIdx]++;

            int aIdx = AA_ORDER.indexOf(seq.charAt(i));
            if (aIdx != -1) counts[sIdx][aIdx][CENTER]++;
        }
    }

    // GOR III: sliding window of size 17
    private static void trainGor3(String seq, String ss, double[][][] counts, long[] stateCounts) {
        int len = seq.length();
        for (int i = 0; i < len; i++) {
            int sIdx = SS_ORDER.indexOf(ss.charAt(i));
            if (sIdx == -1) continue;
            stateCounts[sIdx]++;

            for (int w = 0; w < WINDOW; w++) {
                int p = i + (w - CENTER);
                if (p >= 0 && p < len) {
                    int aIdx = AA_ORDER.indexOf(seq.charAt(p));
                    if (aIdx != -1) counts[sIdx][aIdx][w]++;
                }
            }
        }
    }

    // GOR IV: placeholder (same as III for now)
    private static void trainGor4(String seq, String ss, double[][][] counts, long[] stateCounts) {
        trainGor3(seq, ss, counts, stateCounts);
    }

    // save model in matrix format (one block per state)
    private static void saveModel(String path, double[][][] counts, long[] stateCounts, long total, String method) throws IOException {
        try (PrintWriter pw = new PrintWriter(path)) {
            pw.println("METHOD=" + method);
            pw.println("TOTAL=" + total);
            pw.println("PRIORS=" + stateCounts[0] + "," + stateCounts[1] + "," + stateCounts[2]);
            pw.println();

            char[] states = {'H', 'E', 'C'};
            for (int s = 0; s < 3; s++) {
                pw.println("# " + states[s]); // state header
                for (int a = 0; a < 20; a++) {
                    pw.print(AA_ORDER.charAt(a)); // amino acid
                    for (int w = 0; w < WINDOW; w++) {
                        pw.print("\t" + (int) counts[s][a][w]); // count as integer
                    }
                    pw.println();
                }
                pw.println(); // blank line between states
            }
        }
    }
}

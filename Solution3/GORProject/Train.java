import java.io.*;
import java.util.*;

public class Train {
    private static final String AA_ORDER = "ACDEFGHIKLMNPQRSTVWY";
    private static final String SS_ORDER = "CEH"; // Coil, Extended, Helix
    private static final int WINDOW = 17;
    private static final int CENTER = 8;

    // flatCounts[state][neighborAA][windowPos] 
    private long[][][] flatCounts = new long[3][20][WINDOW];
    private long[] stateCounts = new long[3]; 

    public static void main(String[] args) {
        String dbPath = null;
        String method = "gor3";
        String modelPath = null;

        for (int i = 0; i < args.length; i++) {
            if (args[i].equals("--db") && i+1 < args.length) dbPath = args[++i];
            else if (args[i].equals("--method") && i+1 < args.length) method = args[++i].toLowerCase();
            else if (args[i].equals("--model") && i+1 < args.length) modelPath = args[++i];
            else if (args[i].equals("--help")) {
                printHelp();
                return;
            }
        }

        if (dbPath == null || modelPath == null) {
            printHelp();
            System.exit(1);
        }

        Train trainer = new Train();
        trainer.run(dbPath, method, modelPath);
    }

    private static void printHelp() {
        System.out.println("Usage: java -jar train.jar --db <seclib-file> --method <gor1|gor3|gor4> --model <model-file>");
    }

    private void run(String dbPath, String method, String modelPath) {
        try (BufferedReader br = new BufferedReader(new FileReader(dbPath))) {
            String line;
            StringBuilder seqBuilder = new StringBuilder();
            StringBuilder ssBuilder = new StringBuilder();
            boolean inSeq = false, inSs = false;

            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.startsWith(">")) {
                    if (seqBuilder.length() > 0 && ssBuilder.length() > 0) {
                        processProtein(seqBuilder.toString(), ssBuilder.toString(), method);
                    }
                    seqBuilder.setLength(0);
                    ssBuilder.setLength(0);
                    inSeq = false; inSs = false;
                } else if (line.startsWith("AS")) {
                    inSeq = true; inSs = false;
                    seqBuilder.append(line.substring(2).trim());
                } else if (line.startsWith("SS")) {
                    inSeq = false; inSs = true;
                    ssBuilder.append(line.substring(2).trim());
                } else {
                    if (inSeq) seqBuilder.append(line.trim());
                    else if (inSs) ssBuilder.append(line.trim());
                }
            }
            if (seqBuilder.length() > 0 && ssBuilder.length() > 0) {
                processProtein(seqBuilder.toString(), ssBuilder.toString(), method);
            }

            long totalValid = stateCounts[0] + stateCounts[1] + stateCounts[2];
            saveModel(modelPath, totalValid, method);

        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }

    private void processProtein(String seq, String ss, String method) {
        seq = seq.replaceAll("\\s+", "");
        ss = ss.replaceAll("\\s+", "");
        if (seq.length() != ss.length()) return;

        int len = seq.length();
        for (int i = 0; i < len; i++) {
            char cAA = seq.charAt(i);
            int cAAidx = AA_ORDER.indexOf(cAA);
            if (cAAidx == -1) continue; // Skip aa

            char cSS = ss.charAt(i);
            int cSSidx = -1;
            // 严格只接受 H, E, C
            if (cSS == 'H') cSSidx = 2;      // Helix -> index 2
            else if (cSS == 'E') cSSidx = 1; // Sheet -> index 1
            else if (cSS == 'C') cSSidx = 0; // Coil  -> index 0
            else continue; // IGNORE OTHERS

            stateCounts[cSSidx]++;


            for (int w = 0; w < WINDOW; w++) {
                int p = i + (w - CENTER);
                if (p >= 0 && p < len) {
                    char nAA = seq.charAt(p);
                    int nAAidx = AA_ORDER.indexOf(nAA);
                    if (nAAidx != -1) {
                        flatCounts[cSSidx][nAAidx][w]++;
                    }
                }
            }
        }
    }

    private void saveModel(String path, long totalValid, String method) throws IOException {
        try (PrintWriter pw = new PrintWriter(path)) {
            // Head
            pw.println("METHOD=" + method);
            pw.println("TOTAL=" + totalValid);
            pw.println("PRIORS=" + stateCounts[0] + "," + stateCounts[1] + "," + stateCounts[2]);
            pw.println();

            // CEH
            for (int s = 0; s < 3; s++) {
                pw.println("# " + SS_ORDER.charAt(s));
                for (int nAA = 0; nAA < 20; nAA++) {
                    pw.print(AA_ORDER.charAt(nAA));
                    for (int w = 0; w < WINDOW; w++) {
                        pw.print("\t" + flatCounts[s][nAA][w]);
                    }
                    pw.println();
                }
                pw.println();
            }
        }
    }
}

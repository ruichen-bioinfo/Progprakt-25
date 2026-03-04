import java.io.*;
import java.util.*;

public class Train {
    private static final String AA_ORDER = "ACDEFGHIKLMNPQRSTVWY";
    private static final String SS_ORDER = "CEH"; // Coil, Extended, Helix
    private static final int WINDOW = 17;
    private static final int CENTER = 8;

    // flatCounts[state][neighborAA][windowPos] — for GOR I/III flat output
    private long[][][] flatCounts = new long[3][20][WINDOW];
    // counts[centerAA][state][neighborAA][windowPos] — for GOR IV per-center output
    private long[][][][] counts = new long[20][3][20][WINDOW];
    private long[] stateCounts = new long[3]; // C, E, H totals

    public static void main(String[] args) {
        String dbPath = null;
        String method = "gor1";
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
                        processProtein(seqBuilder.toString(), ssBuilder.toString());
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
                processProtein(seqBuilder.toString(), ssBuilder.toString());
            }

            saveModel(modelPath, method);

        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }

    private void processProtein(String seq, String ss) {
        seq = seq.replaceAll("\\s+", "");
        ss  = ss.replaceAll("\\s+", "");
        if (seq.length() != ss.length()) return;

        int len = seq.length();
        for (int i = 0; i < len; i++) {
            char cAA = seq.charAt(i);
            int cAAidx = AA_ORDER.indexOf(cAA);
            if (cAAidx == -1) continue;

            char cSS = ss.charAt(i);
            int cSSidx;
            // Strict: only accept H, E, C — skip G, I, B, T, S, -, etc.
            if      (cSS == 'H') cSSidx = 2; // Helix
            else if (cSS == 'E') cSSidx = 1; // Sheet
            else if (cSS == 'C') cSSidx = 0; // Coil
            else continue;

            stateCounts[cSSidx]++;

            for (int w = 0; w < WINDOW; w++) {
                int p = i + (w - CENTER);
                if (p >= 0 && p < len) {
                    char nAA = seq.charAt(p);
                    int nAAidx = AA_ORDER.indexOf(nAA);
                    if (nAAidx != -1) {
                        flatCounts[cSSidx][nAAidx][w]++;
                        counts[cAAidx][cSSidx][nAAidx][w]++;
                    }
                }
            }
        }
    }

    private void saveModel(String path, String method) throws IOException {
        try (PrintWriter pw = new PrintWriter(path)) {
            if (method.equals("gor4")) {
                // Matrix4D: conditioned on center AA
                pw.println("// Matrix4D");
                pw.println();
                for (int cAA = 0; cAA < 20; cAA++) {
                    for (int s = 0; s < 3; s++) {
                        pw.println("=" + AA_ORDER.charAt(cAA) + "," + SS_ORDER.charAt(s) + "=");
                        pw.println("\t");
                        for (int nAA = 0; nAA < 20; nAA++) {
                            pw.print(AA_ORDER.charAt(nAA));
                            for (int w = 0; w < WINDOW; w++) {
                                pw.print("\t" + counts[cAA][s][nAA][w]);
                            }
                            pw.println("\t");
                        }
                        pw.println();
                    }
                }
            } else {
                // GOR I / GOR III: Matrix3D, marginalized over center AA
                pw.println("// Matrix3D");
                pw.println();
                for (int s = 0; s < 3; s++) {
                    pw.println("=" + SS_ORDER.charAt(s) + "=");
                    pw.println("\t");
                    for (int nAA = 0; nAA < 20; nAA++) {
                        pw.print(AA_ORDER.charAt(nAA));
                        for (int w = 0; w < WINDOW; w++) {
                            pw.print("\t" + flatCounts[s][nAA][w]);
                        }
                        pw.println("\t");
                    }
                    pw.println();
                }
            }
        }
    }
}

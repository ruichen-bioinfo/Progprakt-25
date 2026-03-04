import java.io.*;
import java.util.*;

public class Train {
    private static final String AA_ORDER = "ACDEFGHIKLMNPQRSTVWY";
    private static final String SS_ORDER = "HEC"; // Query H, E, C
    private static final int WINDOW = 17;
    private static final int CENTER = 8;

    // counts[centerAA][state][neighborAA][windowPos]
    // Even for GOR I/III，Full stack first，save mod after method I/III/IV
    private long[][][][] counts = new long[20][3][20][WINDOW];
    private long[] stateCounts = new long[3]; // H, E, C total count

    public static void main(String[] args) {
        String dbPath = null;
        String method = "gor3";
        String modelPath = null;

        for (int i = 0; i < args.length; i++) {
            if (args[i].equals("--db") && i+1 < args.length) dbPath = args[++i];
            else if (args[i].equals("--method") && i+1 < args.length) method = args[++i].toLowerCase();
            else if (args[i].equals("--model") && i+1 < args.length) modelPath = args[++i];
        }

        if (dbPath == null || modelPath == null) {
            System.err.println("Usage: java -jar train.jar --db <file> --method <gor1|gor3|gor4> --model <file>");
            System.exit(1);
        }

        Train trainer = new Train();
        trainer.run(dbPath, method, modelPath);
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
                        processPair(seqBuilder.toString(), ssBuilder.toString(), method);
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
            // Process last entry
            if (seqBuilder.length() > 0 && ssBuilder.length() > 0) {
                processPair(seqBuilder.toString(), ssBuilder.toString(), method);
            }

            long totalValid = stateCounts[0] + stateCounts[1] + stateCounts[2];
            saveModel(modelPath, totalValid, method);

        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }

    private void processPair(String seq, String ss, String method) {
        // Remove spaces inside sequence if any (just in case)
        seq = seq.replaceAll("\\s+", "");
        ss = ss.replaceAll("\\s+", "");

        if (seq.length() != ss.length()) return;

        int len = seq.length();
        for (int i = 0; i < len; i++) {
            char cAA = seq.charAt(i);
            int cAAidx = AA_ORDER.indexOf(cAA);
            if (cAAidx == -1) continue; // Skip B, Z, X

            char cSS = ss.charAt(i);
            int cSSidx = 2; // Default to Coil

            // Coil Mapping Logic
            if (cSS == 'H' || cSS == 'G' || cSS == 'I') cSSidx = 0;
            else if (cSS == 'E' || cSS == 'B') cSSidx = 1;
            // Else (C, S, T, -, space) -> 2 (Coil)

            stateCounts[cSSidx]++;

            // Fill counts
            for (int w = 0; w < WINDOW; w++) {
                int p = i + (w - CENTER);
                if (p >= 0 && p < len) {
                    char nAA = seq.charAt(p);
                    int nAAidx = AA_ORDER.indexOf(nAA);
                    if (nAAidx != -1) {
                        counts[cAAidx][cSSidx][nAAidx][w]++;
                    }
                }
            }
        }
    }

    private void saveModel(String path, long totalValid, String method) throws IOException {
        try (PrintWriter pw = new PrintWriter(path)) {
            pw.println("METHOD=" + method);
            pw.println("TOTAL=" + totalValid);
            pw.println("PRIORS=" + stateCounts[0] + "," + stateCounts[1] + "," + stateCounts[2]);
            pw.println();

            // GOR I and GOR III use the Flat Format (# H ...)
            // GOR IV usually uses Matrix4D, but if the reference is Flat, we use Flat.
            // Based on your paste, GOR1 and GOR3 are definitely Flat.

            if (method.equals("gor4")) {

                 pw.println("// Matrix4D");
                 pw.println();
                 for (int cAA = 0; cAA < 20; cAA++) {
                    for (int s = 0; s < 3; s++) {
                        pw.println("=" + AA_ORDER.charAt(cAA) + "," + SS_ORDER.charAt(s) + "=");
                        pw.println();
                        for (int nAA = 0; nAA < 20; nAA++) {
                            pw.print(AA_ORDER.charAt(nAA));
                            for (int w = 0; w < WINDOW; w++) {
                                pw.print("\t" + counts[cAA][s][nAA][w]);
                            }
                            pw.println();
                        }
                        pw.println();
                    }
                }
            } else {
                // GOR I and GOR III -> Flat Format

                // 1. Marginalize (Sum over CenterAA)
                long[][][] flatCounts = new long[3][20][WINDOW];
                for (int cAA = 0; cAA < 20; cAA++) {
                    for (int s = 0; s < 3; s++) {
                        for (int nAA = 0; nAA < 20; nAA++) {
                            for (int w = 0; w < WINDOW; w++) {
                                flatCounts[s][nAA][w] += counts[cAA][s][nAA][w];
                            }
                        }
                    }
                }

                // 2. Output
                for (int s = 0; s < 3; s++) {
                    pw.println("# " + SS_ORDER.charAt(s));
                    for (int nAA = 0; nAA < 20; nAA++) {
                        pw.print(AA_ORDER.charAt(nAA)); // AA at start of line

                        for (int w = 0; w < WINDOW; w++) {
                            long val = flatCounts[s][nAA][w];

                            // GOR I Special Handling: Only center (index 8) has value
                            if (method.equals("gor1")) {
                                if (w != CENTER) val = 0;
                            }

                            pw.print("\t" + val); // Tab separated integers
                        }
                        pw.println();
                    }
                    pw.println();
                }
            }
        }
    }
}

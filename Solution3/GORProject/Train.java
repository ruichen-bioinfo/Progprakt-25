import java.io.*;
import java.util.*;

public class Train {
    private static final String AA_ORDER = "ACDEFGHIKLMNPQRSTVWY";
    //  CEH (Coil, Extended, Helix)
    private static final String SS_ORDER = "CEH";

    private static final int WINDOW = 17;
    private static final int CENTER = 8;

    // counts[centerAA][state][neighborAA][windowPos]
    private long[][][][] counts = new long[20][3][20][WINDOW];
    private long[] stateCounts = new long[3]; // Total counts for each State

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
                        trainPair(seqBuilder.toString(), ssBuilder.toString(), method);
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
                trainPair(seqBuilder.toString(), ssBuilder.toString(), method);
            }

            long totalValid = stateCounts[0] + stateCounts[1] + stateCounts[2];
            saveModel(modelPath, totalValid, method);

        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }

    private void trainPair(String seq, String ss, String method) {
        seq = seq.replaceAll("\\s+", "");
        ss = ss.replaceAll("\\s+", "");
        if (seq.length() != ss.length()) return;

        int len = seq.length();

        // Skip Boundaries

        int startI = CENTER;
        int endI = len - CENTER;

        for (int i = startI; i < endI; i++) {
            char cAA = seq.charAt(i);
            int cAAidx = AA_ORDER.indexOf(cAA);
            if (cAAidx == -1) continue;

            char cSS = ss.charAt(i);
            int cSSidx = -1;

            // Map SS to 0,1,2 based on SS_ORDER="CEH"
            // C -> 0
            // E -> 1
            // H -> 2

            if (cSS == 'H' || cSS == 'G' || cSS == 'I') cSSidx = 2; // H
            else if (cSS == 'E' || cSS == 'B') cSSidx = 1;          // E
            else cSSidx = 0;                                        // C (Coil)

            stateCounts[cSSidx]++;

            // Fill counts
            for (int w = 0; w < WINDOW; w++) {
                int p = i + (w - CENTER);
                // p from 0 to len-1

                char nAA = seq.charAt(p);
                int nAAidx = AA_ORDER.indexOf(nAA);
                if (nAAidx != -1) {
                    counts[cAAidx][cSSidx][nAAidx][w]++;
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

            if (method.equals("gor1")) {
                //GOR I: Matrix3D
                pw.println("// Matrix3D");
                pw.println();

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

                for (int s = 0; s < 3; s++) {
                    pw.println("=" + SS_ORDER.charAt(s) + "=");
                    pw.println(); // Empty line after header
                    for (int nAA = 0; nAA < 20; nAA++) {
                        pw.print(AA_ORDER.charAt(nAA));
                        for (int w = 0; w < WINDOW; w++) {
                            long val = flatCounts[s][nAA][w];
                            if (w != CENTER) val = 0; // GOR I only center
                            pw.print("\t" + val);
                        }
                        pw.println();
                    }
                    pw.println();
                }

            } else {
                // GOR III / IV: Matrix4D
                pw.println("// Matrix4D");
                pw.println();

                for (int cAA = 0; cAA < 20; cAA++) {
                    for (int s = 0; s < 3; s++) {
                        pw.println("=" + AA_ORDER.charAt(cAA) + "," + SS_ORDER.charAt(s) + "=");
                        pw.println(); // Empty line
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
            }
        }
    }
}

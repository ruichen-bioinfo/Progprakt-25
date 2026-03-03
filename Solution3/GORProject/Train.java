import java.io.*;
import java.util.*;

public class Train {
    private static final String AA_ORDER = "ACDEFGHIKLMNPQRSTVWY";
    private static final String SS_ORDER = "CEH";  // order from reference: Coil, Extended, Helix
    private static final int WINDOW = 17;
    private static final int CENTER = 8;

    // counts[centerAA][centerSS][neighborAA][windowPos]
    private long[][][][] counts = new long[20][3][20][WINDOW];
    private long[] stateCounts = new long[3]; // total valid centers for each SS (C,E,H)

    public static void main(String[] args) {
        String dbPath = null;
        String method = "gor3";
        String modelPath = null;
        String mafPath = null;   // for GOR V, not used in training

        for (int i = 0; i < args.length; i++) {
            if (args[i].equals("--db") && i+1 < args.length) dbPath = args[++i];
            else if (args[i].equals("--method") && i+1 < args.length) method = args[++i];
            else if (args[i].equals("--model") && i+1 < args.length) modelPath = args[++i];
            else if (args[i].equals("--maf") && i+1 < args.length) mafPath = args[++i];
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
        trainer.run(dbPath, method, modelPath, mafPath);
    }

    private static void printHelp() {
        System.out.println("Usage: java -jar train.jar --db <seclib-file> --method <gor1|gor3|gor4|gor5> --model <model-file> [--maf <align-folder>]");
    }

    private void run(String dbPath, String method, String modelPath, String mafPath) {
        try (BufferedReader br = new BufferedReader(new FileReader(dbPath))) {
            String line;
            StringBuilder seqBuilder = new StringBuilder();
            StringBuilder ssBuilder = new StringBuilder();
            boolean inSeq = false, inSs = false;

            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.startsWith(">")) {
                    if (seqBuilder.length() > 0 && ssBuilder.length() > 0) {
                        String seq = seqBuilder.toString().replaceAll("\\s+", "");
                        String ss = ssBuilder.toString().replaceAll("\\s+", "");
                        if (seq.length() == ss.length()) {
                            trainProtein(seq, ss, method);
                        }
                    }
                    seqBuilder.setLength(0);
                    ssBuilder.setLength(0);
                    inSeq = false;
                    inSs = false;
                } else if (line.startsWith("AS")) {
                    inSeq = true;
                    inSs = false;
                    seqBuilder.append(line.substring(2));
                } else if (line.startsWith("SS")) {
                    inSeq = false;
                    inSs = true;
                    ssBuilder.append(line.substring(2));
                } else {
                    if (inSeq) seqBuilder.append(line);
                    else if (inSs) ssBuilder.append(line);
                }
            }
            if (seqBuilder.length() > 0 && ssBuilder.length() > 0) {
                String seq = seqBuilder.toString().replaceAll("\\s+", "");
                String ss = ssBuilder.toString().replaceAll("\\s+", "");
                if (seq.length() == ss.length()) {
                    trainProtein(seq, ss, method);
                }
            }

            long totalValid = stateCounts[0] + stateCounts[1] + stateCounts[2];
            saveModel(modelPath, totalValid, method);

        } catch (IOException e) {
            e.printStackTrace();
            System.exit(1);
        }
    }

    // Map input SS characters to indices in SS_ORDER (0=C,1=E,2=H)
    private int ssCharToIndex(char c) {
        if (c == 'H' || c == 'G' || c == 'I') return 2; // Helix
        if (c == 'E' || c == 'B') return 1;             // Sheet
        return 0;                                        // Coil (includes 'C', 'T', 'S', '-', etc.)
    }

    private void trainProtein(String seq, String ss, String method) {
        int len = seq.length();
        for (int i = 0; i < len; i++) {
            char centerAA = seq.charAt(i);
            int cAAidx = AA_ORDER.indexOf(centerAA);
            if (cAAidx == -1) continue; // skip ambiguous center

            char centerSS = ss.charAt(i);
            int cSSidx = ssCharToIndex(centerSS); // always 0,1,2

            stateCounts[cSSidx]++;

            if (method.equals("gor1")) {
                // GOR I: only center position
                int w = CENTER;
                char neighborAA = seq.charAt(i);
                int nAAidx = AA_ORDER.indexOf(neighborAA);
                if (nAAidx != -1) {
                    counts[cAAidx][cSSidx][nAAidx][w]++;
                }
            } else {
                // GOR III, IV, V: count all window positions
                for (int w = 0; w < WINDOW; w++) {
                    int p = i + (w - CENTER);
                    if (p >= 0 && p < len) {
                        char neighborAA = seq.charAt(p);
                        int nAAidx = AA_ORDER.indexOf(neighborAA);
                        if (nAAidx != -1) {
                            counts[cAAidx][cSSidx][nAAidx][w]++;
                        }
                    }
                }
            }
        }
    }

    private void saveModel(String path, long totalValid, String method) throws IOException {
        try (PrintWriter pw = new PrintWriter(path)) {
            // No extra headers (like METHOD, TOTAL, PRIORS) – keep only matrix blocks as in reference

            if (method.equals("gor1")) {
                // GOR I: Matrix3D format (summed over center amino acids)
                pw.println("// Matrix3D");
                pw.println();

                // Marginalize over centerAA
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
                    pw.println();
                    for (int nAA = 0; nAA < 20; nAA++) {
                        pw.print(AA_ORDER.charAt(nAA));
                        for (int w = 0; w < WINDOW; w++) {
                            pw.print("\t" + flatCounts[s][nAA][w]);
                        }
                        pw.println();
                    }
                    pw.println();
                }
            } else {
                // GOR III, IV, V: Matrix4D format (pairwise)
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
            }
        }
    }
}

import java.io.*;
import java.util.*;

public class Train {
    private static final String AA_ORDER = "ACDEFGHIKLMNPQRSTVWY";
    private static final String SS_ORDER = "HEC";
    private static final int WINDOW = 17;      // for GOR III/IV
    private static final int CENTER = 8;

    // counts[centerAA][centerSS][neighborAA][windowPos]   (for GOR I/III/IV)
    private long[][][][] counts = new long[20][3][20][WINDOW];

    // for GOR IV: additional pair frequencies (neighbor1, neighbor2) – you may expand
    // private long[][][][][] pairCounts; // if needed

    private long[] stateCounts = new long[3]; // total valid centers for each SS

    public static void main(String[] args) {
        String dbPath = null;
        String method = "gor3";
        String modelPath = null;
        String mafPath = null;   // not used in training, only for GOR V

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
        // read seclib file
        try (BufferedReader br = new BufferedReader(new FileReader(dbPath))) {
            String line;
            StringBuilder seqBuilder = new StringBuilder();
            StringBuilder ssBuilder = new StringBuilder();
            boolean inSeq = false, inSs = false;

            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.startsWith(">")) {
                    // process previous protein
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

    // train one protein according to method
    private void trainProtein(String seq, String ss, String method) {
        int len = seq.length();
        for (int i = 0; i < len; i++) {
            char centerAA = seq.charAt(i);
            int cAAidx = AA_ORDER.indexOf(centerAA);
            if (cAAidx == -1) continue; // skip ambiguous center

            char centerSS = ss.charAt(i);
            int cSSidx = SS_ORDER.indexOf(centerSS);
            if (cSSidx == -1) continue; // skip non H/E/C

            stateCounts[cSSidx]++;

            if (method.equals("gor1")) {
                // GOR I: only count center position
                int w = CENTER;
                char neighborAA = seq.charAt(i);
                int nAAidx = AA_ORDER.indexOf(neighborAA);
                if (nAAidx != -1) {
                    counts[cAAidx][cSSidx][nAAidx][w]++;
                }
            } else if (method.equals("gor3")) {
                // GOR III: symmetric window 17
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
            }   else if (method.equals("gor4")) {
                // GOR IV: Use Pairwise Statistics (Center AA <-> Neighbor AA)
                // Your current structure already supports this!
                // counts[cAA][cSS][nAA][w] captures the correlation between
                // the center residue and the neighbor at w.

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
                // TODO: implement proper GOR IV (e.g., separate left/right statistics, or pairwise)
            } else if (method.equals("gor5")) {
                // GOR V: training is same as GOR III (counts are used to build base model)
                // The evolutionary information comes from the --maf folder during prediction.
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

    // save model in Matrix4D format
    private void saveModel(String path, long totalValid, String method) throws IOException {
        try (PrintWriter pw = new PrintWriter(path)) {
            pw.println("METHOD=" + method);
            pw.println("TOTAL=" + totalValid);
            pw.println("PRIORS=" + stateCounts[0] + "," + stateCounts[1] + "," + stateCounts[2]);
            pw.println("// Matrix4D");
            pw.println();

            for (int cAA = 0; cAA < 20; cAA++) {
                for (int cSS = 0; cSS < 3; cSS++) {
                    pw.println("=" + AA_ORDER.charAt(cAA) + "," + SS_ORDER.charAt(cSS) + "=");
                    pw.println("\t");
                    for (int nAA = 0; nAA < 20; nAA++) {
                        pw.print(AA_ORDER.charAt(nAA));
                        for (int w = 0; w < WINDOW; w++) {
                            pw.print("\t" + counts[cAA][cSS][nAA][w]);
                        }
                        pw.println();
                    }
                    pw.println();
                }
            }
        }
    }
}

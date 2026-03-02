import java.io.*;
import java.nio.file.*;
import java.util.*;

public class GorEval {
    // settings
    private static final int FOLDS = 5;
    private static final String TRAIN_JAR = "train.jar";
    private static final String PREDICT_JAR = "predict.jar";
    private static final Random RAND = new Random(42); // fixed seed for same shuffle each time

    public static void main(String[] args) throws Exception {
        // default values
        String dbPath = "CB513DSSP.db";
        String outPath = "eval_results.txt";
        String psipredPath = null;
        String method = "gor3";

        // simple arg parse
        for (int i = 0; i < args.length; i++) {
            if (args[i].equals("--db") && i+1 < args.length) dbPath = args[++i];
            else if (args[i].equals("--out") && i+1 < args.length) outPath = args[++i];
            else if (args[i].equals("--psipred") && i+1 < args.length) psipredPath = args[++i];
            else if (args[i].equals("--method") && i+1 < args.length) method = args[++i];
            else if (args[i].equals("--help")) {
                System.out.println("Usage: java -jar gor_eval.jar [--db <file>] [--out <file>] [--psipred <file>] [--method <gor1|gor3>]");
                return;
            }
        }

        // load all proteins from db file
        List<Protein> proteins = loadProteins(dbPath);
        System.out.println("Loaded " + proteins.size() + " proteins.");
        Collections.shuffle(proteins, RAND); // random order

        // split into folds
        List<List<Protein>> folds = partition(proteins, FOLDS);

        double[] q3 = new double[FOLDS];
        double[] sov = new double[FOLDS];

        // do cross-validation
        for (int fold = 0; fold < FOLDS; fold++) {
            System.out.println("Fold " + (fold+1) + "/" + FOLDS);
            List<Protein> testSet = folds.get(fold);
            List<Protein> trainSet = new ArrayList<>();
            for (int i = 0; i < FOLDS; i++) if (i != fold) trainSet.addAll(folds.get(i));

            // create temp files
            Path trainFile = Files.createTempFile("train", ".db");
            Path modelFile = Files.createTempFile("model", ".txt");
            Path testFasta = Files.createTempFile("test", ".fasta");
            Path predOut = Files.createTempFile("pred", ".out");

            try {
                // write training data in the format train.jar expects
                writeTrainFile(trainSet, trainFile.toString());

                // run train.jar
                runProcess("java", "-jar", TRAIN_JAR, "--db", trainFile.toString(),
                        "--method", method, "--model", modelFile.toString());

                // write test sequences as fasta
                writeFasta(testSet, testFasta.toString());

                // run predict.jar and save output to predOut
                runProcessRedirectOutput(predOut.toFile(),
                        "java", "-jar", PREDICT_JAR, "--model", modelFile.toString(),
                        "--seq", testFasta.toString(), "--format", "txt", "--probabilities");

                // evaluate predictions against true structures
                double[] metrics = evaluatePredictions(predOut.toString(), testSet);
                q3[fold] = metrics[0];
                sov[fold] = metrics[1];
            } finally {
                // delete temp files
                Files.deleteIfExists(trainFile);
                Files.deleteIfExists(modelFile);
                Files.deleteIfExists(testFasta);
                Files.deleteIfExists(predOut);
            }
        }

        // write results to output file
        try (PrintWriter out = new PrintWriter(outPath)) {
            out.println("Fold\tQ3\tSOV");
            for (int i = 0; i < FOLDS; i++) {
                out.printf("%d\t%.4f\t%.4f%n", i+1, q3[i], sov[i]);
            }
            out.printf("Mean\t%.4f\t%.4f%n", mean(q3), mean(sov));
        }
        System.out.println("Results written to " + outPath);

        // optional: compare with PSIPRED
        if (psipredPath != null) {
            double[] psipredMetrics = evaluatePsipred(psipredPath, proteins);
            System.out.printf("PSIPRED: Q3=%.4f SOV=%.4f%n", psipredMetrics[0], psipredMetrics[1]);
        }
    }

    // simple class to hold protein data
    static class Protein {
        String id;
        String seq;
        String ss;
    }

    // read proteins from db file (format: >id, AS seq, SS ss)
    static List<Protein> loadProteins(String dbPath) throws IOException {
        List<Protein> list = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(new FileReader(dbPath))) {
            String line;
            Protein p = null;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.startsWith(">")) {
                    if (p != null) list.add(p);
                    p = new Protein();
                    p.id = line.substring(1).split("\\s+")[0];
                } else if (line.startsWith("AS") && p != null) {
                    p.seq = line.substring(2).trim();
                } else if (line.startsWith("SS") && p != null) {
                    p.ss = line.substring(2).trim();
                }
            }
            if (p != null) list.add(p);
        }
        return list;
    }

    // write training data in the same format as the original db
    static void writeTrainFile(List<Protein> trainSet, String path) throws IOException {
        try (PrintWriter pw = new PrintWriter(path)) {
            for (Protein p : trainSet) {
                pw.println(">" + p.id);
                pw.println("AS " + p.seq);
                pw.println("SS " + p.ss);
            }
        }
    }

    // write test sequences in fasta format
    static void writeFasta(List<Protein> testSet, String path) throws IOException {
        try (PrintWriter pw = new PrintWriter(path)) {
            for (Protein p : testSet) {
                pw.println(">" + p.id);
                pw.println(p.seq);
            }
        }
    }

    // run a command and show its output (for debugging)
    static void runProcess(String... cmd) throws IOException, InterruptedException {
        ProcessBuilder pb = new ProcessBuilder(cmd);
        pb.redirectErrorStream(true);
        pb.inheritIO(); // prints to console
        Process p = pb.start();
        int exit = p.waitFor();
        if (exit != 0) throw new IOException("Process exited with code " + exit);
    }

    // run a command and redirect its output to a file
    static void runProcessRedirectOutput(File outFile, String... cmd) throws IOException, InterruptedException {
        ProcessBuilder pb = new ProcessBuilder(cmd);
        pb.redirectErrorStream(true);
        pb.redirectOutput(outFile);
        Process p = pb.start();
        int exit = p.waitFor();
        if (exit != 0) throw new IOException("Process exited with code " + exit);
    }

    // parse predictions from predict.jar output and compute Q3/SOV
    static double[] evaluatePredictions(String predFile, List<Protein> testSet) throws IOException {
        // read predicted ss for each id
        Map<String, String> predMap = new HashMap<>();
        try (BufferedReader br = new BufferedReader(new FileReader(predFile))) {
            String line;
            String currentId = null;
            String pred = null;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.startsWith(">")) {
                    if (currentId != null && pred != null) predMap.put(currentId, pred);
                    currentId = line.substring(1).split("\\s+")[0];
                    pred = null;
                } else if (line.startsWith("PS") && currentId != null) {
                    pred = line.substring(2).trim();
                }
            }
            if (currentId != null && pred != null) predMap.put(currentId, pred);
        }

        // true ss from test set
        Map<String, String> trueMap = new HashMap<>();
        for (Protein p : testSet) trueMap.put(p.id, p.ss);

        return computeQ3AndSOV(trueMap, predMap);
    }

    // Q3 and SOV calculation
    static double[] computeQ3AndSOV(Map<String, String> trueMap, Map<String, String> predMap) {
        int totalCorrect = 0;
        int totalResidues = 0;

        // store segments for each state
        Map<Character, List<int[]>> trueSegments = new HashMap<>();
        Map<Character, List<int[]>> predSegments = new HashMap<>();
        for (char s : new char[]{'H','E','C'}) {
            trueSegments.put(s, new ArrayList<>());
            predSegments.put(s, new ArrayList<>());
        }

        // go through each protein
        for (Map.Entry<String, String> entry : trueMap.entrySet()) {
            String id = entry.getKey();
            String trueStr = entry.getValue();
            String predStr = predMap.get(id);
            if (predStr == null || trueStr.length() != predStr.length()) continue;

            // Q3: count correct residues
            for (int i = 0; i < trueStr.length(); i++) {
                if (trueStr.charAt(i) == predStr.charAt(i)) totalCorrect++;
                totalResidues++;
            }

            // extract segments for SOV
            extractSegments(trueStr, trueSegments);
            extractSegments(predStr, predSegments);
        }

        double q3 = totalResidues > 0 ? (double) totalCorrect / totalResidues : 0.0;

        // average SOV over the three states
        double sovSum = 0.0;
        int stateCount = 0;
        for (char s : new char[]{'H','E','C'}) {
            double sovState = sovForState(s, trueSegments.get(s), predSegments.get(s));
            sovSum += sovState;
            stateCount++;
        }
        double sov = stateCount > 0 ? sovSum / stateCount : 0.0;

        return new double[]{q3, sov};
    }

    // split a sequence into contiguous segments of same character
    static void extractSegments(String seq, Map<Character, List<int[]>> segments) {
        if (seq.isEmpty()) return;
        char prev = seq.charAt(0);
        int start = 0;
        for (int i = 1; i <= seq.length(); i++) {
            char cur = i < seq.length() ? seq.charAt(i) : 0;
            if (i == seq.length() || cur != prev) {
                // segment from start to i-1
                segments.get(prev).add(new int[]{start, i-1});
                start = i;
                if (i < seq.length()) prev = cur;
            }
        }
    }

    // SOV for one state (simplified version)
    static double sovForState(char state, List<int[]> trueSegs, List<int[]> predSegs) {
        if (trueSegs.isEmpty()) return 1.0; // nothing to compare -> perfect

        double totalSov = 0.0;
        int totalLen = 0;

        for (int[] tseg : trueSegs) {
            int tStart = tseg[0];
            int tEnd = tseg[1];
            int tLen = tEnd - tStart + 1;
            totalLen += tLen;

            double maxOverlap = 0;
            int maxLen = 0;

            for (int[] pseg : predSegs) {
                int pStart = pseg[0];
                int pEnd = pseg[1];
                int pLen = pEnd - pStart + 1;

                int overlapStart = Math.max(tStart, pStart);
                int overlapEnd = Math.min(tEnd, pEnd);
                if (overlapStart <= overlapEnd) {
                    int overlap = overlapEnd - overlapStart + 1;
                    if (overlap > maxOverlap) {
                        maxOverlap = overlap;
                        maxLen = Math.max(tLen, pLen);
                    }
                }
            }

            if (maxOverlap > 0) {
                // SOV formula: (overlap * (overlap / maxLen)) summed
                totalSov += maxOverlap * (maxOverlap / (double) maxLen);
            }
        }

        return totalSov / totalLen;
    }

    // read PSIPRED output (format: protein_id res_num aa true pred ...) and compute Q3/SOV
    static double[] evaluatePsipred(String psipredPath, List<Protein> proteins) throws IOException {
        Map<String, String> trueMap = new HashMap<>();
        Map<String, String> predMap = new HashMap<>();

        try (BufferedReader br = new BufferedReader(new FileReader(psipredPath))) {
            String line;
            String currentId = null;
            StringBuilder trueSeq = new StringBuilder();
            StringBuilder predSeq = new StringBuilder();

            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.startsWith("#") || line.isEmpty()) continue;
                String[] parts = line.split("\\s+");
                if (parts.length < 5) continue; // need at least id, res, aa, true, pred
                String id = parts[0];
                if (!id.equals(currentId)) {
                    if (currentId != null) {
                        trueMap.put(currentId, trueSeq.toString());
                        predMap.put(currentId, predSeq.toString());
                    }
                    currentId = id;
                    trueSeq = new StringBuilder();
                    predSeq = new StringBuilder();
                }
                trueSeq.append(parts[2]); // true state is column 3 (0-based)
                predSeq.append(parts[3]); // pred state is column 4
            }
            if (currentId != null) {
                trueMap.put(currentId, trueSeq.toString());
                predMap.put(currentId, predSeq.toString());
            }
        }

        return computeQ3AndSOV(trueMap, predMap);
    }

    // split list into n folds (almost equal size)
    static List<List<Protein>> partition(List<Protein> proteins, int folds) {
        List<List<Protein>> result = new ArrayList<>();
        int size = proteins.size();
        int foldSize = size / folds;
        int remainder = size % folds;
        int start = 0;
        for (int i = 0; i < folds; i++) {
            int end = start + foldSize + (i < remainder ? 1 : 0);
            result.add(new ArrayList<>(proteins.subList(start, end)));
            start = end;
        }
        return result;
    }

    // average of an array
    static double mean(double[] arr) {
        double sum = 0;
        for (double v : arr) sum += v;
        return sum / arr.length;
    }
}

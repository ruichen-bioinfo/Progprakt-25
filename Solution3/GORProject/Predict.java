import java.io.*;
import java.util.*;

public class Predict {
    // Setup
    private static final String AA_ORDER = "ACDEFGHIKLMNPQRSTVWY";
    private static final String SS_ORDER = "HEC";
    private static final int WINDOW = 17;
    private static final int CENTER = 8;

    // 1. raw data (Counts)
    private double[][][] counts = new double[3][20][WINDOW];
    private long[] stateTotals = new long[3]; // H, E, C counts
    private long totalResidues = 0;

    public static void main(String[] args) {
        String modelPath = null;
        String seqPath = null;
        String format = "txt";
        boolean showProbs = false;

        for (int i = 0; i < args.length; i++) {
            if (args[i].equals("--model")) modelPath = args[++i];
            if (args[i].equals("--seq")) seqPath = args[++i];
            if (args[i].equals("--format")) format = args[++i];
            if (args[i].equals("--probabilities")) showProbs = true;
        }

        if (modelPath == null || seqPath == null) {
            System.err.println("Usage: java -jar predict.jar --model <file> --seq <file>");
            System.exit(1);
        }

        Predict p = new Predict();
        try {
            p.loadModel(modelPath);
            p.predictFile(seqPath, format, showProbs);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    // Loading save counts for model
    private void loadModel(String path) throws IOException {
        BufferedReader br = new BufferedReader(new FileReader(path));
        String line;

        while ((line = br.readLine()) != null) {
            line = line.trim();
            if (line.startsWith("PRIORS=") || line.startsWith("S_COUNTS=")) {
                String val = line.contains("=") ? line.split("=")[1] : line;
                String[] parts = val.split(",");
                for(int i=0; i<3; i++) stateTotals[i] = Long.parseLong(parts[i]);
            } else if (line.startsWith("TOTAL=")) {
                totalResidues = Long.parseLong(line.substring(6));
            } else if (!line.contains("=")) {
                // H A -8 50.0
                String[] parts = line.split("\\s+");
                if (parts.length < 4) continue;
                int s = SS_ORDER.indexOf(parts[0]);
                int a = AA_ORDER.indexOf(parts[1]);
                int w = Integer.parseInt(parts[2]);
                double val = Double.parseDouble(parts[3]);
                counts[s][a][w] = val;
            }
        }
        br.close();

        // safety check in case /0
        if (totalResidues == 0) totalResidues = 1;
    }

    private void predictFile(String seqPath, String format, boolean showProbs) throws IOException {
        BufferedReader br = new BufferedReader(new FileReader(seqPath));
        String line;
        String id = "";
        StringBuilder seq = new StringBuilder();

        while ((line = br.readLine()) != null) {
            line = line.trim();
            if (line.startsWith(">")) {
                if (seq.length() > 0) doPredict(id, seq.toString(), format, showProbs);
                id = line.substring(1).split("\\s+")[0];
                seq.setLength(0);
            } else {
                seq.append(line);
            }
        }
        if (seq.length() > 0) doPredict(id, seq.toString(), format, showProbs);
        br.close();
    }

    private void doPredict(String id, String seq, String format, boolean showProbs) {
        int len = seq.length();
        char[] result = new char[len];
        int[][] probScale = new int[3][len];

        for (int i = 0; i < len; i++) {
            double[] scores = new double[3];

            for (int s = 0; s < 3; s++) {

                // Term 1: log( P(S) / P(not S) )
                double countS = stateTotals[s];
                double countNotS = totalResidues - countS;

                // accumulate
                if (countS == 0) countS = 1;
                if (countNotS == 0) countNotS = 1;

                scores[s] = Math.log(countS / countNotS);

                // Term 2: Sum log( P(R|S) / P(R|not S) )
                for (int w = 0; w < WINDOW; w++) {
                    int pos = i + (w - CENTER);
                    if (pos >= 0 && pos < len) {
                        int a = AA_ORDER.indexOf(seq.charAt(pos));
                        if (a != -1) {
                            // P(R|S) term
                            double c_RS = counts[s][a][w];
                            // P(R|not S) term
                            // R total count(at windows w) = Sum(counts[k][a][w])
                            double c_R_total = 0;
                            for(int k=0; k<3; k++) c_R_total += counts[k][a][w];

                            double c_R_NotS = c_R_total - c_RS;

                            // Calc probability with conditions
                            // P(R|S) = c_RS / countS
                            // P(R|not S) = c_R_NotS / countNotS
                            // LogOdds = log( (c_RS / countS) / (c_R_NotS / countNotS) )
                            //         = log( (c_RS * countNotS) / (c_R_NotS * countS) )

                            double num = (c_RS + 0.1) * countNotS;
                            double den = (c_R_NotS + 0.1) * countS;

                            scores[s] += Math.log(num / den);
                        }
                    }
                }
            }

            // Softmax standardization
            double maxS = Math.max(scores[0], Math.max(scores[1], scores[2]));
            double expH = Math.exp(scores[0] - maxS);
            double expE = Math.exp(scores[1] - maxS);
            double expC = Math.exp(scores[2] - maxS);
            double sum = expH + expE + expC;

            double pH = expH / sum;
            double pE = expE / sum;
            double pC = expC / sum;

            // decision!!!! What is what!
            if (pH >= pE && pH >= pC) result[i] = 'H';
            else if (pE >= pH && pE >= pC) result[i] = 'E';
            else result[i] = 'C';

            probScale[0][i] = (int)(pH * 9);
            probScale[1][i] = (int)(pE * 9);
            probScale[2][i] = (int)(pC * 9);
        }

        if (format.equals("html")) printHtml(id, seq, new String(result), probScale, showProbs);
        else printTxt(id, seq, new String(result), probScale, showProbs);
    }

    private void printTxt(String id, String seq, String ss, int[][] probs, boolean showProbs) {
        System.out.println(">" + id);
        System.out.println("AS " + seq);
        System.out.println("PS " + ss);
        if (showProbs) {
            System.out.println("PH " + arrToStr(probs[0]));
            System.out.println("PE " + arrToStr(probs[1]));
            System.out.println("PC " + arrToStr(probs[2]));
        }
    }

    private void printHtml(String id, String seq, String ss, int[][] probs, boolean showProbs) {
        System.out.println("<div class='prediction'>");
        System.out.println("<h4>" + id + "</h4>");
        System.out.println("<pre>");
        System.out.println("AS " + seq);
        System.out.print("PS ");
        for(char c : ss.toCharArray()) {
            String col = c=='H'?"red": (c=='E'?"blue":"black");
            System.out.print("<span style='color:"+col+"'>"+c+"</span>");
        }
        System.out.println();
        if (showProbs) {
            System.out.println("PH " + arrToStr(probs[0]));
            System.out.println("PE " + arrToStr(probs[1]));
            System.out.println("PC " + arrToStr(probs[2]));
        }
        System.out.println("</pre></div>");
    }

    private String arrToStr(int[] arr) {
        StringBuilder sb = new StringBuilder();
        for (int i : arr) sb.append(i);
        return sb.toString();
    }
}

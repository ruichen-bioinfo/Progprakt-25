import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

public class Main {
    public static void main(String[] args) {
        Map<String, String> options = parseArgs(args);
        //teilweise noch nicht ganz korrekt für manche flags glaube ich
        String pairfile = options.get("pair");
        String seqlibfile = options.get("seqlib");
        String matrixfile = options.get("m");
        int gapOpenPenalty = Integer.parseInt(options.get("go"));
        int gapExtentPenalty = Integer.parseInt(options.get("ge"));
        String mode = options.get("mode");
        boolean nw = Boolean.parseBoolean(options.get("nw"));
        String format = options.get("format");
        String dpmatricesDir = options.get("dpmatrices");
        boolean check = Boolean.parseBoolean(options.get("check"));


        InputReader inputreader = new InputReader();
        try {
            Map<String, Sequence> seqs = inputreader.readSeqLib(Path.of(seqlibfile));
            List<Pair> pairs = inputreader.readPairs(Path.of(pairfile));
            Matrix scoringMatrix = Matrix.readMatrix(Path.of(matrixfile));

            for(Pair pair : pairs) {
                Sequence s1 = seqs.get(pair.getId1());
                Sequence s2 = seqs.get(pair.getId2());

                AlignmentAlgorithm AA;

                //hier das richtige Objekt
                if (nw) {
                    //--mode <local|global|freeshift>
                    if (mode == "global"){
                        AA = new NeedlemanWunschGlobal(s1, s2, scoringMatrix);
                    }
                    else if (mode == "local"){
                        AA = new NeedlemanWunschLocal(s1, s2, scoringMatrix);
                    }
                    else if (mode == "freeshift"){
                        AA = new NeedlemanWunschFreeshift(s1, s2, scoringMatrix);
                    }
                    else {
                        System.err.println("Unknown mode " + mode);
                        throw new IllegalArgumentException("Unknown mode " + mode);
                    }
                }
                else {
                    if (mode == "global"){
                        AA = new GotohGlobal(s1, s2, scoringMatrix);
                    }
                    else if (mode == "local"){
                        AA = new GotohLocal(s1, s2, scoringMatrix);
                    }
                    else if (mode == "freeshift"){
                        AA = new GotohFreeshift(s1, s2, scoringMatrix);
                    }
                    else{
                        System.out.println("Unknown mode " + mode);
                        throw new IllegalArgumentException("Unknown mode " + mode);
                    }

                }
                AA.align();



            }


        }
        catch (IOException e) {
            System.err.println("Error reading seqlib file: " + e.getMessage());
        }

    }

    private static Map<String, String> parseArgs(String[] args) {
        Map<String, String> map = new HashMap<>();
        for (int i = 0; i < args.length; i++) {
            //checken ob arg eine Flag ist
            if (args[i].startsWith("--")) {

                String key = args[i].substring(2);

                //check das nächste Ding keine weitere Flag
                if (i + 1 < args.length && !args[i + 1].startsWith("--")){
                    map.put(key, args[i + 1]);
                    i++;
                    //wenn weitere Flag dann war es ein boolean arg
                } else {
                    map.put(key, "true");
                }
            }
        }
        return map;
    }



}

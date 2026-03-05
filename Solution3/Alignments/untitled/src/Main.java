import java.io.IOException;
import java.nio.file.Path;
import java.util.*;

public class Main {

    private static final String HELP =
            "Syntax:\n" +
                    "java -jar alignment.jar [--go <gapopen>] [--ge <gapextend>] " +
                    "[--dpmatrices <dir>] [--check] --pairs <pairfile> --seqlib <seqlibfile> " +
                    "-m <matrixname> --mode <local|global|freeshift> [--nw] --format <scores|ali|html>";

    public static void main(String[] args) {

        Map<String,String> options = parseArgs(args);

        if(!options.containsKey("pairs") ||
                !options.containsKey("seqlib") ||
                !options.containsKey("m") ||
                !options.containsKey("mode") ||
                !options.containsKey("format")) {

            System.out.println(HELP);
            return;
        }

        String pairfile = options.get("pairs");
        String seqlibfile = options.get("seqlib");
        String matrixfile = options.get("m");
        String mode = options.get("mode");
        String format = options.get("format");

        int gapOpen = Integer.parseInt(options.getOrDefault("go","-12"));
        int gapExtend = Integer.parseInt(options.getOrDefault("ge","-1"));

        boolean nw = options.containsKey("nw");
        boolean check = options.containsKey("check");

        GapPenalty gapPenalty = new GapPenalty(gapOpen,gapExtend);

        try {

            InputReader reader = new InputReader();

            Map<String,Sequence> seqs =
                    reader.readSeqLib(Path.of(seqlibfile));

            List<Pair> pairs =
                    reader.readPairs(Path.of(pairfile));

            Matrix matrix =
                    Matrix.readMatrix(Path.of(matrixfile));

            for(Pair pair : pairs){

                Sequence s1 = seqs.get(pair.getId1());
                Sequence s2 = seqs.get(pair.getId2());

                AlignmentAlgorithm alg;

                if(nw){

                    switch(mode){
                        case "global":
                            alg = new NeedlemanWunschGlobal(s1,s2,matrix,gapPenalty);
                            break;

                        case "local":
                            alg = new NeedlemanWunschLocal(s1,s2,matrix,gapPenalty);
                            break;

                        case "freeshift":
                            alg = new NeedlemanWunschFreeshift(s1,s2,matrix,gapPenalty);
                            break;

                        default:
                            System.out.println(HELP);
                            return;
                    }

                } else {

                    switch(mode){
                        case "global":
                            alg = new GotohGlobal(s1,s2,matrix,gapPenalty);
                            break;

                        case "local":
                            alg = new GotohLocal(s1,s2,matrix,gapPenalty);
                            break;

                        case "freeshift":
                            alg = new GotohFreeshift(s1,s2,matrix,gapPenalty);
                            break;

                        default:
                            System.out.println(HELP);
                            return;
                    }
                }

                alg.align();
                Alignment ali = alg.getResult();

                if(check){
                    int recalculated =
                            CheckScore.score(ali,matrix,gapPenalty);

                    if(recalculated != ali.getScore()){
                        Output.print(ali,format);
                    }
                } else {
                    Output.print(ali,format);
                }
            }

        } catch(IOException e){
            System.out.println(e.getMessage());
        }
    }

    private static Map<String, String> parseArgs(String[] args) {

        Map<String, String> map = new HashMap<>();

        for (int i = 0; i < args.length; i++) {

            if (args[i].startsWith("-")) {

                String key = args[i].replaceFirst("^-+", "");

                if (i + 1 < args.length && !args[i + 1].startsWith("--")) {
                    map.put(key, args[i + 1]);
                    i++;
                } else {
                    map.put(key, "true");
                }
            }
        }

        return map;
    }
}
import java.io.BufferedReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public class AlignmentReader {
    public static Alignment readAli(Path path, Matrix matrix, GapPenalty gapPenalty) throws IOException {

        String id1 = "";
        String id2 = "";
        String aligned1 = "";
        String aligned2 = "";
        String seq1string = "";
        String seq2string = "";
        String mode = "G";

        try (BufferedReader reader = Files.newBufferedReader(path)) {
            String line;

            while ((line = reader.readLine()) != null) {

                line = line.trim();
                if (line.isEmpty()) continue;

                String[] words = line.split("\\s+");

                switch(words[0]) {

                    case "Seq1":
                        id1 = words[1];
                        seq1string = words[2];
                        break;

                    case "Seq2":
                        id2 = words[1];
                        seq2string = words[2];
                        break;

                    case "Aligned1":
                        aligned1 = words[1];
                        break;

                    case "Aligned2":
                        aligned2 = words[1];
                        break;

                    case "Mode":
                        mode = words[1];
                        break;
                }
            }
        }

        Sequence seq1 = new Sequence(id1, seq1string);
        Sequence seq2 = new Sequence(id2, seq2string);

        Alignment ali = new Alignment(
                id1, id2,
                aligned1, aligned2,
                0,
                0, seq1string.length(),
                0, seq2string.length(),
                seq1, seq2,
                mode
        );

        double score = CheckScore.score(ali, matrix, gapPenalty);

        return new Alignment(
                id1, id2,
                aligned1, aligned2,
                score,
                0, seq1string.length(),
                0, seq2string.length(),
                seq1, seq2,
                mode
        );
    }
}

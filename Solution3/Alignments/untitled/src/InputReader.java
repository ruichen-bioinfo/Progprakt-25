import java.io.BufferedReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class InputReader {

    // liest Seqlib-Datei und baut eine Map
    public Map<String, Sequence> readSeqLib(Path seqlibFile) throws IOException {
        Map<String, Sequence> seqs = new HashMap<>();

        // Datei zeilenweise oeffnen
        try (BufferedReader br = Files.newBufferedReader(seqlibFile)) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) continue;

                int colon = line.indexOf(':');
                if (colon < 0) continue;

                String id = line.substring(0, colon).trim();
                String seq = line.substring(colon + 1).trim();
                if (id.isEmpty() || seq.isEmpty()) continue;

                Sequence s = new Sequence(seq, id);
                s.setLength(seq.length());
                seqs.put(id, s);
            }
        }

        return seqs;
    }

    public List<Pair> readPairs(Path pairsFile) throws IOException {
        List<Pair> pairs = new ArrayList<>();

        try (BufferedReader br = Files.newBufferedReader(pairsFile)) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) continue;

                // aufteilen nach beliebig vielen Whitespaces
                String[] parts = line.split("\\s+");
                if (parts.length < 2) continue;

                String id1 = parts[0];
                String id2 = parts[1];

                // alles nach ersten 2 Tokens als Annotation speichern
                String annotation = "";
                if (parts.length > 2) {
                    StringBuilder sb = new StringBuilder();
                    for (int i = 2; i < parts.length; i++) {
                        if (i > 2) sb.append(' ');
                        sb.append(parts[i]);
                    }
                    annotation = sb.toString();
                }

                pairs.add(new Pair(id1, id2, annotation));
            }
        }

        return pairs;
    }
}
import java.io.BufferedReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public class ValidationInputReader {

    public List<ValidationCase> readCases(Path inputFile) throws IOException {
        List<ValidationCase> cases = new ArrayList<>();

        try (BufferedReader br = Files.newBufferedReader(inputFile)) {
            String line;

            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) continue;

                // jeder Block startet mit einem Header
                if (!line.startsWith(">")) continue;

                String header = line;

                String candLine1 = readNextNonEmptyLine(br);
                String candLine2 = readNextNonEmptyLine(br);
                String refLine1 = readNextNonEmptyLine(br);
                String refLine2 = readNextNonEmptyLine(br);

                if (candLine1 == null || candLine2 == null || refLine1 == null || refLine2 == null) {
                    break;
                }

                ParsedLine c1 = parseAlignmentLine(candLine1);
                ParsedLine c2 = parseAlignmentLine(candLine2);
                ParsedLine r1 = parseAlignmentLine(refLine1);
                ParsedLine r2 = parseAlignmentLine(refLine2);

                PairAlignment candidate = new PairAlignment(c1.id, c2.id, c1.sequence, c2.sequence);
                PairAlignment reference = new PairAlignment(r1.id, r2.id, r1.sequence, r2.sequence);

                cases.add(new ValidationCase(header, candidate, reference));
            }
        }

        return cases;
    }

    private String readNextNonEmptyLine(BufferedReader br) throws IOException {
        String line;

        while ((line = br.readLine()) != null) {
            line = line.trim();
            if (!line.isEmpty()) {
                return line;
            }
        }

        return null;
    }

    private ParsedLine parseAlignmentLine(String line) {
        int colon = line.indexOf(':');
        if (colon < 0) {
            return new ParsedLine("", line.trim());
        }

        String id = line.substring(0, colon).trim();
        String sequence = line.substring(colon + 1).trim();

        return new ParsedLine(id, sequence);
    }

    private static class ParsedLine {
        String id;
        String sequence;

        ParsedLine(String id, String sequence) {
            this.id = id;
            this.sequence = sequence;
        }
    }
}
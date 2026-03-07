import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.Locale;
import java.nio.file.Paths;

public class ValidateAliMain {

    public static void main(String[] args) {
        if (args.length != 2 || !args[0].equals("-f")) {
            printHelp();
            return;
        }

        Path inputFile = Paths.get(args[1]);

        ValidationInputReader reader = new ValidationInputReader();
        AlignmentMetrics metrics = new AlignmentMetrics();

        try {
            List<ValidationCase> cases = reader.readCases(inputFile);

            for (ValidationCase validationCase : cases) {
                ValidationResult result = metrics.evaluate(
                        validationCase.getCandidate(),
                        validationCase.getReference()
                );

                printCase(validationCase, result);
            }
        } catch (IOException e) {
            System.err.println("Error while reading validation input: " + e.getMessage());
        }
    }

    private static void printCase(ValidationCase validationCase, ValidationResult result) {
        String header = validationCase.getHeader();

        System.out.println(
                header
                        + " " + format(result.getSensitivity())
                        + " " + format(result.getSpecificity())
                        + " " + format(result.getCoverage())
                        + " " + format(result.getMeanShiftError())
                        + " " + format(result.getInverseMeanShiftError())
        );

        printAlignment(validationCase.getCandidate());
        printAlignment(validationCase.getReference());
    }

    private static void printAlignment(PairAlignment alignment) {
        System.out.println(alignment.getId1() + ": " + alignment.getAlignedSeq1());
        System.out.println(alignment.getId2() + ": " + alignment.getAlignedSeq2());
    }

    private static String format(double value) {
        return String.format(Locale.ENGLISH, "%.4f", value);
    }

    private static void printHelp() {
        System.out.println("Syntax:");
        System.out.println("java -jar validateAli.jar -f <alignment-pairs>");
        System.out.println("Options:");
        System.out.println("    -f <alignment-pairs>    file containing alignment pairs");
    }
}
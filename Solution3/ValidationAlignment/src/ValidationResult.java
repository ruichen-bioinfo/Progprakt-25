public class ValidationResult {

    private final double sensitivity;
    private final double specificity;
    private final double coverage;
    private final double meanShiftError;
    private final double inverseMeanShiftError;

    public ValidationResult(double sensitivity, double specificity, double coverage,
                            double meanShiftError, double inverseMeanShiftError) {
        this.sensitivity = sensitivity;
        this.specificity = specificity;
        this.coverage = coverage;
        this.meanShiftError = meanShiftError;
        this.inverseMeanShiftError = inverseMeanShiftError;
    }

    public double getSensitivity() {
        return sensitivity;
    }

    public double getSpecificity() {
        return specificity;
    }

    public double getCoverage() {
        return coverage;
    }

    public double getMeanShiftError() {
        return meanShiftError;
    }

    public double getInverseMeanShiftError() {
        return inverseMeanShiftError;
    }
}
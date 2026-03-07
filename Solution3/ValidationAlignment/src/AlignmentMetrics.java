public class AlignmentMetrics {

    public ValidationResult evaluate(PairAlignment candidate, PairAlignment reference) {
        double sensitivity = computeSensitivity(candidate, reference);
        double specificity = computeSpecificity(candidate, reference);

        // erstmal nur Platzhalter
        double coverage = 0.0;
        double meanShiftError = 0.0;
        double inverseMeanShiftError = 0.0;

        return new ValidationResult(sensitivity, specificity, coverage,
                meanShiftError, inverseMeanShiftError);
    }

    public double computeSensitivity(PairAlignment candidate, PairAlignment reference) {
        int correct = AlignmentMappingUtils.countCorrectlyAlignedResidues(candidate, reference);
        int referenceAligned = AlignmentMappingUtils.countAlignedResidues(reference);

        if (referenceAligned == 0) {
            return 0.0;
        }

        return (double) correct / referenceAligned;
    }

    public double computeSpecificity(PairAlignment candidate, PairAlignment reference) {
        int correct = AlignmentMappingUtils.countCorrectlyAlignedResidues(candidate, reference);
        int candidateAligned = AlignmentMappingUtils.countAlignedResidues(candidate);

        if (candidateAligned == 0) {
            return 0.0;
        }

        return (double) correct / candidateAligned;
    }

    public double computeCoverage(PairAlignment candidate, PairAlignment reference) {
        return 0.0;
    }

    public double computeMeanShiftError(PairAlignment candidate, PairAlignment reference) {
        return 0.0;
    }

    public double computeInverseMeanShiftError(PairAlignment candidate, PairAlignment reference) {
        return 0.0;
    }
}
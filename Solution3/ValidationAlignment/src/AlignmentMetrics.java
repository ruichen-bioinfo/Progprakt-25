import java.util.Map;

public class AlignmentMetrics {

    public ValidationResult evaluate(PairAlignment candidate, PairAlignment reference) {
        double sensitivity = computeSensitivity(candidate, reference);
        double specificity = computeSpecificity(candidate, reference);
        double coverage = computeCoverage(candidate, reference);
        double meanShiftError = computeMeanShiftError(candidate, reference);

        // erstmal nur Platzhalter
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
        Map<Integer, Integer> candidateMap = AlignmentMappingUtils.mapSeq2ToSeq1(candidate);
        Map<Integer, Integer> referenceMap = AlignmentMappingUtils.mapSeq2ToSeq1(reference);

        int candidateAligned = candidateMap.size();
        if (candidateAligned == 0) {
            return 0.0;
        }

        int definedShiftCount = 0;
        for (Integer targetResidue : candidateMap.keySet()) {
            if (referenceMap.containsKey(targetResidue)) {
                definedShiftCount++;
            }
        }
        return (double) definedShiftCount / candidateAligned;
    }

    public double computeMeanShiftError(PairAlignment candidate, PairAlignment reference) {
        Map<Integer, Integer> candidateMap = AlignmentMappingUtils.mapSeq2ToSeq1(candidate);
        Map<Integer, Integer> referenceMap = AlignmentMappingUtils.mapSeq2ToSeq1(reference);

        int definedCount = 0;
        int shiftSum = 0;

        for (Integer targetResidue : candidateMap.keySet()) {
            if (!referenceMap.containsKey(targetResidue)) {
                continue;
            }

            int candidateTemplatePos = candidateMap.get(targetResidue);
            int referenceTemplatePos = referenceMap.get(targetResidue);

            shiftSum += Math.abs(candidateTemplatePos - referenceTemplatePos);
            definedCount++;
        }

        if (definedCount == 0) {
            return 0.0;
        }

        return (double) shiftSum / definedCount;
    }

    public double computeInverseMeanShiftError(PairAlignment candidate, PairAlignment reference) {
        return 0.0;
    }
}
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public class AlignmentMappingUtils {

    // alle Residuenpaare, die in einem Alignment wirklich aufeinander liegen
    public static Set<ResiduePair> getAlignedResiduePairs(PairAlignment alignment) {
        Set<ResiduePair> pairs = new HashSet<>();

        String seq1 = alignment.getAlignedSeq1();
        String seq2 = alignment.getAlignedSeq2();

        int pos1 = 0;
        int pos2 = 0;

        for (int i = 0; i < seq1.length(); i++) {
            char c1 = seq1.charAt(i);
            char c2 = seq2.charAt(i);

            int residue1 = -1;
            int residue2 = -1;

            if (c1 != '-') {
                pos1++;
                residue1 = pos1;
            }

            if (c2 != '-') {
                pos2++;
                residue2 = pos2;
            }

            if (residue1 != -1 && residue2 != -1) {
                pairs.add(new ResiduePair(residue1, residue2));
            }
        }

        return pairs;
    }

    // mapping von seq1-residuum -> seq2-residuum
    public static Map<Integer, Integer> mapSeq1ToSeq2(PairAlignment alignment) {
        Map<Integer, Integer> map = new HashMap<>();

        String seq1 = alignment.getAlignedSeq1();
        String seq2 = alignment.getAlignedSeq2();

        int pos1 = 0;
        int pos2 = 0;

        for (int i = 0; i < seq1.length(); i++) {
            char c1 = seq1.charAt(i);
            char c2 = seq2.charAt(i);

            int residue1 = -1;
            int residue2 = -1;

            if (c1 != '-') {
                pos1++;
                residue1 = pos1;
            }

            if (c2 != '-') {
                pos2++;
                residue2 = pos2;
            }

            if (residue1 != -1 && residue2 != -1) {
                map.put(residue1, residue2);
            }
        }

        return map;
    }

    // mapping von seq2-residuum -> seq1-residuum
    public static Map<Integer, Integer> mapSeq2ToSeq1(PairAlignment alignment) {
        Map<Integer, Integer> map = new HashMap<>();

        String seq1 = alignment.getAlignedSeq1();
        String seq2 = alignment.getAlignedSeq2();

        int pos1 = 0;
        int pos2 = 0;

        for (int i = 0; i < seq1.length(); i++) {
            char c1 = seq1.charAt(i);
            char c2 = seq2.charAt(i);

            int residue1 = -1;
            int residue2 = -1;

            if (c1 != '-') {
                pos1++;
                residue1 = pos1;
            }

            if (c2 != '-') {
                pos2++;
                residue2 = pos2;
            }

            if (residue1 != -1 && residue2 != -1) {
                map.put(residue2, residue1);
            }
        }

        return map;
    }

    public static int countAlignedResidues(PairAlignment alignment) {
        return getAlignedResiduePairs(alignment).size();
    }

    public static int countCorrectlyAlignedResidues(PairAlignment candidate, PairAlignment reference) {
        Set<ResiduePair> candidatePairs = getAlignedResiduePairs(candidate);
        Set<ResiduePair> referencePairs = getAlignedResiduePairs(reference);

        int count = 0;
        for (ResiduePair pair : candidatePairs) {
            if (referencePairs.contains(pair)) {
                count++;
            }
        }

        return count;
    }

    public static class ResiduePair {
        private final int pos1;
        private final int pos2;

        public ResiduePair(int pos1, int pos2) {
            this.pos1 = pos1;
            this.pos2 = pos2;
        }

        public int getPos1() {
            return pos1;
        }

        public int getPos2() {
            return pos2;
        }

        @Override
        public boolean equals(Object obj) {
            if (this == obj) return true;
            if (!(obj instanceof ResiduePair)) return false;

            ResiduePair other = (ResiduePair) obj;
            return pos1 == other.pos1 && pos2 == other.pos2;
        }

        @Override
        public int hashCode() {
            int result = Integer.hashCode(pos1);
            result = 31 * result + Integer.hashCode(pos2);
            return result;
        }
    }
}
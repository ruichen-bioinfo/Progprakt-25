public class PairAlignment {

    private final String id1;
    private final String id2;
    private final String alignedSeq1;
    private final String alignedSeq2;

    public PairAlignment (String id1, String id2, String alignedSeq1, String alignedSeq2) {
        this.id1 = id1;
        this.id2 = id2;
        this.alignedSeq1 = alignedSeq1;
        this.alignedSeq2 = alignedSeq2;
    }

    public String getId1() {
        return id1;
    }

    public String getId2() {
        return id2;
    }

    public String getAlignedSeq1() {
        return alignedSeq1;
    }

    public String getAlignedSeq2() {
        return alignedSeq2;
    }

    // ungegappte erste Sequenz
    public String getUngappedSeq1() {
        return alignedSeq1.replace("-","");
    }

    // ungegappte zweite Sequenz
    public String getUngappedSeq2() {
        return alignedSeq2.replace("-","");
    }

    public int getAlignmentLength() {
        return alignedSeq1.length();
    }

    public boolean hasSameLength() {
        return alignedSeq1.length() == alignedSeq2.length();
    }
}

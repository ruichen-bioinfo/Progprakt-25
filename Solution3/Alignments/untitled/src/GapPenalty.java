public class GapPenalty {

    private final int open;
    private final int extend;

    public GapPenalty(int open, int extend) {
        this.open = open;
        this.extend = extend;
    }
    public int getOpen() {
        return open;
    }
    public int getExtend() {
        return extend;
    }
    // affine open + (len-1) * extend
    public int cost(int len) {
        if (len <= 0) return 0;
        return open + (len-1) * extend;
    }
    // für NW linear
    public int linearCost() {
        return open;
    }
}

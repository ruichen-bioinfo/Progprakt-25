public class Sequence {
    private String sequence;
    private String ID;
    private int length;

    public Sequence(String sequence, String ID) {
        this.sequence = sequence;
        this.ID = ID;
    }

    public String getSequence() {
        return sequence;
    }
    public void setSequence(String sequence) {
        this.sequence = sequence;
    }
    public String getID() {
        return ID;
    }
    public void setID(String ID) {
        this.ID = ID;
    }

    public int getLength() {
        return length;
    }
    public void setLength(int length) {
        this.length = length;
    }
    public char charAt(int index) {
        return sequence.charAt(index);
    }

}

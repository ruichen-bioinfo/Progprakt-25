public class Pair {

    private final String id1;
    private final String id2;
    private final String annotation; // kann leer sein

    public Pair(String id1, String id2, String annotation) {
        this.id1 = id1;
        this.id2 = id2;
        this.annotation = (annotation == null) ? "" : annotation;
    }

    public String getId1() {
        return id1;
    }

    public String getId2() {
        return id2;
    }

    public String getAnnotation() {
        return annotation;
    }
}
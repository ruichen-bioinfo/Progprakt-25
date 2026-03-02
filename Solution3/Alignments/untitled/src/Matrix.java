public class Matrix {
    private int[][] values;

    public Matrix(int rows, int cols) {
        values = new int[rows][cols];
    }

    public void set(int row, int col, int value) {
        values[row][col] = value;
    }

    public int get(int row, int col) {
        return values[row][col];
    }

    public void printMatrix() {
        for (int i = 0; i < values.length; i++) {
            for (int j = 0; j < values[i].length; j++) {
                System.out.print(values[i][j] + " ");
            }
        }
    }

}

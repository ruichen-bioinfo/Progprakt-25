import java.util.Map;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;

public class Matrix {
    private int[][] Matrix;
    private Map<Character, Integer> map;

    public Matrix(int[][] matrix, Map<Character, Integer> map) {
        this.Matrix = matrix;
        this.map = map;
    }

    public int score(char c, char d) {
        int i = map.get(c);
        int j = map.get(d);
        int score = Matrix[i][j];
        return score;

    }

    public void readMatrix() {
        BufferedReader reader = new BufferedReader(FileReader())
    }



}

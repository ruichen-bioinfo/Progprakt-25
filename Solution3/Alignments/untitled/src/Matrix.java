import java.util.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;

public class Matrix {
    private int[][] Matrix;
    private Map<Character, Integer> map;
    //similarity = true soll heißen similarity score = false soll heißen distance score
    boolean similarity;

    public Matrix(int[][] matrix, Map<Character, Integer> map, boolean similarity) {
        this.Matrix = matrix;
        this.map = map;
        this.similarity = similarity;
    }

    public int score(char c, char d) {
        int i = map.get(c);
        int j = map.get(d);

        int score = Matrix[i][j];
        return score;

    }

    public static Matrix readMatrix(Path path) throws IOException {
        boolean similarity = false;
        int rowCount = 0;
        int colCount = 0;
        String rowIndex = null;
        String colIndex = null;
        List<int[]> matrixRows = new ArrayList<>();


        try (BufferedReader reader = Files.newBufferedReader(path)) {
            String line;
            while ((line = reader.readLine()) != null) {
                line = line.trim();

                if (line.startsWith("#")){
                    continue;
                }

                String[] words = line.split("\\s+");


                if (line.startsWith("SCORE")){
                    if (Objects.equals(words[1], "similarity")){
                        similarity = true;
                    }
                    else{
                        similarity = false;
                    }
                }
                if (line.startsWith("NUMROW")){
                    rowCount = Integer.parseInt(words[1]);
                }
                if (line.startsWith("NUMCOL")){
                    colCount = Integer.parseInt(words[1]);
                }
                if (line.startsWith("ROWINDEX")){
                    rowIndex = words[1];
                }
                if (line.startsWith("COLINDEX")){
                    colIndex = words[1];
                }


                if (line.startsWith("MATRIX")){
                    int[] row = new int[words.length - 1];
                    for (int i = 1; i < words.length; i++) {
                        String value = words[i].replace(".", "");
                        row[i - 1] = Integer.parseInt(value);
                    }
                    matrixRows.add(row);
                }

            }

        }
        int[][] matrix = new int[rowCount][colCount];
        for (int i = 0; i < matrixRows.size(); i++) {
            int[] row = matrixRows.get(i);
            for (int j = 0; j <= i; j++) {
                //wegen symmetrie
                matrix[i][j] = row[j];
                matrix[j][i] = row[j];
            }
        }
        Map<Character, Integer> map = new HashMap<>();
        for (int i = 0; i < rowIndex.length(); i++) {
            map.put(rowIndex.charAt(i), i);
        }
        return new Matrix(matrix, map, similarity);
    }






}

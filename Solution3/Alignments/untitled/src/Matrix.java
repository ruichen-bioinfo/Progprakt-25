import java.util.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;

public class Matrix {
    private double[][] Matrix;
    private Map<Character, Integer> map;
    //similarity = true soll heißen similarity score = false soll heißen distance score
    boolean similarity;

    public Matrix(double[][] matrix, Map<Character, Integer> map, boolean similarity) {
        this.Matrix = matrix;
        this.map = map;
        this.similarity = similarity;
    }

    public double score(char c, char d) {
        int i = map.get(c);
        int j = map.get(d);

        double score = Matrix[i][j];
        return score;

    }

    public static Matrix readMatrix(Path path) throws IOException {
        boolean similarity = false;
        int rowCount = 0;
        int colCount = 0;
        String rowIndex = null;
        String colIndex = null;
        List<double[]> matrixRows = new ArrayList<>();


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
                    double[] row = new double[words.length - 1];
                    for (int i = 1; i < words.length; i++) {
                        row[i - 1] = Double.parseDouble(words[i]);

                    }
                    matrixRows.add(row);
                }

            }

        }
        double[][] matrix = new double[rowCount][colCount];

        for (int i = 0; i < matrixRows.size() && i < rowCount; i++) {
            double[] row = matrixRows.get(i);
            for (int j = 0; j < row.length && j < colCount; j++) {
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

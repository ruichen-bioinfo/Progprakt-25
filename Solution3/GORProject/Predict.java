import java.io.*;
import java.util.*;
public class Predict {
    private static final String AA_ORDER = "ACDEFGHIKLMNPQRSTVWY";
    private static final String SS_ORDER = "CEH";
    private static final int WINDOW = 17;
    private static final int CENTER = 8;

    static class GorModel {
        String method;
        long total;
        long[] priors = new long[3];
        double[][][] counts = new double[3][20][WINDOW];
        double[] logPbg = new double[20];
        double[][][] logPpos = new double[3][WINDOW][20];
        double[][][][] logP1_center=new double[3][20][WINDOW][20];
        double[] logPrior = new double[3];
        double[][][][] counts3 = new double[20][3][WINDOW][20];
        double[][][][] logP3 = new double[20][3][WINDOW][20];
        double[][][][][] logPpair_bg_center=new double[20][20][WINDOW][20][WINDOW];
        double[][][][][][] counts4=new double[3][20][20][WINDOW][20][WINDOW];
        double[][][][][][] logP4=new double[3][20][20][WINDOW][20][WINDOW];
    }

    static class FastaEntry {
        String id;
        String seq;
        FastaEntry(String id, String seq) { this.id = id; this.seq = seq; }
    }

    public static void main(String[] args) throws Exception {
        String modelPath = null;
        String format = "txt";
        String fastaPath = null;
        String refPath = null;          // NEW: --ref flag
        boolean probabilities = false;
        boolean isMaf = false;

        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--model":
                    if (i + 1 < args.length) modelPath = args[++i]; break;
                case "--format":
                    if (i + 1 < args.length) format = args[++i]; break;
                case "--seq":
                    if (i + 1 < args.length) fastaPath = args[++i]; break;
                case "--ref":                                          // NEW
                    if (i + 1 < args.length) refPath = args[++i]; break;
                case "--probabilities":
                    probabilities = true; break;
                case "--maf":
                    if (i + 1 < args.length) fastaPath = args[++i];
                    isMaf = true; break;
                case "--help":
                    printHelpAndExit(0); break;
                default: break;
            }
        }
        if (modelPath == null || fastaPath == null) printHelpAndExit(1);

        String type = peekModelType(modelPath);
        GorModel model = null;
        if (type.equals("Gor3")) { model=loadModelMatrixGor3(modelPath); precomputeLogs3(model,1.0); }
        else if (type.equals("Gor1")) { model=loadModelMatrixGor1(modelPath); precumputeLogs1(model,1.0); }
        else if (type.equals("Gor4")) { model=loadModelMAtrixGor4(modelPath); precomputeLogs3(model,0.015); precomputeLogs4(model,0.015); }
        else { System.err.println("Unrecognized model type: "+type); System.exit(1); }

        // Load reference SS if provided
        Map<String,String> refMap = new HashMap<>();
        if (refPath != null) refMap = loadRefSS(refPath);

        if (isMaf) {
            File dirOrFile = new File(fastaPath);
            List<File> alnFiles = new ArrayList<>();
            if (dirOrFile.isDirectory()) {
                File[] arr = dirOrFile.listFiles((d, name) -> name.toLowerCase().endsWith(".aln"));
                if (arr != null) alnFiles.addAll(Arrays.asList(arr));
                alnFiles.sort(Comparator.comparing(File::getName));
            } else { alnFiles.add(dirOrFile); }
            for (File aln : alnFiles) {
                try {
                    MafEntry e = readMafFastaAlignment(aln);
                    if (e == null) continue;
                    Prediction pred = predictGor5FromQueryAligned(e.as, e.alignedSeqs, model);
                    String ref = refMap.get(e.id);
                    writeTxt(System.out, e.id, e.as, pred, probabilities, ref);
                } catch (Exception ex) {
                    System.err.println("SKIP " + aln.getName() + ": " + ex.getMessage());
                }
            }
            return;
        }

        File input = new File(fastaPath);
        List<File> fastaFiles = new ArrayList<>();
        if (input.isDirectory()) {
            File[] arr = input.listFiles();
            if (arr != null) for (File x : arr) if (x.isFile() && !x.getName().startsWith(".")) fastaFiles.add(x);
            fastaFiles.sort(Comparator.comparing(File::getName));
        } else { fastaFiles.add(input); }

        if (format.equals("txt")) {
            for (File ff : fastaFiles) {
                List<FastaEntry> entries = readFasta(ff.getPath());
                for (FastaEntry e : entries) {
                    Prediction pred = predictOne(e.seq, model, probabilities);
                    String ref = refMap.get(e.id);
                    writeTxt(System.out, e.id, e.seq, pred, probabilities, ref);
                }
            }
        } else {
            List<FastaEntry> all = new ArrayList<>();
            for (File ff : fastaFiles) all.addAll(readFasta(ff.getPath()));
            writeHTML(System.out, all, model, probabilities);
        }
    }

    // NEW: load reference SS from a simple text file
    // Format: either plain ">id\nSS_STRING" or just one SS string per line
    static Map<String,String> loadRefSS(String path) throws IOException {
        Map<String,String> map = new HashMap<>();
        try (BufferedReader br = new BufferedReader(new FileReader(path))) {
            String line, curId = null;
            StringBuilder sb = new StringBuilder();
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) continue;
                if (line.startsWith(">")) {
                    if (curId != null && sb.length() > 0) map.put(curId, sb.toString());
                    curId = line.substring(1).trim();
                    sb.setLength(0);
                } else if (line.startsWith("PS ")) {
                    // seclib/predict output format
                    if (curId != null) { map.put(curId, line.substring(3).trim()); curId = null; }
                } else if (curId != null) {
                    sb.append(line);
                }
            }
            if (curId != null && sb.length() > 0) map.put(curId, sb.toString());
        }
        return map;
    }

    // NEW: generate match line: '|' for match, '.' for mismatch, ' ' for length diff
    static String matchLine(String pred, String ref) {
        int len = Math.min(pred.length(), ref.length());
        StringBuilder sb = new StringBuilder();
        int matches = 0;
        for (int i = 0; i < len; i++) {
            if (pred.charAt(i) == ref.charAt(i)) { sb.append('|'); matches++; }
            else sb.append('.');
        }
        double q3 = len > 0 ? (double) matches / len * 100 : 0;
        return sb.toString() + String.format(Locale.US, "  Q3=%.1f%%", q3);
    }

    static String peekModelType(String path) throws IOException {
        try (BufferedReader br = new BufferedReader(new FileReader(path))) {
            String line;
            while ((line = br.readLine()) != null) {
                if (line.contains("Matrix4D")) return "Gor3";
                if (line.contains("Matrix3D")) return "Gor1";
                if (line.contains("Matrix6D")) return "Gor4";
            }
            return "unknown";
        }
    }

    static void printHelpAndExit(int exitCode) {
        System.out.println("Usage: java -jar predict.jar --model MODEL --seq FASTA [--ref REF] [--format txt|html] [--probabilities] [--maf ALN]");
        System.exit(exitCode);
    }

    static GorModel loadModelMatrixGor1(String modelPath) throws Exception {
        GorModel model = new GorModel();
        int currentstate = -1;
        try (BufferedReader br = new BufferedReader(new FileReader(modelPath))) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) continue;
                if (line.startsWith("//")) continue;
                if (line.startsWith("=") && line.endsWith("=") && line.length() >= 3) {
                    char st = line.charAt(1);
                    currentstate = SS_ORDER.indexOf(st);
                    if (currentstate < 0) throw new IllegalStateException("Unknown state: " + line);
                    continue;
                }
                if (currentstate < 0) continue;
                String[] tokens = line.split("\\s+");
                if (tokens.length < 1 + WINDOW) throw new IOException("Bad AA" + line);
                char aaChar = tokens[0].charAt(0);
                int a = AA_ORDER.indexOf(aaChar);
                if (a < 0) continue;
                for (int w = 0; w < WINDOW; w++)
                    model.counts[currentstate][a][w] = Double.parseDouble(tokens[1 + w]);
            }
        }
        model.method = "gor1";
        return model;
    }

    static GorModel loadModelMatrixGor3(String modelPath) throws Exception {
        GorModel model = new GorModel();
        int curCenter = -1, curState = -1;
        try (BufferedReader br = new BufferedReader(new FileReader(modelPath))) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) continue;
                if (line.startsWith("//")) continue;
                if (line.startsWith("=") && line.endsWith("=")) {
                    String inside = line.substring(1, line.length() - 1).trim();
                    String[] parts = inside.split(",");
                    if (parts.length != 2) throw new IllegalStateException("Not 4d header" + line);
                    curCenter = AA_ORDER.indexOf(parts[0].trim().charAt(0));
                    curState = SS_ORDER.indexOf(parts[1].trim().charAt(0));
                    if (curCenter < 0 || curState < 0) throw new IllegalStateException("Bad header" + line);
                    continue;
                }
                if (curCenter < 0 || curState < 0) continue;
                String[] tokens = line.split("\\s+");
                if (tokens.length < 1 + WINDOW) throw new IOException("Bad AA" + line);
                int neigh = AA_ORDER.indexOf(tokens[0].charAt(0));
                if (neigh < 0) continue;
                for (int w = 0; w < WINDOW; w++)
                    model.counts3[curCenter][curState][w][neigh] = Double.parseDouble(tokens[1 + w]);
            }
        }
        model.method = "gor3";
        return model;
    }

    static String removeGaps(String s) { return s.replaceAll("[-.]",""); }
    static boolean isGap(char c) { return c=='-'|| c=='.'; }
    static boolean isAA(char c) { return AA_ORDER.indexOf(c)>=0; }
    static String keepAAOnly(String s) {
        s=s.toUpperCase(); StringBuilder sb=new StringBuilder(s.length());
        for(int i=0;i<s.length();i++){char c=s.charAt(i);if(isAA(c))sb.append(c);}
        return sb.toString();
    }
    static String keepAAorGap(String s) {
        s=s.toUpperCase(); StringBuilder sb=new StringBuilder(s.length());
        for(int i=0;i<s.length();i++){char c=s.charAt(i);if(isAA(c)||isGap(c))sb.append(c);}
        return sb.toString();
    }

    static GorModel loadModelMAtrixGor4(String modelPath) throws Exception {
        GorModel model = new GorModel();
        int curState=-1,curCenter=-1,curA1=-1,curOffIdx=-1;
        boolean in6D=false,in4D=false;
        int cur4DCenter=-1,cur4DState=-1;
        try (BufferedReader br = new BufferedReader(new FileReader(modelPath))) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) continue;
                if (line.equals("// Matrix6D")) { in6D=true; in4D=false; continue; }
                if (line.equals("// Matrix4D")) { in4D=true; in6D=false; continue; }
                if (line.startsWith("//")) continue;
                if (line.startsWith("=") && line.endsWith("=")) {
                    String inside=line.substring(1,line.length()-1).trim();
                    String[] parts=inside.split(",");
                    if (in6D && parts.length==4) {
                        curState=SS_ORDER.indexOf(parts[0].trim().charAt(0));
                        curCenter=AA_ORDER.indexOf(parts[1].trim().charAt(0));
                        curA1=AA_ORDER.indexOf(parts[2].trim().charAt(0));
                        curOffIdx=Integer.parseInt(parts[3].trim())+CENTER;
                        if(curState<0||curCenter<0||curA1<0||curOffIdx<0||curOffIdx>=WINDOW) curState=-1;
                    } else if (in4D && parts.length==2) {
                        cur4DCenter=AA_ORDER.indexOf(parts[0].trim().charAt(0));
                        cur4DState=SS_ORDER.indexOf(parts[1].trim().charAt(0));
                        if(cur4DCenter<0||cur4DState<0) cur4DCenter=-1;
                    }
                    continue;
                }
                if (in6D && curState>=0) {
                    String full=line; String[] tokens=full.split("\\s+");
                    while(tokens.length<1+WINDOW){String cont=br.readLine();if(cont==null)break;cont=cont.trim();if(cont.isEmpty())continue;full=full+" "+cont;tokens=full.split("\\s+");}
                    if(tokens.length<1+WINDOW) continue;
                    int aa2=AA_ORDER.indexOf(tokens[0].charAt(0)); if(aa2<0) continue;
                    for(int w=0;w<WINDOW;w++) model.counts4[curState][curCenter][curA1][curOffIdx][aa2][w]=Double.parseDouble(tokens[1+w]);
                } else if (in4D && cur4DCenter>=0) {
                    String[] tokens=line.split("\\s+"); if(tokens.length<1+WINDOW) continue;
                    int nAA=AA_ORDER.indexOf(tokens[0].charAt(0)); if(nAA<0) continue;
                    for(int w=0;w<WINDOW;w++) model.counts3[cur4DCenter][cur4DState][w][nAA]=Double.parseDouble(tokens[1+w]);
                }
            }
        }
        model.method="gor4";
        return model;
    }

    static void precumputeLogs1(GorModel model,double alpha){
        double[]bgCount=new double[20];double bgTotal=0.0;
        for(int s=0;s<3;s++){long total=0;for(int a=0;a<20;a++)total+=(long)model.counts[s][a][CENTER];model.priors[s]=total;}
        for(int a=0;a<20;a++){double c=0.0;for(int s=0;s<3;s++)c+=model.counts[s][a][CENTER];bgCount[a]=c;bgTotal+=c;}
        double denomBg=bgTotal+20.0*alpha;
        for(int a=0;a<20;a++) model.logPbg[a]=Math.log((bgCount[a]+alpha)/denomBg);
        double priorSum=(double)model.priors[0]+model.priors[1]+model.priors[2];double denomPrior=priorSum+3.0*alpha;
        for(int s=0;s<3;s++){model.logPrior[s]=Math.log((model.priors[s]+alpha)/denomPrior);for(int w=0;w<WINDOW;w++){double tot=0.0;for(int a=0;a<20;a++)tot+=model.counts[s][a][w];double denom=tot+20.0*alpha;for(int a=0;a<20;a++)model.logPpos[s][w][a]=Math.log((model.counts[s][a][w]+alpha)/denom);}}
    }

    static void precomputeLogs3(GorModel model,double alpha){
        for(int s=0;s<3;s++){long total=0;for(int c=0;c<20;c++)for(int w=0;w<WINDOW;w++)for(int neigh=0;neigh<20;neigh++)total+=(long)model.counts3[c][s][w][neigh];model.priors[s]=total;}
        double[]bgCount=new double[20];double bgTotal=0.0;
        for(int a=0;a<20;a++){double sum=0.0;for(int c=0;c<20;c++)for(int s=0;s<3;s++)for(int w=0;w<WINDOW;w++)sum+=model.counts3[c][s][w][a];bgCount[a]=sum;bgTotal+=sum;}
        double denomBg=bgTotal+20.0*alpha;for(int a=0;a<20;a++)model.logPbg[a]=Math.log((bgCount[a]+alpha)/denomBg);
        double priorSum=(double)model.priors[0]+model.priors[1]+model.priors[2];double denomPrior=priorSum+3.0*alpha;
        for(int s=0;s<3;s++)model.logPrior[s]=Math.log((model.priors[s]+alpha)/denomPrior);
        for(int c=0;c<20;c++)for(int s=0;s<3;s++)for(int w=0;w<WINDOW;w++){double tot=0.0;for(int a=0;a<20;a++)tot+=model.counts3[c][s][w][a];double denom=tot+20.0*alpha;for(int a=0;a<20;a++)model.logP3[c][s][w][a]=Math.log((model.counts3[c][s][w][a]+alpha)/denom);}
    }

    static void precomputeLogs4(GorModel model,double alpha){
        double[]bgCount=new double[20];double bgTotal=0.0;
        for(int a2=0;a2<20;a2++){double sum=0.0;for(int st=0;st<3;st++)for(int c=0;c<20;c++)for(int a1=0;a1<20;a1++)for(int off=0;off<WINDOW;off++)for(int w=0;w<WINDOW;w++)sum+=model.counts4[st][c][a1][off][a2][w];bgCount[a2]=sum;bgTotal+=sum;}
        double denomBg=bgTotal+20.0*alpha;for(int a2=0;a2<20;a2++)model.logPbg[a2]=Math.log((bgCount[a2]+alpha)/denomBg);
        for(int st=0;st<3;st++){long total=0;for(int c=0;c<20;c++)for(int a1=0;a1<20;a1++)for(int off=0;off<WINDOW;off++)for(int a2=0;a2<20;a2++)total+=(long)model.counts4[st][c][a1][off][a2][CENTER];model.priors[st]=total;}
        double priorSum=(double)model.priors[0]+model.priors[1]+model.priors[2];double denomPrior=priorSum+3.0*alpha;
        for(int st=0;st<3;st++)model.logPrior[st]=Math.log((model.priors[st]+alpha)/denomPrior);
        for(int st=0;st<3;st++)for(int c=0;c<20;c++)for(int a1=0;a1<20;a1++)for(int off=0;off<WINDOW;off++)for(int w=0;w<WINDOW;w++){double tot=0.0;for(int a2=0;a2<20;a2++)tot+=model.counts4[st][c][a1][off][a2][w];double denom=tot+20.0*alpha;for(int a2=0;a2<20;a2++)model.logP4[st][c][a1][off][a2][w]=Math.log((model.counts4[st][c][a1][off][a2][w]+alpha)/denom);}
        for(int c=0;c<20;c++)for(int a1=0;a1<20;a1++)for(int off=0;off<WINDOW;off++)for(int w=0;w<WINDOW;w++){double tot=0.0;double[]agg=new double[20];for(int a2=0;a2<20;a2++){double sum=0.0;for(int st=0;st<3;st++)sum+=model.counts4[st][c][a1][off][a2][w];agg[a2]=sum;tot+=sum;}double denom=tot+20.0*alpha;for(int a2=0;a2<20;a2++)model.logPpair_bg_center[c][a1][off][a2][w]=Math.log((agg[a2]+alpha)/denom);}
        for(int st=0;st<3;st++)for(int w=0;w<WINDOW;w++){double tot=0.0;double[]agg=new double[20];for(int a2=0;a2<20;a2++){double sum=0.0;for(int c=0;c<20;c++)for(int a1=0;a1<20;a1++)for(int off=0;off<WINDOW;off++)sum+=model.counts4[st][c][a1][off][a2][w];agg[a2]=sum;tot+=sum;}double denom=tot+20.0*alpha;for(int a2=0;a2<20;a2++)model.logPpos[st][w][a2]=Math.log((agg[a2]+alpha)/denom);}
        for(int st=0;st<3;st++)for(int c=0;c<20;c++)for(int w=0;w<WINDOW;w++){double tot=0.0;double[]agg=new double[20];for(int a2=0;a2<20;a2++){double sum=0.0;for(int a1=0;a1<20;a1++)for(int off=0;off<WINDOW;off++)sum+=model.counts4[st][c][a1][off][a2][w];agg[a2]=sum;tot+=sum;}double denom=tot+20.0*alpha;for(int a2=0;a2<20;a2++)model.logP1_center[st][c][w][a2]=Math.log((agg[a2]+alpha)/denom);}
    }

    static List<FastaEntry> readFasta(String path) throws IOException {
        List<FastaEntry> out=new ArrayList<>();
        try(BufferedReader br=new BufferedReader(new FileReader(path))){
            String line;String id=null;StringBuilder builder=new StringBuilder();
            while((line=br.readLine())!=null){line=line.trim();if(line.startsWith(">")){if(id!=null)out.add(new FastaEntry(id,builder.toString().toUpperCase()));id=line.substring(1).trim();builder.setLength(0);}else if(!line.isEmpty())builder.append(line.replaceAll("\\s+",""));}
            if(id!=null)out.add(new FastaEntry(id,builder.toString().toUpperCase()));
        }
        return out;
    }

    static class Prediction {
        String ps; double[][]scores;
        Prediction(String ps,double[][]scores){this.ps=ps;this.scores=scores;}
    }

    static Prediction predictOne(String seq,GorModel model,boolean wantProb){
        int n=seq.length();double[][]score=new double[3][n];char[]ps=new char[n];
        String method=model.method==null?"gor1":model.method;
        for(int i=0;i<n;i++){
            char center=seq.charAt(i);int a0=AA_ORDER.indexOf(center);
            if(a0<0){ps[i]='C';score[0][i]=0.0;score[1][i]=0.0;score[2][i]=0.0;continue;}
            double[]s=new double[3];
            for(int st=0;st<3;st++){
                double acc=model.logPrior[st];
                if(method.equals("gor4")){
                    for(int w=0;w<WINDOW;w++){int j=i+w-CENTER;if(j<0||j>=n)continue;int a=AA_ORDER.indexOf(seq.charAt(j));if(a<0)continue;acc+=model.logP3[a0][st][w][a]-model.logPbg[a];}
                    for(int r=-CENTER;r<=CENTER;r++){if(r==0)continue;int j1=i+r;if(j1<0||j1>=n)continue;int a1=AA_ORDER.indexOf(seq.charAt(j1));if(a1<0)continue;int offIdx=r+CENTER;for(int wOff=r+1;wOff<=CENTER;wOff++){if(wOff==0)continue;int j2=i+wOff;if(j2<0||j2>=n)continue;int a2=AA_ORDER.indexOf(seq.charAt(j2));if(a2<0)continue;int w2=wOff+CENTER;acc+=model.logP4[st][a0][a1][offIdx][a2][w2]-model.logPpair_bg_center[a0][a1][offIdx][a2][w2];}}
                } else {
                    for(int w=0;w<WINDOW;w++){int j=i+w-CENTER;if(j<0||j>=n)continue;int a=AA_ORDER.indexOf(seq.charAt(j));if(a<0)continue;if(method.equals("gor3"))acc+=model.logP3[a0][st][w][a]-model.logPbg[a];else acc+=model.logPpos[st][w][a]-model.logPbg[a];}
                }
                s[st]=acc;
            }
            int best=argmax(s);ps[i]=SS_ORDER.charAt(best);for(int st=0;st<3;st++)score[st][i]=s[st];
        }
        if(wantProb){
            double[][]prob=new double[3][n];
            for(int i=0;i<n;i++){double h=score[0][i],e=score[1][i],c=score[2][i],m=Math.max(h,Math.max(e,c));double eh=Math.exp(h-m),ee=Math.exp(e-m),ec=Math.exp(c-m),z=eh+ee+ec;prob[0][i]=eh/z;prob[1][i]=ee/z;prob[2][i]=ec/z;}
            return new Prediction(new String(ps),prob);
        } else {
            return new Prediction(new String(ps),score);
        }
    }

    static int argmax(double[]v){int best=0;for(int i=1;i<v.length;i++)if(v[i]>v[best])best=i;return best;}

    // MODIFIED: probabilities now actually output; ref structure comparison added
    static void writeTxt(PrintStream out, String id, String seq, Prediction p,
                         boolean prob, String ref) {
        out.println("> " + id);
        out.println("AS " + seq);
        out.println("PS " + p.ps);

        // Probability lines: convert 0.0-1.0 to 0-9 integer scale
        if (prob) {
            out.println("PH " + probs2str(p.scores[2]));  // H=index2
            out.println("PE " + probs2str(p.scores[0]));  // E=index0 (CEH order: C=0,E=1,H=2)
            out.println("PC " + probs2str(p.scores[1]));  // C=index1
        }

        // Reference structure comparison
        if (ref != null && !ref.isEmpty()) {
            out.println("RS " + ref);
            out.println("MT " + matchLine(p.ps, ref));
        }
        out.println();
    }

    // NEW: convert probability array to 0-9 digit string
    static String probs2str(double[] probs) {
        StringBuilder sb = new StringBuilder(probs.length);
        for (double v : probs) {
            int d = (int) Math.round(v * 9);
            if (d < 0) d = 0;
            if (d > 9) d = 9;
            sb.append((char)('0' + d));
        }
        return sb.toString();
    }

    static String joinDoubles(double[]arr){StringBuilder sb=new StringBuilder();for(int i=0;i<arr.length;i++){if(i>0)sb.append(' ');sb.append(String.format(Locale.US,"%.3f",arr[i]));}return sb.toString();}

    static void writeHTML(PrintStream out,List<FastaEntry> entries,GorModel model,boolean prob){
        out.println("<html><body><h2>GOR Prediction</h2><p>Method:"+(model.method==null?"":model.method)+"</p>");
        for(FastaEntry e:entries){Prediction p=predictOne(e.seq,model,prob);out.println("<h3>"+escape(e.id)+"</h3><pre>> "+escape(e.id)+"\nAS "+escape(e.seq)+"\nPS "+escape(p.ps)+"\n</pre>");}
        out.println("</body></html>");
    }

    static class MafEntry {
        String id, as, queryAligned; List<String> alignedSeqs;
        MafEntry(String id,String as,String qa,List<String> al){this.id=id;this.as=as;this.queryAligned=qa;this.alignedSeqs=al;}
    }

    static MafEntry readMafFastaAlignment(File file) throws IOException {
        try(BufferedReader br=new BufferedReader(new FileReader(file))){
            String line;String id=null,as=null;List<String>alignedSeqs=new ArrayList<>();
            while((line=br.readLine())!=null){line=line.trim();if(line.isEmpty())continue;if(line.startsWith(">")){id=line.substring(1).trim();int sp=id.indexOf(' ');if(sp>=0)id=id.substring(0,sp);continue;}if(line.startsWith("AS ")){as=line.substring(3).trim().toUpperCase();continue;}if(line.startsWith("SS "))continue;String[]tok=line.split("\\s+",2);if(tok.length>=2&&tok[0].matches("\\d+")){String seq=keepAAorGap(tok[1].trim());if(!seq.isEmpty())alignedSeqs.add(seq);}}
            if(id==null)id=file.getName();if(as==null)return null;if(alignedSeqs.isEmpty())alignedSeqs.add(as);
            int L=as.length();List<String>cleaned=new ArrayList<>();for(String s:alignedSeqs)if(s.length()==L)cleaned.add(s);if(cleaned.isEmpty())cleaned=alignedSeqs;
            return new MafEntry(id,as,null,cleaned);
        }
    }

    static Prediction predictGor5FromQueryAligned(String queryAligned,List<String>alignedSeqs,GorModel model){
        int L=queryAligned.length();double[][]colSum=new double[3][L];int[]colCount=new int[L];
        for(String aligned:alignedSeqs){if(aligned.length()!=L)continue;String ungapped=keepAAOnly(aligned);if(ungapped.isEmpty())continue;Prediction p=predictOne(ungapped,model,true);double[][]prob=p.scores;int pos=0;for(int col=0;col<L;col++){char ch=aligned.charAt(col);if(!isAA(ch))continue;if(pos>=ungapped.length())break;for(int st=0;st<3;st++)colSum[st][col]+=prob[st][pos];colCount[col]++;pos++;}}
        Prediction queryPred=predictOne(queryAligned,model,true);double[][]queryProb=queryPred.scores;for(int col=0;col<L;col++){for(int st=0;st<3;st++)colSum[st][col]+=queryProb[st][col];colCount[col]++;}
        char[]colPred=new char[L];for(int col=0;col<L;col++){int best=0;if(colSum[1][col]>colSum[best][col])best=1;if(colSum[2][col]>colSum[best][col])best=2;colPred[col]=SS_ORDER.charAt(best);}
        // Build output PS (ungapped) and normalized avg probs for each output position
        StringBuilder ps=new StringBuilder();
        List<double[]> probList=new ArrayList<>();
        for(int col=0;col<L;col++){
            char qc=queryAligned.charAt(col);
            if(!isGap(qc)){
                ps.append(colPred[col]);
                int cnt=Math.max(1,colCount[col]);
                probList.add(new double[]{colSum[0][col]/cnt, colSum[1][col]/cnt, colSum[2][col]/cnt});
            }
        }
        int outLen=ps.length();
        double[][]outProbs=new double[3][outLen];
        for(int i=0;i<outLen;i++){outProbs[0][i]=probList.get(i)[0];outProbs[1][i]=probList.get(i)[1];outProbs[2][i]=probList.get(i)[2];}
        return new Prediction(ps.toString(), outProbs);
    }

    static String escape(String s){return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;");}
}

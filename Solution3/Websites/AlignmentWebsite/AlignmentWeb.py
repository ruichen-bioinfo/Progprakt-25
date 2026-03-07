<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bioinformatics Group 11</title>
    <style>
        /* Global Styles */
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f7f6;
            color: #333;
            margin: 0;
            padding: 0;
            line-height: 1.6;
        }

        /* Header */
        header {
            background-color: #2c3e50;
            color: #ecf0f1;
            padding: 2rem 0;
            text-align: center;
        }
        header h1 { margin: 0; font-size: 2.5rem; }
        header h2 { margin: 10px 0 0; font-weight: 300; color: #bdc3c7; }

        /* Container */
        .container {
            max-width: 1000px;
            margin: 20px auto;
            padding: 0 20px;
        }

        /* Team Section */
        .info-box {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .info-box h3 { border-bottom: 2px solid #3498db; padding-bottom: 10px; color: #2980b9; }

        /* Tools Grid */
        .tools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .tool-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            border-left: 5px solid #27ae60;
        }
        .tool-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.15);
        }
        .tool-card h4 { margin-top: 0; color: #2c3e50; }
        .tool-card p { font-size: 0.9rem; color: #666; }
        .btn {
            display: inline-block;
            background: #3498db;
            color: white;
            padding: 8px 15px;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 10px;
            font-weight: bold;
        }
        .btn:hover { background: #2980b9; }
        .btn-disabled {
            background: #bdc3c7;
            cursor: not-allowed;
            pointer-events: none;
        }

        /* Git Cheat Sheet */
        .code-block {
            background: #2d3436;
            color: #dfe6e9;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9rem;
        }
        .code-block ul { list-style: none; padding: 0; }
        .code-block li { margin-bottom: 8px; border-bottom: 1px solid #444; padding-bottom: 4px; }
        .cmd { color: #55efc4; font-weight: bold; }

        footer {
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
            font-size: 0.8rem;
        }
    </style>
</head>
<body>

    <header>
        <h1>Programming Practice WS25/26</h1>
        <h2>Group 11 Portal</h2>
    </header>

    <div class="container">

        <!-- Team Info -->
        <div class="info-box">
            <h3>Team Information</h3>
            <p><strong>Members:</strong> Chen Rui, Johannes, Luka, Xiuqi</p>
            <p><strong>Supervisors:</strong> Prof. Dr. Caroline Friedel, Leonard Saalfrank</p>
        </div>

        <!-- Bio-Tools Dashboard -->
        <h3 style="color: #2c3e50;">Bioinformatics Tools</h3>
        <div class="tools-grid">

            <!-- Task 5 -->
            <div class="tool-card">
                <h4>Task 5: SwissProt Search</h4>
                <p>Retrieve full FASTA sequences using SwissProt Accession Numbers.</p>
                <a href="task5.html" class="btn">Launch Tool</a>
            </div>

            <!-- Task 6 -->
            <div class="tool-card">
                <h4>Task 6: Keyword Search</h4>
                <p>Search the SwissProt database for entries matching specific keywords.</p>
                <a href="task6.html" class="btn">Launch Tool</a>
            </div>

            <!-- Task 7 -->
            <div class="tool-card">
                <h4>Task 7: Prosite Scanner</h4>
                <p>Scan sequences for Prosite patterns (manual or ID-based).</p>
                <a href="task7.html" class="btn">Launch Tool</a>
            </div>

            <!-- Task 8 -->
            <div class="tool-card" >
                <h4>Task 8: Genome Report</h4>
                <p>Search bacterial genome reports using regular expressions.</p>
                <a href="task8.html" class="btn">Launch Tool</a>
            </div>

            <!-- Task 10 -->
            <div class="tool-card">
                <h4>Task 10: DNA to Protein</h4>
                <p>Full workflow: Extract ORF -> Transcribe -> Translate.</p>
                <a href="task10.html" class="btn">Launch Tool</a>            </div>

            <!-- GOR Secondary Structure -->
            <div class="tool-card" style="border-left-color: #8e44ad;">
                <h4>GOR: Secondary Structure Prediction</h4>
                <p>Train GOR I/III/IV models, predict H/E/C secondary structure,
                   validate with Q3 &amp; SOV scores, and run 5-fold cross-validation.</p>
                <a href="gor.html" class="btn" style="background:#8e44ad;">Launch Tool</a>
            </div>
        </div>

        <!-- Git Guide -->
        <div class="info-box">
            <h3>Git Cheat Sheet</h3>
            <div class="code-block">
                <ul>
                    <li><span class="cmd">git clone &lt;url&gt;</span> - Download repository</li>
                    <li><span class="cmd">git status</span> - Check file status</li>
                    <li><span class="cmd">git add .</span> - Stage all changes</li>
                    <li><span class="cmd">git commit -m "msg"</span> - Save snapshot</li>
                    <li><span class="cmd">git pull</span> - Update from server</li>
                    <li><span class="cmd">git push</span> - Upload to server</li>
                </ul>
            </div>
        </div>

    </div>

    <footer>
        &copy; 2026 Group 11 - LMU Munich | Practical Course Bioinformatics
    </footer>

</body>
</html>

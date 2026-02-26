#!/usr/bin/env python3
import mysql.connector
from db_config import DB_CONFIG

def create_tables():

    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()
    except mysql.connector.Error as err:
        print(f"Connection failed: {err}")
        return

    # 1.Table 1 sequences with length and description Protein Function
    table_sequences = """
    CREATE TABLE IF NOT EXISTS sequences (
        id INT AUTO_INCREMENT PRIMARY KEY,
        accession VARCHAR(50) NOT NULL,
        source VARCHAR(20) NOT NULL,
        organism VARCHAR(255),
        sequence LONGTEXT NOT NULL,
        length INT,
        description TEXT,
        UNIQUE KEY unique_seq (accession, source)
    ) ;
    """

    # 2. Table2 keywords
    table_keywords = """
    CREATE TABLE IF NOT EXISTS keywords (
        id INT AUTO_INCREMENT PRIMARY KEY,
        keyword VARCHAR(255) UNIQUE NOT NULL
    ) ;
    """

    # 3. references table as relation build by 2 main tables
    table_seq_keywords = """
    CREATE TABLE IF NOT EXISTS seq_keywords (
        seq_id INT,
        kw_id INT,
        FOREIGN KEY (seq_id) REFERENCES sequences(id) ON DELETE CASCADE,
        FOREIGN KEY (kw_id) REFERENCES keywords(id) ON DELETE CASCADE,
        PRIMARY KEY (seq_id, kw_id)
    ) ;
    """

    # CONSTRUCTION
    tables = {
        'sequences': table_sequences,
        'keywords': table_keywords,
        'seq_keywords': table_seq_keywords
    }

    for name, ddl in tables.items():
        try:
            print(f"Creating table {name}: ", end='')
            cursor.execute(ddl)
            print("OK")
        except mysql.connector.Error as err:
            print(f"Error: {err.msg}")

    cursor.close()
    cnx.close()

if __name__ == "__main__":
    create_tables()

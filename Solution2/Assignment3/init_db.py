#!/usr/bin/env python3
import mysql.connector
from db_config import DB_CONFIG

def init_database():
    print("Connecting to database...")
    try:
        cnx = mysql.connector.connect(**DB_CONFIG)
        cursor = cnx.cursor()
        print("Connected.")
    except mysql.connector.Error as err:
        print(f"Connection failed: {err}")
        return

    # def in query
    queries = [
        """
        CREATE TABLE IF NOT EXISTS sequences (
            id INT AUTO_INCREMENT PRIMARY KEY,
            accession VARCHAR(50) NOT NULL,
            source VARCHAR(20) NOT NULL,
            seq_type ENUM('protein', 'dna', 'rna') NOT NULL DEFAULT 'protein',
            organism VARCHAR(255),
            sequence LONGTEXT NOT NULL,
            length INT,
            description TEXT,
            gene_name VARCHAR(100),
            UNIQUE KEY unique_seq (accession, source, seq_type)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS keywords (
            id INT AUTO_INCREMENT PRIMARY KEY,
            keyword VARCHAR(255) UNIQUE NOT NULL
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS seq_keywords (
            seq_id INT NOT NULL,
            kw_id INT NOT NULL,
            PRIMARY KEY (seq_id, kw_id),
            INDEX idx_seq (seq_id),
            INDEX idx_kw (kw_id)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS features (
            id INT AUTO_INCREMENT PRIMARY KEY,
            seq_id INT NOT NULL,
            feature_type VARCHAR(20) NOT NULL,
            start INT NOT NULL,
            end INT NOT NULL,
            strand CHAR(1) NOT NULL,
            name VARCHAR(100),
            gene_id VARCHAR(50),
            transcript_id VARCHAR(50),
            protein_seq_id INT,
            parent_id INT,
            INDEX idx_seq (seq_id),
            INDEX idx_protein (protein_seq_id),
            INDEX idx_parent (parent_id),
            INDEX idx_type (feature_type)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS alignment (
            id INT AUTO_INCREMENT PRIMARY KEY,
            family_name VARCHAR(100) NOT NULL,
            family_description TEXT,
            seq_id INT NOT NULL,
            aligned_sequence TEXT NOT NULL,
            start_in_seq INT,
            end_in_seq INT,
            chain_id VARCHAR(2),
            secondary_structure LONGTEXT,
            UNIQUE KEY unique_member (family_name, seq_id, chain_id),
            INDEX idx_seq (seq_id),
            INDEX idx_family (family_name)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS pdb_entry (
            id INT AUTO_INCREMENT PRIMARY KEY,
            pdb_id VARCHAR(4) UNIQUE NOT NULL,
            title TEXT,
            method VARCHAR(50),
            resolution FLOAT,
            deposition_date DATE
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
        """,
        """
        CREATE TABLE IF NOT EXISTS pdb_chain (
            id INT AUTO_INCREMENT PRIMARY KEY,
            pdb_id VARCHAR(4) NOT NULL,
            chain_id VARCHAR(2) NOT NULL,
            seq_id INT NOT NULL,
            UNIQUE KEY unique_pdb_chain (pdb_id, chain_id),
            INDEX idx_seq (seq_id)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4
        """
    ]


    print("Creating tables...")
    for i, q in enumerate(queries, 1):
        try:
            print(f"Creating table {i}/{len(queries)} ... ", end="", flush=True)
            cursor.execute(q)
            print("OK")
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    cursor.close()
    cnx.close()
    print("Done.")

if __name__ == "__main__":
    init_database()

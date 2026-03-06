#!/usr/bin/env python3
# All cgi file use the same config
import os

HOME        = os.path.expanduser("~")                          # /home/chenru
PUBLIC_HTML = os.path.join(HOME, "public_html")                # ~/public_html
GOR_FILES   = os.path.join(PUBLIC_HTML, "GORFiles")            # ~/public_html/GORFiles

# Jar File path and names
JARS_DIR     = os.path.join(GOR_FILES, "jars")
TRAIN_JAR    = os.path.join(JARS_DIR, "train.jar")
PREDICT_JAR  = os.path.join(JARS_DIR, "predict.jar")
VALIDATE_JAR = os.path.join(JARS_DIR, "validateGor.jar")

# Model dictionary
MODELS_DIR = os.path.join(GOR_FILES, "models")

# Pre-trained model we can use directly as for example
PRESET_MODELS = {
    "cb513_gor1": os.path.join(MODELS_DIR, "cb513_gor1.mod"),
    "cb513_gor3": os.path.join(MODELS_DIR, "cb513_gor3.mod"),
    "cb513_gor4": os.path.join(MODELS_DIR, "cb513_gor4.mod"),
}

# db
CB513_DB = "/mnt/extstud/praktikum/bioprakt/Data/GOR/CB513/CB513DSSP.db"

PRESET_DBS = {
    "cb513": CB513_DB,
}

# java use
JAVA     = "/usr/bin/java"
JAVA_MEM = ["-Xmx3000M", "-Xms500M"]
TIMEOUT  = 400  # sec

# RAM dictionary, we drop it after execution done
TMP_DIR = os.path.join(PUBLIC_HTML, "uploads")
os.makedirs(TMP_DIR, exist_ok=True)

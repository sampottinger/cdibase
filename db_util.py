import csv
import os
import sqlite3

import yaml

import file_util
import models


class ConnectionManager:
    instance = None

    @classmethod
    def get_instance(cls):
        if cls.instance == None:
            cls.instance = ConnectionManager()
        return cls.instance

    def __init__(self):
        self.__conn = sqlite3.connect('./db/daxlab.db')
    
    def get_connection(self):
        return self.__conn

def get_db_connection():
    return ConnectionManager.get_instance().get_connection()

def save_mcdi_model(newMetadataModel):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO mcdi_formats VALUES (?, ?, ?)",
        (
            newMetadataModel.safe_name,
            newMetadataModel.human_name,
            newMetadataModel.filename
        )
    )
    connection.commit()

def delete_mcdi_model(metadataModel):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM mcdi_formats WHERE safe_name=?",
        (metadataModel.safe_name,)
    )
    connection.commit()

def load_mcdi_model_listing():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT human_name,safe_name,filename FROM mcdi_formats"
    )
    return map(lambda x: models.MCDIFormatMetadata(x[0], x[1], x[2]), cursor)

def load_mcdi_model(name):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT human_name,safe_name,filename FROM mcdi_formats WHERE safe_name=?",
        (name,)
    )
    metadata = cursor.fetchone()

    if metadata == None:
        return None

    filename = metadata[2]
    filename = os.path.join(file_util.UPLOAD_FOLDER, filename)
    with open(filename) as f:
        content = f.read()
    spec = yaml.load(content)

    return models.MCDIFormat(metadata[0], metadata[1], metadata[2], spec)

def save_presentation_model(newMetadataModel):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO presentation_formats VALUES (?, ?, ?)",
        (
            newMetadataModel.safe_name,
            newMetadataModel.human_name,
            newMetadataModel.filename
        )
    )
    connection.commit()

def delete_presentation_model(metadataModel):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM presentation_formats WHERE safe_name=?",
        (metadataModel.safe_name,)
    )
    connection.commit()

def load_presentation_model_listing():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT human_name,safe_name,filename FROM presentation_formats"
    )
    return map(lambda x: models.PresentationFormatMetadata(x[0], x[1], x[2]), cursor)

def load_presentation_model(name):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT human_name,safe_name,filename FROM presentation_formats WHERE safe_name=?",
        (name,)
    )
    metadata = cursor.fetchone()

    if metadata == None:
        return None

    filename = metadata[2]
    filename = os.path.join(file_util.UPLOAD_FOLDER, filename)
    with open(filename) as f:
        content = f.read()
    spec = yaml.load(content)

    return models.PresentationFormat(metadata[0], metadata[1], metadata[2], spec)

def save_percentile_model(newMetadataModel):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO percentile_tables VALUES (?, ?, ?)",
        (
            newMetadataModel.safe_name,
            newMetadataModel.human_name,
            newMetadataModel.filename
        )
    )
    connection.commit()

def delete_percentile_model(metadataModel):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM percentile_tables WHERE safe_name=?",
        (metadataModel.safe_name,)
    )
    connection.commit()

def load_percentile_model_listing():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT human_name,safe_name,filename FROM percentile_tables"
    )
    return map(lambda x: models.PercentileTableMetadata(x[0], x[1], x[2]), cursor)

def load_percentile_model(name):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT human_name,safe_name,filename FROM percentile_tables WHERE safe_name=?",
        (name,)
    )
    metadata = cursor.fetchone()

    if metadata == None:
        return None

    filename = metadata[2]
    filename = os.path.join(file_util.UPLOAD_FOLDER, filename)
    with open(filename) as f:
        spec = list(csv.reader(f))

    return models.PercentileTable(metadata[0], metadata[1], metadata[2], spec)
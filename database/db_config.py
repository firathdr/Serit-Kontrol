import json
import mysql.connector
import os
import pymysql

config_path = os.path.join(os.path.dirname(__file__), "mysql.json")

def get_connection():
    with open(config_path) as f:
        config = json.load(f)

    conn = pymysql.connect(
        host=config['host'],
        user=config['user'],
        password=config['password'],
        database=config['database']
    )
    return conn

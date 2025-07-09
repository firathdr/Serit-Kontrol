import json
import mysql.connector
import os
config_path = os.path.join(os.path.dirname(__file__), "mysql.json")
def get_connection():
    with open(config_path) as f:
        config = json.load(f)

    connection = mysql.connector.connect(
        host=config['host'],
        user=config['user'],
        password=config['password'],
        database=config['database']
    )
    print("MySQL connection established")
    return connection

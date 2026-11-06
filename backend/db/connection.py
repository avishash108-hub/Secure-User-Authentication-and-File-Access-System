import os
import psycopg

def get_db():
    con = psycopg.connect(os.environ["DB_URL"])
    return con
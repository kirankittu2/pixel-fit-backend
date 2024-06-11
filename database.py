import mysql.connector

def connect_to_mysql():
    conn = mysql.connector.connect(
        host="localhost",
        user="Kittu",
        password="Kiran@2001",
        database="imagedb"
    )
    cursor = conn.cursor(dictionary=True)
    return conn, cursor



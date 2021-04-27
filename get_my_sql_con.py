import mysql.connector
from mysql.connector import Error


def get_connection():
    try:
        connection = mysql.connector.connect(host="localhost",
                                     user="itda",
                                     password="28031994",
                                     database="aristodb")

        return connection
    except Error as e:
        print("error occurd")
        print(e)
        return


if __name__ == '__main__':
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("select * from tasks")
    print(cursor.fetchall())

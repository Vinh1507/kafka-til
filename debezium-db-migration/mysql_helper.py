import mysql.connector
from dotenv import load_dotenv
import os
import time
load_dotenv()


# Thiết lập thông tin kết nối
s1_config = {
    'user': os.getenv('DB_S1_USERNAME'),        
    'password': os.getenv('DB_S1_PASSWORD'),    
    'host': os.getenv('MYSQL_DB_HOST'),       
    # 'database': None,
    'port': os.getenv('MYSQL_DB_PORT', 3306)
}
print(s1_config)
s1_connection = None
s1_cursor = None


def get_s1_connection_and_cursor(reopen=False, max_retries=5, retry_delay=2):
    attempts = 0
    while attempts < max_retries:
        try:
            global s1_connection, s1_cursor
            # Nếu đã có kết nối, trả về kết nối và cursor hiện tại
            if s1_connection and not reopen:
                return s1_connection, s1_cursor
            
            # Thử kết nối MySQL
            s1_connection = mysql.connector.connect(**s1_config)
            s1_cursor = s1_connection.cursor()
            return s1_connection, s1_cursor
        except mysql.connector.Error as err:
            print(f"Đã xảy ra lỗi: {err}, thử lại lần {attempts + 1} trong {retry_delay} giây...")
            attempts += 1
            time.sleep(retry_delay)
    
    # Nếu thử hết số lần mà vẫn không kết nối được, trả về None
    print("Không thể kết nối sau nhiều lần thử.")
    return None, None


def execute(query):
    try:
        s1_connection, s1_cursor = get_s1_connection_and_cursor()
        for command in query.split(';'):
            if command.strip():
                s1_cursor.execute(command)
                s1_connection.commit()

    except Exception as e:
        print(e)
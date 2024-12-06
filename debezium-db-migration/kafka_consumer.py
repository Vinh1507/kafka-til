from confluent_kafka import Consumer, KafkaException, KafkaError
import signal
import sys
import time
import debelizum2mysql
import mysql_helper

# Kafka configuration
KAFKA_BROKER = 'localhost:9092'  # Địa chỉ Kafka broker
TOPIC_SCHEMA_HISTORY = 'dbserver1.schema.history'
TOPIC1 = 'db.test_db.test_table'  # Tên topic Kafka
TOPIC2 = 'db.test_db.tmp2'
GROUP_ID = 'debezium-group'  # ID của consumer group

# Biến để kiểm tra trạng thái chạy
running = True

def graceful_shutdown(signum, frame):
    """
    Xử lý tín hiệu shutdown (Ctrl+C hoặc kill).
    """
    global running
    print("\nGraceful shutdown initiated...")
    running = False

def print_assignment(consumer):
    """
    Hiển thị các partition mà consumer đang được gán.
    """
    partitions = consumer.assignment()
    if partitions:
        print("Currently assigned partitions:")
        for p in partitions:
            print(f" - Topic: {p.topic}, Partition: {p.partition}")
    else:
        print("No partitions assigned yet.")

def main():
    # Cấu hình consumer
    consumer_conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'group.id': GROUP_ID,
        'auto.offset.reset': 'earliest',  # Đọc từ offset đầu tiên nếu chưa có checkpoint
        'partition.assignment.strategy': 'cooperative-sticky'
    }

    # Tạo consumer
    consumer = Consumer(consumer_conf)

    # Đăng ký topic
    consumer.subscribe([TOPIC1, TOPIC2, TOPIC_SCHEMA_HISTORY])

    # Đăng ký tín hiệu shutdown (Ctrl+C)
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    print(f"Consuming messages from topic ... Press Ctrl+C to exit.")

    try:
        print_assignment(consumer)
        while running:
            # Poll messages từ Kafka
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                # Không có message, tiếp tục vòng lặp
                continue
            if msg.error():
                # Xử lý lỗi
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # Đã đọc hết phân vùng, không phải lỗi nghiêm trọng
                    print(f"End of partition reached {msg.topic()} [{msg.partition()}]")
                elif msg.error():
                    # Các lỗi nghiêm trọng khác
                    raise KafkaException(msg.error())
            else:
                # Xử lý message hợp lệ
                print(f"Received message {msg.topic()}: {msg.value().decode('utf-8')} (key: {msg.key()})s")
                try:
                    if msg.topic() == TOPIC_SCHEMA_HISTORY:
                        mysql_command = debelizum2mysql.extract_DDL(msg.value().decode('utf-8'))
                    else:
                        mysql_command = debelizum2mysql.convert_DML(msg.value().decode('utf-8'))

                    print(mysql_command)
                    if mysql_command is not None:
                        mysql_helper.execute(mysql_command)
                except Exception as e:
                    print(f"Error occurred when converting to mysql: {e}")

    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Đảm bảo dừng tiêu thụ và commit offset
        print("Closing consumer...")
        consumer.close()
        print("Consumer closed gracefully.")

if __name__ == "__main__":
    main()

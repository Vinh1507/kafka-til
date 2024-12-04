from confluent_kafka import Consumer, KafkaException, KafkaError
import signal
import sys
import time

# Kafka configuration
KAFKA_BROKER = 'localhost:9092'  # Địa chỉ Kafka broker
TOPIC = 'third_topic'  # Tên topic Kafka
GROUP_ID = 'example-group'  # ID của consumer group

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
    consumer.subscribe([TOPIC])

    # Đăng ký tín hiệu shutdown (Ctrl+C)
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    print(f"Consuming messages from topic '{TOPIC}'... Press Ctrl+C to exit.")

    try:
        while running:
            # Poll messages từ Kafka
            msg = consumer.poll(timeout=1.0)
            print_assignment(consumer)

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
                print(f"Received message: {msg.value().decode('utf-8')} (key: {msg.key()})")

    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Đảm bảo dừng tiêu thụ và commit offset
        print("Closing consumer...")
        consumer.close()
        print("Consumer closed gracefully.")

if __name__ == "__main__":
    main()

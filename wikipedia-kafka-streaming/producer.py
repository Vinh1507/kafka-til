import json
import requests
from confluent_kafka import Producer
from sseclient import SSEClient as EventSource

# Kafka Configuration
KAFKA_BROKER = 'localhost:9092'  # Kafka broker URL
TOPIC = 'stream-topic'  # Kafka topic để gửi dữ liệu
wiki = 'commonswiki'

# SSE API URL
SSE_API_URL = "https://stream.wikimedia.org/v2/stream/recentchange"

# Kafka Producer Configuration
producer_config = {
    'bootstrap.servers': KAFKA_BROKER,  # Kafka broker
    'acks': 'all',
    'linger.ms': 20,
    'batch.size': 32 * 1024, # 32 KB
    'compression.type': 'snappy',      # Kiểu nén: snappy
}

# Tạo Kafka Producer
producer = Producer(producer_config)

def delivery_report(err, msg):
    """
    Callback xử lý khi gửi thành công hoặc lỗi.
    """
    if err is not None:
        print(f"Failed to deliver message: {err}")
    else:
        print(f"Message produced: {msg.key()} => {msg.value()}")

def stream_sse_to_kafka():
    """
    Stream dữ liệu từ SSE API vào Kafka topic.
    """
    url = 'https://stream.wikimedia.org/v2/stream/recentchange'

    try:
        for event in EventSource(url, last_id=None):
            if event.event == 'message':
                try:
                    change = json.loads(event.data)
                except ValueError as e:
                    print(e)
                    pass
                else:
                    # discard canary events
                    if change['meta']['domain'] == 'canary':
                        continue            
                    if change['wiki'] == wiki:
                        message = ('{user} edited {title}'.format(**change))
                        print(message)
                        # Produce the message to Kafka
                        producer.produce(
                            TOPIC,
                            key=str('test_stream_key'),  # Optional: specify a key
                            value=json.dumps(message),
                            callback=delivery_report
                        )
    except KeyboardInterrupt:
        print("\nStopping producer...")
    finally:
        # Đóng producer an toàn
        producer.flush()
        print("Producer closed.")

if __name__ == "__main__":
    stream_sse_to_kafka()

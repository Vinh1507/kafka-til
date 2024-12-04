from confluent_kafka import Producer
import json
import time

# Kafka configuration
KAFKA_BROKER = 'localhost:9092'  # Replace with your Kafka broker
TOPIC = 'third_topic'  # Replace with your Kafka topic

def delivery_report(err, msg):
    """
    Callback for delivery reports.
    Called once for each message produced to indicate delivery result.
    """
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

def main():
    # Create producer configuration
    producer_conf = {
        'bootstrap.servers': KAFKA_BROKER,
        'linger.ms': 100,  # Batch messages for up to 100ms before sending
        'acks': 'all',  # Ensure all replicas acknowledge
    }

    # Create a Kafka producer
    producer = Producer(producer_conf)

    id_counter = 0

    try:
        while True:
            # Example message payload
            message = {
                "timestamp": time.time(),
                "data": id_counter,
            }
            
            # Produce the message to Kafka
            producer.produce(
                TOPIC,
                key=str(id_counter % 10),  # Optional: specify a key
                value=json.dumps(message),
                callback=delivery_report
            )
            
            # Poll for delivery report callbacks
            producer.poll(0)

            print(f"Sent: {message}")
            id_counter += 1
            time.sleep(1)  # Wait 5 second before sending the next message

    except KeyboardInterrupt:
        print("Shutting down producer...")
    finally:
        # Wait for all messages to be delivered before closing
        producer.flush()

if __name__ == "__main__":
    main()

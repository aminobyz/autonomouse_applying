import json
import time
import uuid
import random
from datetime import datetime
from confluent_kafka import Producer
import os

# Configuration
BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
TOPIC = os.getenv('KAFKA_TOPIC', 'demo-topic')
PRODUCER_INTERVAL = int(os.getenv('PRODUCER_INTERVAL', '2'))

# Sample data generators
messages = [
    "Hello Kafka!",
    "KRaft mode is awesome!",
    "No ZooKeeper needed",
    "Streaming data is fun",
    "Kafka with Docker Compose"
]

statuses = ["INFO", "WARNING", "ERROR", "DEBUG"]
users = ["alice", "bob", "charlie", "david", "emma"]

def delivery_report(err, msg):
    """Callback for message delivery"""
    if err is not None:
        print(f"❌ Message delivery failed: {err}")
    else:
        print(f"✅ Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

def create_producer():
    """Create and configure Kafka producer"""
    conf = {
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'client.id': 'python-producer',
        'acks': 'all',  # Wait for all replicas to acknowledge
        'retries': 3,
    }
    return Producer(conf)

def generate_message():
    """Generate a random message"""
    return {
        'id': str(uuid.uuid4()),
        'timestamp': datetime.now().isoformat(),
        'message': random.choice(messages),
        'status': random.choice(statuses),
        'user': random.choice(users),
        'value': random.randint(1, 100),
        'counter': 0  # Will be updated by producer
    }

def main():
    print(f"🚀 Kafka Producer Starting...")
    print(f"   Bootstrap Servers: {BOOTSTRAP_SERVERS}")
    print(f"   Topic: {TOPIC}")
    print(f"   Interval: {PRODUCER_INTERVAL} seconds")
    print("-" * 50)
    
    producer = create_producer()
    counter = 0
    
    try:
        while True:
            counter += 1
            message_data = generate_message()
            message_data['counter'] = counter
            
            # Convert to JSON string
            message_json = json.dumps(message_data)
            
            # Produce message
            producer.produce(
                TOPIC,
                key=str(message_data['user']),
                value=message_json,
                callback=delivery_report
            )
            
            print(f"📤 Sent [{counter}]: {message_data['status']} - {message_data['message']}")
            
            # Flush to ensure message is sent
            producer.flush()
            
            time.sleep(PRODUCER_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n🛑 Producer stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        producer.flush()

if __name__ == "__main__":
    main()
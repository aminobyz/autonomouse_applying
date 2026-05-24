import json
from confluent_kafka import Consumer, KafkaError, KafkaException
import os
import signal
import sys

# Configuration
BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
TOPIC = os.getenv('KAFKA_TOPIC', 'demo-topic')
CONSUMER_GROUP = os.getenv('CONSUMER_GROUP', 'tracker-group')

# Statistics tracking
stats = {
    'total_messages': 0,
    'status_counts': {'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'DEBUG': 0},
    'user_counts': {},
    'last_10_messages': [],
    'value_sum': 0,
    'value_max': 0,
    'value_min': float('inf')
}

running = True

def signal_handler(sig, frame):
    global running
    print("\n🛑 Shutting down consumer...")
    running = False

def print_stats():
    """Print current statistics"""
    print("\n" + "="*60)
    print("📊 TRACKER STATISTICS")
    print("="*60)
    print(f"📨 Total Messages Received: {stats['total_messages']}")
    print(f"\n📈 Status Breakdown:")
    for status, count in stats['status_counts'].items():
        print(f"   {status}: {count}")
    print(f"\n👥 User Activity:")
    for user, count in sorted(stats['user_counts'].items(), key=lambda x: x[1], reverse=True):
        print(f"   {user}: {count}")
    if stats['total_messages'] > 0:
        print(f"\n📊 Value Statistics:")
        print(f"   Sum: {stats['value_sum']}")
        print(f"   Avg: {stats['value_sum'] / stats['total_messages']:.2f}")
        print(f"   Min: {stats['value_min']}")
        print(f"   Max: {stats['value_max']}")
    print(f"\n📝 Last 5 Messages:")
    for msg in stats['last_10_messages'][-5:]:
        print(f"   [{msg['counter']}] {msg['status']}: {msg['message'][:30]}...")
    print("="*60)

def process_message(message_data):
    """Process and track message statistics"""
    stats['total_messages'] += 1
    
    # Track status
    status = message_data.get('status', 'UNKNOWN')
    stats['status_counts'][status] = stats['status_counts'].get(status, 0) + 1
    
    # Track users
    user = message_data.get('user', 'unknown')
    stats['user_counts'][user] = stats['user_counts'].get(user, 0) + 1
    
    # Track values
    value = message_data.get('value', 0)
    stats['value_sum'] += value
    stats['value_max'] = max(stats['value_max'], value)
    stats['value_min'] = min(stats['value_min'], value)
    
    # Store last 10 messages
    stats['last_10_messages'].append(message_data)
    if len(stats['last_10_messages']) > 10:
        stats['last_10_messages'].pop(0)
    
    # Print every 5 messages
    if stats['total_messages'] % 5 == 0:
        print_stats()

def create_consumer():
    """Create and configure Kafka consumer"""
    conf = {
        'bootstrap.servers': BOOTSTRAP_SERVERS,
        'group.id': CONSUMER_GROUP,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': True,
        'auto.commit.interval.ms': 1000,
        'session.timeout.ms': 6000,
    }
    return Consumer(conf)

def main():
    global running
    
    # Setup signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print(f"🔍 Kafka Consumer/Tracker Starting...")
    print(f"   Bootstrap Servers: {BOOTSTRAP_SERVERS}")
    print(f"   Topic: {TOPIC}")
    print(f"   Consumer Group: {CONSUMER_GROUP}")
    print("-" * 50)
    print("Waiting for messages... Press Ctrl+C to stop\n")
    
    consumer = create_consumer()
    
    try:
        consumer.subscribe([TOPIC])
        
        while running:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
                
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    raise KafkaException(msg.error())
            
            # Process the message
            try:
                message_data = json.loads(msg.value().decode('utf-8'))
                print(f"📥 Received: [{message_data.get('counter', '?')}] {message_data.get('status', '?')} from {message_data.get('user', '?')}")
                process_message(message_data)
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"❌ Consumer error: {e}")
    finally:
        print_stats()
        consumer.close()
        print("✅ Consumer closed gracefully")

if __name__ == "__main__":
    main()
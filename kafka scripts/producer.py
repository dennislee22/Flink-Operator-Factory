from kafka import KafkaProducer
import time
import json
import random
import string

kafka_broker = 'my-cluster-kafka-bootstrap.dlee-kafkanodepool.svc.cluster.local:9092'
topic_name = 'pyflink-sink-in'

producer = KafkaProducer(
    bootstrap_servers=kafka_broker,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Function to generate a random message
def generate_random_message(length=10):
    """Generates a random string of the given length."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

count = 0
try:
    while True:
        random_message = generate_random_message(random.randint(5, 70)) 
        message = {"message": random_message}
        producer.send(topic_name, value=message)
        print(f"Sent: {message['message']}")
        count += 1

        if count % 100 == 0:
            producer.flush()
        
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Producer stopped manually.")
finally:
    # Ensure any remaining messages are sent before closing
    producer.flush()
    producer.close()

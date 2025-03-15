from kafka import KafkaConsumer
import time
import json

topic_name = 'pyflink-sink-out'
bootstrap_servers = ['my-cluster-kafka-bootstrap.dlee-kafkanodepool.svc.cluster.local:9092']
group_id = 'cgroup-2'

consumer = KafkaConsumer(topic_name, 
                         bootstrap_servers=bootstrap_servers, 
                         group_id=group_id, 
                         auto_offset_reset='earliest')

# Consume messages and update metrics
for message in consumer:
    try:
        msg_value = message.value.decode('utf-8')
        message_size = len(msg_value.encode('utf-8'))  # Size of the message in bytes
        
        print(f"Consumed message: {msg_value}, Size: {message_size} bytes")

    except Exception as e:
        print(f"Error processing message: {e}")

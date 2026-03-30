# client-agent

import pika
import json
import time
import os

def execute_local_os_command(action, target):
    """
    This is where the agent actually talks to the local Operating System.
    """
    print(f"\n[!] INCOMING COMMAND RECEIVED FROM SOAR BRAIN [!]")
    print(f"    Action: {action}")
    print(f"    Target: {target}")
    
    if action == "isolate_network":
        print(f"[*] Executing OS level isolation for {target}...")
        
        # In a real scenario, this would execute actual OS commands like:
        # os.system("netsh interface set interface 'Ethernet' admin=disable")
        # os.system(f"iptables -A INPUT -s {target} -j DROP")
        
        time.sleep(2) # Simulating the time it takes to run OS commands
        print("[+] SUCCESS: Network interface disabled. Host is isolated.")
        
    else:
        print(f"[-] Unknown action requested: {action}")

def start_listening():
    """Connects to RabbitMQ and listens for commands."""
    credentials = pika.PlainCredentials('soar_admin', 'supersecret')
    parameters = pika.ConnectionParameters('localhost', 5672, '/', credentials)
    
    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        channel.queue_declare(queue='soar_actuator_queue', durable=True)
        print(" [*] Client Agent Actuator is active.")
        print(" [*] Waiting for commands from RabbitMQ. To exit press CTRL+C")

        def callback(ch, method, properties, body):
            payload = json.loads(body)
            execute_local_os_command(payload['action'], payload['target'])
            
            # Acknowledge the message so RabbitMQ removes it from the queue
            ch.basic_ack(delivery_tag=method.delivery_tag)

        # Set up the consumer
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue='soar_actuator_queue', on_message_callback=callback)
        channel.start_consuming()

    except Exception as e:
        print(f"Connection to RabbitMQ failed: {e}")
        print("Retrying in 5 seconds...")
        time.sleep(5)
        start_listening()

if __name__ == '__main__':
    start_listening()
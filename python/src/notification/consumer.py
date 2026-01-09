import pika
import sys
import os
import logging
from send import email
import logging

def main():
    logging.info("Notification main invoked")
    MP3_QUEUE = os.environ.get("MP3_QUEUE", "mp3")

    # RabbitMQ connection (K8s-safe)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host="rabbitmq",
            heartbeat=60,
            blocked_connection_timeout=300
        )
    )
    channel = connection.channel()

    # Ensure queue exists
    channel.queue_declare(queue=MP3_QUEUE, durable=True)

    def callback(ch, method, properties, body):
        logging.info("Fetch from queue done ...")
        logging.info(f"📩 Received message:{body}")
        err = email.notification(body)
        logging.info(f"📤 Email function returned: {err}")
        if err:
            # requeue so it can be retried
            ch.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=True
            )
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    # Process one message at a time
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=MP3_QUEUE,
        on_message_callback=callback
    )

    logging.info("Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(0)

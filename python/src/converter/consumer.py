import pika
import sys
import os
import json
from pymongo import MongoClient
import gridfs
from convert import to_mp3


def main():
    # MongoDB (use service name inside K8s)
    mongo_client = MongoClient("mongodb://mongo:27017")
    db_videos = mongo_client.videos
    db_mp3s = mongo_client.mp3s

    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    # RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host="rabbitmq",
            heartbeat=60,
            blocked_connection_timeout=300
        )
    )
    channel = connection.channel()

    VIDEO_QUEUE = os.environ.get("VIDEO_QUEUE", "video")
    MP3_QUEUE = os.environ.get("MP3_QUEUE", "mp3")

    channel.queue_declare(queue=VIDEO_QUEUE, durable=True)
    channel.queue_declare(queue=MP3_QUEUE, durable=True)

    def callback(ch, method, properties, body):
        err = to_mp3.start(body, fs_videos, fs_mp3s, ch)
        if err:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue=VIDEO_QUEUE,
        on_message_callback=callback
    )

    print("Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(0)

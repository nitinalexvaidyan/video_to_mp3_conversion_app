import pika, json, sys
import logging

def upload(f, fs, access):
    try:
        fid = fs.put(f)
    except Exception as err:
        logging.error(err)
        return "internal server error util.py L9", 500

    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "username": access["username"]
    }

    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host="rabbitmq",
                heartbeat=60,
                blocked_connection_timeout=300
            )
        )
        channel = connection.channel()

        channel.queue_declare(queue="video", durable=True)

        channel.basic_publish(
            exchange="",
            routing_key="video",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            )
        )

        connection.close()

    except Exception as err:
        logging.error(err)
        fs.delete(fid)
        return "internal server error util.py L43", 500
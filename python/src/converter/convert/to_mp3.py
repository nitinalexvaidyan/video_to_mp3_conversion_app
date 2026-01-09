import json
import tempfile
import os
import pika
from bson.objectid import ObjectId
from moviepy.editor import VideoFileClip


def start(message, fs_videos, fs_mp3s, channel):
    try:
        message = json.loads(message)

        # Get video from GridFS
        video_file = fs_videos.get(ObjectId(message["video_fid"]))

        # Create temp video file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tf:
            tf.write(video_file.read())
            temp_video_path = tf.name

        # Extract audio
        clip = VideoFileClip(temp_video_path)
        audio = clip.audio

        temp_mp3_path = tempfile.gettempdir() + f"/{message['video_fid']}.mp3"
        audio.write_audiofile(temp_mp3_path)

        clip.close()
        os.remove(temp_video_path)

        # Save MP3 to GridFS
        with open(temp_mp3_path, "rb") as f:
            mp3_fid = fs_mp3s.put(f)

        os.remove(temp_mp3_path)

        message["mp3_fid"] = str(mp3_fid)

        # Publish to next queue
        channel.basic_publish(
            exchange="",
            routing_key=os.environ.get("MP3_QUEUE", "mp3"),
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            )
        )

        return None

    except Exception as err:
        print("Conversion failed:", err)
        return "conversion failed"

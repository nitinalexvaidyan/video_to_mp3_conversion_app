import os, gridfs, pika, json
from flask import Flask, request, send_file
from flask_pymongo import PyMongo
from auth import validate
from auth_svc import access
from storage import util
from bson.objectid import ObjectId
import logging

logging.info("gateway server starting ...")
server = Flask(__name__)
mongo_video = PyMongo(server, uri=os.environ["MONGO_VIDEO_URI"] )
mongo_mp3 = PyMongo(server, uri=os.environ["MONGO_MP3_URI"] )
fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)


@server.route("/healthcheck", methods=["GET"])
def healthcheck():
    logging.info("gateway healthcheck invoked ...")
    return "Server is up and running", 200

@server.route("/login", methods=["POST"])
def login():
    logging.info("gateway login invoked ...")
    token, err = access.login(request)
    logging.info("Acess is valid server.py L25")
    if not err:
        return token
    else:
        return err[0], err[1]


@server.route("/upload", methods=['POST'])
def upload():
    logging.info("gateway upload invoked ...")
    access, err = validate.token(request)
    access = json.loads(access)
    if access["admin"]:
        print("Acess is valid server.py L25")
        if len(request.files) != 1:
            return "excatly 1 file required server.py L37", 400
        
        for _, f in request.files.items():
            err = util.upload(f, fs_videos, access)
            if err:
                return err
        return "success", 200
    else:
        return "not authorized server.py L45", 401


@server.route("/download", methods=["GET"])
def download():
    logging.info("gateway download invoked ...")
    access, err = validate.token(request)
    if err:
        return err
    
    access = json.loads(access)
    if access["admin"]:
        fid_string = request.args.get("fid")

        if not fid_string:
            return "fid is required", 400

        try:
            out = fs_mp3s.get(ObjectId(fid_string))
            return send_file(out, download_name=f"{fid_string}.mp3")
        except Exception as err:
            logging.info(err)
            return "internal server error", 500
    return "not authorized", 401


if __name__=="__main__":
    try:
        server.run(host="0.0.0.0", port=8080)
        logging.info("Gatway server deployed !!! ...")
    except Exception as e:
        logging.info("Gatway server failed to start !!!")
        logging.info(e)
    

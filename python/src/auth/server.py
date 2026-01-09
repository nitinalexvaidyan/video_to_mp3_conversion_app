import jwt, datetime, os
from flask import Flask, request
from flask_mysqldb import MySQL
import logging

logging.info("Auth server starting ...")

server = Flask(__name__)
mysql = MySQL(server)

# config
server.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
server.config["MYSQL_USER"] = os.environ.get("MYSQL_USER")
server.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD")
server.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")
server.config["MYSQL_PORT"] = int(os.environ.get("MYSQL_PORT"))
print(server.config["MYSQL_PORT"])

@server.route("/healthcheck", methods=["GET"])
def healthcheck():
    logging.info("auth healthcheck invoked ...")
    return "Server is up and running", 200

@server.route("/login", methods=["POST"])
def login():
    logging.info("auth login invoked ...")
    auth = request.authorization
    if not auth:
        return "missing credentials", 401
    
    # Check db for username and password
    cur = mysql.connection.cursor()
    res = cur.execute(
        "SELECT email, password FROM users WHERE email= %s", (auth.username,)
    )
    if res>0:
        user_row = cur.fetchone()
        email = user_row[0]
        password = user_row[1]

        if auth.username != email or auth.password != password:
            return "Invalid credentials", 401
        else:
            return createJWT(auth.username, os.environ.get("JWT_SECRET"), True)
    else:
        return "Invalid credentials", 401



def createJWT(username, secret, auth):
    logging.info("gateway createJWT invoked ...")
    return jwt.encode({
        "username": username,
        "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1),
        "iat": datetime.datetime.now(tz=datetime.timezone.utc),
        "admin": auth
    },
    secret,
    algorithm="HS256")     



@server.route("/validate", methods=["POST"])
def validate():
    logging.info("auth validate invoked ...")
    encoded_jwt = request.headers["Authorization"]
    if not encoded_jwt:
        return "Missing credentials", 401
    
    bearer_token = encoded_jwt.split(" ")[1]
    try:
        decoded_jwt = jwt.decode(
            bearer_token,
            os.environ.get("JWT_SECRET"),
            algorithms=["HS256"]
        )
    except Exception as err:
        print(err)
        return "Not authorized", 403
    
    return decoded_jwt, 200


if __name__=="__main__":
    try:
        server.run(host="0.0.0.0", port=5000)
        logging.info("Auth server deployed !!! ...")
    except Exception as e:
        logging.info("Auth server failed to start !!!")
        logging.info(e)
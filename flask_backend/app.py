from flask import Flask, jsonify, request, send_file
import psycopg
from argon2 import PasswordHasher
import uuid
import jwt
from datetime import datetime, timedelta, timezone
import os
from jwt.exceptions import InvalidTokenError
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[]
)
def get_db():
    con = psycopg.connect(
      dbname = "att",
      user = "postgres",
      password = "avi",
      host = "localhost",
      port = "5432"
    )
    return con
ph = PasswordHasher(time_cost = 3, memory_cost = 65536, parallelism = 4)
JWT_SECRET = os.environ.get("JWT_SECRET_KEY")
@app.route('/')
def home():
    return 'flask is running'

@app.route("/register", methods = ["POST"])
def register():
    ''' request{
  "email": "alice@example.com",
  "username": "alice",
  "password": "Password123!"
}'''
    data = request.get_json()
    for field in ["email", "username", "password"]:
        if not data.get(field):
            return jsonify({"error" : f"{field} is required"}), 400

    email = data.get("email")
    username = data.get("username")
    password = data.get("password")
    if (
        len(password) < 10 or len(password) > 128 
        or not any(c.islower() for c in password) 
        or not any(c.isupper() for c in password) 
        or not any(not c.isalnum() for c in password)
        or not any(c.isdigit() for c in password)
       
    ):
        return jsonify({
                   
                   "error": "Password must be between 10 to 128 characters and contain uppercase, lowercase, a number, and a special character."

                }), 400


    u_id = f"usr_{uuid.uuid4().hex[:12]}"
    pwd_hash = ph.hash(password)
    #storing_in_db
    full_name = ""
    #display_name = email.split('@')[0]
    bio = ""
    role = ""
    con = get_db()
    cur = con.cursor()

    cur.execute('''
             insert into users(
             u_id, 
             email, 
             password_hash, 
             full_name,
             display_name
            )
            values(%s, %s, %s, %s, %s)''',
            (u_id, email, pwd_hash, full_name, username)
            )
    con.commit()
    cur.close()
    con.close()
    return "user registered successfully", 200

@app.route("/login", methods = ["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Invalid email or password"}), 401

    con = get_db()
    cur = con.cursor()
    cur.execute(
        "SELECT u_id, password_hash FROM users WHERE email = %s",
        (email,)
    )

    user = cur.fetchone()

    if user is None:
        cur.close()
        con.close()
        return jsonify({"error": "Invalid email or password"}), 401

    u_id, stored_hash = user

    try:
        ph.verify(stored_hash, password)
    except Exception:
        cur.close()
        con.close()
        return jsonify({"error": "Invalid email or password"}), 401

    cur.close()
    con.close()

    now = datetime.now(timezone.utc)

    access_token = jwt.encode(
        {
            "u_id": u_id,
            "type": "access",
            "exp": now + timedelta(minutes=15)
        },
        JWT_SECRET,
        algorithm="HS256"
    )
    refresh_jti = str(uuid.uuid4())
    refresh_exp = now + timedelta(days=7)
    refresh_token = jwt.encode(
        {
            "u_id": u_id,
            "type": "refresh",
            "jti": refresh_jti,
            "exp": refresh_exp
        },
        JWT_SECRET,
        algorithm="HS256"
    )

    con = get_db()
    cur = con.cursor()
    cur.execute("""
    INSERT INTO refresh_sessions (jti, u_id, expires_at)
    VALUES (%s, %s, %s)""",
    (refresh_jti, u_id, refresh_exp)
    )
    con.commit()
    cur.close()
    con.close()
    

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token
    }), 200

def token_req(function):
    @wraps(function)
    def func_wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error" : "unauthorized user"}), 401

        if not auth_header.startswith("Bearer "):
            return jsonify({"error" : "invalid authorization header"}), 401

        b_token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(b_token, JWT_SECRET, algorithms = ["HS256"])

        except InvalidTokenError:
            return jsonify({"error" : "invalid or expired token"}), 401
        p_type = payload.get("type")
        if not p_type == "access":
            return jsonify({"error" : "invalid token"}), 401
        u_id = payload["u_id"]
        return function(u_id, *args, **kwargs)
    return func_wrapper


@app.route("/me", methods=["GET"])
@token_req
def me(u_id):
    con = get_db()
    cur = con.cursor()

    cur.execute("""
        SELECT full_name, display_name, bio, role
        FROM users
        WHERE u_id = %s
    """, (u_id,))

    user = cur.fetchone()

    cur.close()
    con.close()

    if user is None:
        return jsonify({"error": "user not found"}), 404

    return jsonify({
        "full_name": user[0],
        "username": user[1],
        "bio": user[2],
        "role": user[3]
    }), 200

@app.route("/files", methods=["GET"])
@token_req
def get_files(u_id):
    con = get_db()
    cur = con.cursor()

    cur.execute("""
        SELECT file_id, file_name, mime_type, size_bytes, uploadedAt
        FROM files
        WHERE u_id = %s
    """, (u_id,))

    rows = cur.fetchall()

    cur.close()
    con.close()

    files = []

    for row in rows:
        files.append({
            "file_id": row[0],
            "file_name": row[1],
            "mime_type": row[2],
            "size_bytes": row[3],
            "uploaded_at": row[4].isoformat()
        })

    return jsonify({"files": files}), 200


@app.route("/files/<file_id>", methods=["GET"])
@token_req
def get_file(u_id, file_id):
    con = get_db()
    cur = con.cursor()

    cur.execute("""
        SELECT file_name, mime_type, file_path
        FROM files
        WHERE file_id = %s AND u_id = %s
    """, (file_id, u_id))

    file = cur.fetchone()

    cur.close()
    con.close()

    if file is None:
        return jsonify({"error": "file not found or unauthorized"}), 404

    file_name, mime_type, file_path = file

    full_path = os.path.join(app.root_path, file_path)

    if not os.path.isfile(full_path):
        return jsonify({"error": "file unavailable"}), 404

    return send_file(
        full_path,
        as_attachment=True,
        download_name=file_name,
        mimetype=mime_type
    )

@app.route("/logout", methods=["POST"])
def logout():
    data = request.get_json()

    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return jsonify({"error": "refresh token required"}), 400

    try:
        payload = jwt.decode(
            refresh_token,
            JWT_SECRET,
            algorithms=["HS256"]
        )
    except InvalidTokenError:
        return jsonify({"error": "invalid refresh token"}), 401

    if payload.get("type") != "refresh":
        return jsonify({"error": "invalid token"}), 401

    jti = payload.get("jti")

    if not jti:
        return jsonify({"error": "invalid token"}), 401

    con = get_db()
    cur = con.cursor()

    cur.execute("""
        UPDATE refresh_sessions
        SET revoked = TRUE
        WHERE jti = %s
    """, (jti,))

    con.commit()

    cur.close()
    con.close()

    return jsonify({"message": "logged out successfully"}), 200


@app.route("/refresh", methods=["POST"])
def refresh():
    data = request.get_json()

    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return jsonify({"error": "refresh token required"}), 400

    try:
        payload = jwt.decode(
            refresh_token,
            JWT_SECRET,
            algorithms=["HS256"]
        )
    except InvalidTokenError:
        return jsonify({"error": "invalid or expired refresh token"}), 401

    if payload.get("type") != "refresh":
        return jsonify({"error": "invalid token"}), 401

    u_id = payload.get("u_id")
    jti = payload.get("jti")

    if not u_id or not jti:
        return jsonify({"error": "invalid token"}), 401

    con = get_db()
    cur = con.cursor()

    cur.execute("""
        SELECT revoked, expires_at
        FROM refresh_sessions
        WHERE jti = %s AND u_id = %s
    """, (jti, u_id))

    session = cur.fetchone()

    cur.close()
    con.close()

    if session is None:
        return jsonify({"error": "invalid refresh token"}), 401

    revoked, expires_at = session

    if revoked:
        return jsonify({"error": "refresh token has been revoked"}), 401

    now = datetime.now(timezone.utc)

    if expires_at <= now:
        return jsonify({"error": "refresh token expired"}), 401

    access_payload = {
        "u_id": u_id,
        "type": "access",
        "exp": now + timedelta(minutes=15)
    }

    access_token = jwt.encode(
        access_payload,
        JWT_SECRET,
        algorithm="HS256"
    )

    return jsonify({
        "access_token": access_token
    }), 200

if __name__ == '__main__':
    app.run(debug = True)
    
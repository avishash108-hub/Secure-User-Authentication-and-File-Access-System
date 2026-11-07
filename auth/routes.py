from flask import Blueprint, request, jsonify
import jwt
from jwt.exceptions import InvalidTokenError
import uuid
from datetime import datetime, timezone, timedelta
from auth.security import JWT_SECRET, ph
from extensions import limiter
from backend.db.connection import get_db
auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods = ["POST"])
def register():
    ''' request{
  "email": "alice@example.com",
  "username": "alice",
  "password": "Password123!"
}'''
    data = request.get_json()
    for field in ["email", "password"]:
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

@auth_bp.route("/login", methods = ["POST"])
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



@auth_bp.route("/logout", methods=["POST"])
def logout():
    refresh_token = request.headers.get("Authorization")

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


@auth_bp.route("/refresh", methods=["POST"])
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

from flask import Blueprint, jsonify, request
from backend.db.connection import get_db
from auth.decorators import token_req
me_bp = Blueprint("me", __name__)

@me_bp.route("/me", methods=["GET"])
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

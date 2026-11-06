from functools import wraps
from flask import request, jsonify
import jwt
from jwt.exceptions import InvalidTokenError
from auth.security import JWT_SECRET

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

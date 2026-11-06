import os
from flask import Blueprint, jsonify, request, send_file, current_app
from backend.db.connection import get_db
from auth.decorators import token_req
files_bp = Blueprint("files", __name__)

@files_bp.route("/files", methods=["GET"])
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


@files_bp.route("/files/<file_id>", methods=["GET"])
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

    full_path = os.path.join(current_app.root_path, file_path)

    if not os.path.isfile(full_path):
        return jsonify({"error": "file unavailable"}), 404

    return send_file(
        full_path,
        as_attachment=True,
        download_name=file_name,
        mimetype=mime_type
    )


@files_bp.route("/files/<file_id>/download", methods=["GET"])
@token_req
def download_file(u_id, file_id):
    con = get_db()
    cur = con.cursor()

    try:
        cur.execute("""
            SELECT file_name, mime_type, file_path
            FROM files
            WHERE file_id = %s AND u_id = %s
        """, (file_id, u_id))

        file = cur.fetchone()

    finally:
        cur.close()
        con.close()

    if file is None:
        return jsonify({"error": "file not found or unauthorized"}), 404

    file_name, mime_type, file_path = file

    full_path = os.path.join(current_app.root_path, file_path)

    if not os.path.isfile(full_path):
        return jsonify({"error": "file unavailable"}), 404

    return send_file(
        full_path,
        as_attachment=True,
        download_name=file_name,
        mimetype=mime_type
    )

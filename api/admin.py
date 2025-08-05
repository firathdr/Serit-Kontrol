from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.db_config import get_connection

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/kullanicilar', methods=['GET'])
@jwt_required()
def get_all_users():
    current_user = get_jwt_identity()
    if current_user["rol"] != "admin":
        return jsonify({"error": "Yetkisiz erişim"}), 403

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)  # dict olarak veriler döner
        cursor.execute("SELECT id, isim, username, rol FROM kullanicilar")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"users": users})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

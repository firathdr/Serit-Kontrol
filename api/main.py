from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS, cross_origin
import json
import os
import base64
import datetime
from flask import make_response, request, jsonify
from functools import wraps
import jwt
from database.db_config import get_connection
import bcrypt
import pymysql
from pymysql.cursors import DictCursor

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.config['SECRET_KEY'] = 'd4ea239a4b08d7e6e209a164ce7bf6c8'


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method == 'OPTIONS':
            return jsonify({'message': 'CORS preflight'}), 200

        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token eksik!'}), 403
        try:
            token = token.replace("Bearer ", "")
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['username']
        except Exception as e:
            return jsonify({'message': f'Token geçersiz! {str(e)}'}), 403
        return f(current_user, *args, **kwargs)
    return decorated


@app.route('/api/registr', methods=['POST'])
def register():
    data = request.get_json()
    print(data)
    isim = data['isim']
    username = data['username']
    password = data['password']
    rol="kullanici"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    conn=get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO kullanicilar (isim,username, password, rol) VALUES (%s,%s,%s,%s)', (isim,username, hashed_password, rol))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'status': 'ok'})
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM kullanicilar WHERE username = %s', (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user is None:
        return jsonify({'status': 'kullanici bulunamadi'}), 401

    if not bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
        return jsonify({'message': 'Geçersiz şifre!'}), 401

    # JWT token'ı düzgün format ile oluştur
    token = jwt.encode({
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=12),
        'name':user[1],
        'role':user[4]
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({'token': token})  # access_token yerine token döndür


@app.route('/api/araclar', methods=['GET'])
@token_required
def get_araclar(current_user):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                arac_goruntu.arac_id,
                giris_zamani,
                saat,
                serit_id,
                ihlal_durumu,
                araclar.video_name
            FROM araclar
            INNER JOIN arac_goruntu ON araclar.arac_id = arac_goruntu.arac_id
            ORDER BY video_name
        ''')

        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        data = [dict(zip(column_names, row)) for row in rows]

        return jsonify({'data': data})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        conn.close()



@app.route('/api/araclar/<string:video_name>/<int:arac_id>', methods=['GET'])
@token_required
def get_video(video_name,arac_id):

    conn=get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT giris_zamani,saat,serit_id,ihlal_durumu,araclar.video_name FROM araclar INNER JOIN arac_goruntu ON araclar.arac_id = arac_goruntu.arac_id where arac_goruntu.arac_id=%s and arac_goruntu.video_name=%s', (arac_id,video_name,))
                                                                #arac_goruntu eklencek
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({'data': data})

@app.route('/api/araclar/<string:video_name>/<int:id>', methods=['DELETE'])
@token_required
def delete_araclar(video_name,id):
    conn=get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM araclar WHERE video_name=%s and arac_id=%s', (video_name,id))
    cursor.execute('DELETE FROM arac_goruntu WHERE video_name=%s and arac_id=%s', (video_name,id))
    conn.commit()
    cursor.close()
    return jsonify({'status': 'ok'})


@app.route('/api/itiraz_kayit', methods=['GET'])
@token_required
def get_itiraz(current_user):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM itiraz_kayit WHERE username=%s', (current_user,))
    raw_data = cursor.fetchall() or []

    columns = [desc[0] for desc in cursor.description]

    data = [dict(zip(columns, row)) for row in raw_data]

    cursor.close()
    conn.close()
    print(data)
    return jsonify({'data': data})


@app.route('/api/itiraz_et', methods=["POST"])
@cross_origin(origins="http://localhost:5173", supports_credentials=True)
@token_required
def itiraz_et(current_user):
    try:
        data = request.get_json()
        username = current_user
        arac_id = data.get("arac_id")
        video_name = data.get("video_name")
        sebep = data.get("sebep")
        durum=data.get("ihlal")
        if durum:
            durum="ihlal yok"
        else:
            durum="ihlal"

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO itiraz_kayit (username, arac_id, video_name, durum, sebep) VALUES (%s, %s, %s, %s, %s)',
            (username, arac_id, video_name, durum, sebep))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

#@app.route('/api/kayit_izle/<int:arac_id>', methods=['POST'])
#def kayit_izle(arac_id):               TODO: flask video stream araştır




@app.route('/api/admin/kullanicilar', methods=['GET'])
@token_required
def get_all_users(current_user):
    conn = get_connection()
    cursor = conn.cursor(DictCursor)

    cursor.execute("SELECT rol FROM kullanicilar WHERE username = %s", (current_user,))
    result = cursor.fetchone()

    if not result or result["rol"] != 'admin':
        print("bura caliiyo")
        cursor.close()
        conn.close()
        return jsonify({'message': 'Admin yetkisi gerekli'}), 403

    cursor.execute("SELECT id, isim, username, rol FROM kullanicilar")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'kullanicilar': users}), 200

@app.route('/api/admin/yetkilendir', methods=['POST'])
@token_required
def make_user_admin(current_user):
    data = request.get_json()
    hedef_kullanici = data.get('username')

    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT rol FROM kullanicilar WHERE username = %s", (current_user,))
    result = cursor.fetchone()
    if not result or result["rol"] != "admin":
        cursor.close()
        conn.close()
        return jsonify({'message': 'Admin yetkisi gerekli'}), 403

    cursor.execute("UPDATE kullanicilar SET rol = 'admin' WHERE username = %s", (hedef_kullanici,))
    conn.commit()

    cursor.close()
    conn.close()
    return jsonify({'message': f"{hedef_kullanici} artık admin."}), 200
@app.route('/api/admin/kullanici-sil', methods=['DELETE'])
@token_required
def delete_user(current_user):
    data = request.get_json()
    hedef_kullanici = data.get('username')

    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT rol FROM kullanicilar WHERE username = %s", (current_user,))
    result = cursor.fetchone()
    if not result or result["rol"] != "admin":
        cursor.close()
        conn.close()
        return jsonify({'message': 'Admin yetkisi gerekli'}), 403

    if hedef_kullanici == current_user:
        return jsonify({'message': 'Kendi hesabınızı silemezsiniz.'}), 400

    cursor.execute("DELETE FROM kullanicilar WHERE username = %s", (hedef_kullanici,))
    conn.commit()

    cursor.close()
    conn.close()
    return jsonify({'message': f"{hedef_kullanici} silindi."}), 200

@app.route('/api/admin/ihlaller', methods=['GET'])
@token_required
def get_all_violations(current_user):
    try:
        conn = get_connection()
        cursor = conn.cursor(DictCursor)

        cursor.execute("SELECT rol FROM kullanicilar WHERE username = %s", (current_user,))
        result = cursor.fetchone()

        if not result or result['rol'] != 'admin':
            cursor.close()
            conn.close()
            return jsonify({'message': 'Admin yetkisi gerekli'}), 403

        cursor.execute('''
            SELECT 
                arac_goruntu.arac_id,
                giris_zamani,
                saat,
                serit_id,
                ihlal_durumu,
                araclar.video_name,
                kullanicilar.username
            FROM araclar
            INNER JOIN arac_goruntu ON araclar.arac_id = arac_goruntu.arac_id
            LEFT JOIN itiraz_kayit ON araclar.arac_id = itiraz_kayit.arac_id
            LEFT JOIN kullanicilar ON itiraz_kayit.username = kullanicilar.username
            ORDER BY video_name
        ''')

        rows = cursor.fetchall()
        return jsonify({'data': rows}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        conn.close()

import traceback

@app.route('/api/admin/itirazlar', methods=['GET'])
@token_required
def get_all_itirazlar(current_user):
    try:
        conn = get_connection()
        cursor = conn.cursor(DictCursor)

        cursor.execute("SELECT rol FROM kullanicilar WHERE username = %s", (current_user,))
        result = cursor.fetchone()
        if not result or result["rol"] != "admin":
            cursor.close()
            conn.close()
            return jsonify({'message': 'Admin yetkisi gerekli'}), 403

        cursor.execute('''
            SELECT 
                id,
                username,
                arac_id,
                video_name,
                durum,
                sebep
            FROM itiraz_kayit 
        ''')
        itirazlar = cursor.fetchall()

        return jsonify({'data': itirazlar}), 200

    except Exception as e:
        traceback.print_exc()  # Hatanın tam stack trace'ini verir
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        conn.close()




if __name__ == '__main__':
    app.run(debug=True)



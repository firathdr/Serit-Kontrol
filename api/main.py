from flask_cors import CORS, cross_origin
import base64
import datetime
from functools import wraps
import jwt
from database.db_config import get_connection
import bcrypt
import pymysql
from pymysql.cursors import DictCursor
import os
from flask import Flask, send_file, request, jsonify
import subprocess

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
    ANY_VALUE(giris_zamani) AS giris_zamani,
    ANY_VALUE(saat) AS saat,
    ANY_VALUE(serit_id) AS serit_id,
    ANY_VALUE(ihlal_durumu) AS ihlal_durumu,
    araclar.video_name,
    ANY_VALUE(goruntu) AS goruntu
FROM araclar
INNER JOIN arac_goruntu ON araclar.arac_id = arac_goruntu.arac_id
GROUP BY arac_goruntu.arac_id, araclar.video_name
ORDER BY araclar.video_name

        ''')

        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]

        data = []
        for row in rows:
            row_dict = dict(zip(column_names, row))

            if 'goruntu' in row_dict and row_dict['goruntu'] is not None:
                row_dict['goruntu'] = base64.b64encode(row_dict['goruntu']).decode('utf-8')
            else:
                row_dict['goruntu'] = None

            data.append(row_dict)

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

    data = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({'data': data})

@app.route('/api/araclar/<string:video_name>/<int:id>', methods=['DELETE'])
@token_required
def delete_araclar(current_user,video_name,id):
    conn=get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM araclar WHERE video_name=%s and arac_id=%s', (video_name,id))
    cursor.execute('DELETE FROM arac_goruntu WHERE video_name=%s and arac_id=%s', (video_name,id))
    cursor.execute('DELETE FROM itiraz_kayit WHERE video_name=%s and arac_id=%s', (video_name,id))

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

        cursor.execute("""
SELECT
    ik.id,
    ik.username,
    ik.arac_id,
    ik.video_name,
    ik.durum,
    ik.sebep,
    ag.giris_zamani AS arac_giris_zamani,
    a.saat          AS arac_cikis_zamani,
    ag.goruntu      AS arac_goruntu,
    a.serit_id,
    a.ihlal_durumu
FROM itiraz_kayit ik
LEFT JOIN araclar a ON ik.arac_id = a.id -- 'araclar.id' araclar tablosunun PK'sı ise bu doğru
LEFT JOIN (
    SELECT
        ag1.arac_id,
        ag1.goruntu,
        ag1.giris_zamani,
        -- Her arac_id için giris_zamani'na göre azalan, sonra id'ye göre azalan sıra numarası ver
        ROW_NUMBER() OVER (PARTITION BY ag1.arac_id ORDER BY ag1.giris_zamani DESC, ag1.id DESC) as rn
    FROM arac_goruntu ag1
) ag ON ik.arac_id = ag.arac_id AND ag.rn = 1; -- Sadece 1. sıra numarasına sahip kaydı seç                       """)

        itirazlar = cursor.fetchall()

        for itiraz in itirazlar:
            if itiraz['arac_goruntu'] is not None:
                itiraz['arac_goruntu'] = base64.b64encode(itiraz['arac_goruntu']).decode('utf-8')

        return jsonify({'data': itirazlar}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/itiraz', methods=['PUT'])
@token_required
def guncelle_itiraz_durumu(current_user):
    try:
        data = request.json
        username = data.get("username")
        arac_id = data.get("arac_id")
        video_name = data.get("video_name")
        durum = data.get("durum")

        if not all([username, arac_id, video_name, durum]):
            return jsonify({"error": "Eksik parametre"}), 400

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM itiraz_kayit
            WHERE username = %s AND arac_id = %s AND video_name = %s
        """, (username, arac_id, video_name))
        itiraz = cursor.fetchone()

        if not itiraz:
            return jsonify({"error": "İtiraz bulunamadı"}), 404

        cursor.execute("""
            UPDATE itiraz_kayit 
            SET itiraz_durumu = %s 
            WHERE username = %s AND arac_id = %s AND video_name = %s
        """, (durum, username, arac_id, video_name))

        if durum == "Kabul Edildi":
            cursor.execute("""
                UPDATE ihlal_kayit 
                SET ihlal = 0 
                WHERE username = %s AND arac_id = %s AND video_name = %s
            """, (username, arac_id, video_name))

        conn.commit()
        return jsonify({"message": "İtiraz durumu başarıyla güncellendi."}), 200

    except Exception as e:
        print("Sunucu hatası:", e)
        return jsonify({"error": str(e)}), 500

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()





@app.route('/api/videos/<video_name>')
def serve_video_clip(video_name):
    start = request.args.get('start')
    end = request.args.get('end')

    input_path = os.path.join(f'../videos/{video_name}.mp4')

    output_filename = f"clip_{video_name}"
    output_path = f"../temp_clips/clip_{video_name}.mp4"

    try:
        if not os.path.exists(input_path):
            return jsonify({"error": "Video not found"}), 404

        if not os.path.exists('temp_clips'):
            os.makedirs('temp_clips')

        command = [
            'ffmpeg',
            '-i', input_path,
            '-ss', start,
            '-to', end,
            '-c', 'copy',
            output_path,
            '-y'
        ]

        subprocess.run(command, check=True, capture_output=True, text=True)

        return send_file(output_path, mimetype='video/mp4')

    except subprocess.CalledProcessError as e:
        return jsonify({"error": e.stderr}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/itiraz_kayit/detay', methods=['GET'])
def get_itiraz_detay():
    # URL query parametrelerini al
    username = request.args.get('username')
    arac_id = request.args.get('arac_id')
    video_name = request.args.get('video_name')

    if not all([username, arac_id, video_name]):
        return jsonify({"error": "Eksik parametreler: username, arac_id ve video_name gerekli."}), 400

    try:
        arac_id = int(arac_id)
    except ValueError:
        return jsonify({"error": "arac_id geçerli bir sayı olmalıdır."}), 400

    conn = get_connection()
    if conn is None:
        return jsonify({'status': 'error', 'message': 'Veritabanı bağlantısı kurulamadı'}), 500

    cursor = conn.cursor(pymysql.cursors.DictCursor)

    try:
        query = """
                SELECT
                    ik.id,
                    ik.username,
                    ik.arac_id,
                    ik.video_name,
                    ik.durum,
                    ik.sebep,
                    ik.itiraz_durumu,
                    ag.giris_zamani AS arac_giris_zamani,
                    a.saat AS arac_cikis_zamani,
                    ag.goruntu AS arac_goruntu,
                    a.serit_id,
                    a.ihlal_durumu
                FROM itiraz_kayit ik
                LEFT JOIN araclar a ON ik.arac_id = a.id AND ik.video_name = a.video_name
                LEFT JOIN (
                    SELECT
                        ag1.arac_id,
                        ag1.goruntu,
                        ag1.giris_zamani,
                        ROW_NUMBER() OVER (PARTITION BY ag1.arac_id ORDER BY ag1.giris_zamani DESC, ag1.id DESC) as rn
                    FROM arac_goruntu ag1
                ) ag ON ik.arac_id = ag.arac_id AND ag.rn = 1
                WHERE ik.username = %s
                  AND ik.arac_id = %s
                  AND ik.video_name = %s;
                """

        cursor.execute(query, (username, arac_id, video_name))
        itiraz_detay = cursor.fetchone()

        if not itiraz_detay:
            return jsonify({"error": "Belirtilen itiraz detayı bulunamadı."}), 404

        # Binary görüntüyü base64'e çevir
        if itiraz_detay.get('arac_goruntu') is not None:
            itiraz_detay['arac_goruntu'] = base64.b64encode(itiraz_detay['arac_goruntu']).decode('utf-8')

        # Zaman bilgilerini string'e çevir
        datetime_fields = ['arac_giris_zamani', 'arac_cikis_zamani']
        for field in datetime_fields:
            if itiraz_detay.get(field) is not None:
                itiraz_detay[field] = str(itiraz_detay[field])

        return jsonify(itiraz_detay), 200

    except Exception as e:
        print(f"Hata: İtiraz detayları alınırken bir sorun oluştu: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)



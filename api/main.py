from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import json
import os
from pandas.core.interchange.from_dataframe import primitive_column_to_ndarray
from pynvml import c_nvmlUnitInfo_t
import base64

from database.db_config import get_connection
import bcrypt

app = Flask(__name__)
CORS(app)



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
    conn=get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM kullanicilar WHERE username = %s', (username,))
    database_password = cursor.fetchone()
    if database_password is None:
        cursor.close()
        conn.close()
        return jsonify({'status': 'kullanici bulunamadı'})
    else:
        cursor.close()
        conn.close()
        if not bcrypt.checkpw(password.encode('utf-8'), database_password[3].encode('utf-8')):
            return jsonify({'message': 'Invalid email or password'}), 401
        return jsonify({'status': 'ok'})

@app.route('/api/araclar', methods=['GET'])
def get_araclar():
    conn=get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT arac_goruntu.arac_id,giris_zamani,saat,serit_id,ihlal_durumu,araclar.video_name FROM araclar INNER JOIN arac_goruntu ON araclar.arac_id = arac_goruntu.arac_id ORDER BY video_name')
                                                        #arac_goruntu.goruntu EKLENECEK
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'data': data})
@app.route('/api/araclar/<string:video_name>/<int:arac_id>', methods=['GET'])
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
def delete_araclar(video_name,id):
    conn=get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM araclar WHERE video_name=%s and arac_id=%s', (video_name,id))
    cursor.execute('DELETE FROM arac_goruntu WHERE video_name=%s and arac_id=%s', (video_name,id))
    conn.commit()
    cursor.close()
    return jsonify({'status': 'ok'})
@app.route('/api/itiraz_kayit', methods=['POST'])
def get_itiraz():
    conn=get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM itiraz_kayit')
    data=cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify({'data': data})


@app.route('/api/itiraz_et', methods=['POST'])
def itiraz_et():
    data=request.get_json()
    username=data['username']
    arac_id=data['arac_id']
    video_name=data['video_name']
    if data['durum']:
        durum="ihlal"
    else:
        durum="ihlal bulunamadı"
    sebep=data['sebep']
    conn=get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO itiraz_kayit (username, arac_id, video_name, durum, sebep) VALUES (%s, %s, %s, %s, %s)',(username, arac_id, video_name, durum, sebep))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'status': 'ok'})

#@app.route('/api/kayit_izle/<int:arac_id>', methods=['POST'])
#def kayit_izle(arac_id):               TODO: flask video stream araştır




if __name__ == '__main__':
    app.run(debug=True)



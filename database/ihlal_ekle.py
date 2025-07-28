from database.db_config import get_connection


def ihlal_ekle_db(arac_id,saat,serit_id,ihlal_durum,video_name):
    conn = get_connection()
    cursor = conn.cursor()

    sql = "INSERT INTO araclar (arac_id, saat,serit_id,ihlal_durumu,video_name) VALUES (%s, %s,%s,%s,%s)"
    val = (arac_id,saat,serit_id,ihlal_durum,video_name)
    cursor.execute(sql, val)
    conn.commit()
    #print(cursor.rowcount, "kayıt eklendi.")
    cursor.close()
    conn.close()

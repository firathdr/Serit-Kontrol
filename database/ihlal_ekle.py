import database.db_config as db

def ihlal_ekle_db(arac_id,saat,serit_id,ihlal_durum):
    conn = db.get_connection()
    cursor = conn.cursor()

    sql = "INSERT INTO araclar (arac_id, saat,serit_id,ihlal_durumu) VALUES (%s, %s,%s,%s)"
    val = (arac_id,saat,serit_id,ihlal_durum)
    cursor.execute(sql, val)
    conn.commit()

    print(cursor.rowcount, "kayıt eklendi.")

    cursor.close()
    conn.close()

import sqlite3

def ensure_settings_table(con: sqlite3.Connection) -> None:
    sql = """
    CREATE TABLE IF NOT EXISTS 
    guild_settings (guild_id INT PRIMARY KEY, replace_messages BIT);
    """
    cur = con.cursor()
    cur.execute(sql)
    cur.close()

def get_automod_setting(con: sqlite3.Connection, guild_id: int) -> bool:
    sql = """
    SELECT COALESCE(replace_messages, 0) FROM guild_settings
    WHERE guild_id = :id
    """
    cur = con.cursor()
    res = cur.execute(sql, {"id": guild_id})
    return res.fetchone() == (1,)

def set_automod_setting(con: sqlite3.Connection, guild_id: int, replace_messages: bool) -> None:
    # https://www.sqlite.org/draft/lang_UPSERT.html
    sql_upsert = """
    INSERT INTO guild_settings (guild_id, replace_messages) 
    VALUES (:guild_id, :replace_messages)

    ON CONFLICT(guild_id)
    DO 
        UPDATE SET replace_messages = :replace_messages
        WHERE guild_id = :guild_id
    """

    cur = con.cursor()
    cur.execute(sql_upsert, {"replace_messages": replace_messages, "guild_id": guild_id})
    cur.close()
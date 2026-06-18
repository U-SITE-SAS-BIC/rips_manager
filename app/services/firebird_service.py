import fdb
from typing import Optional


class FirebirdService:
    def __init__(self):
        self.conn = None

    def connect(self, host: str, port: int, database: str, user: str, password: str):
        try:
            self.conn = fdb.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                charset="UTF8",
            )
            return True, "Conexión exitosa"
        except Exception as e:
            return False, str(e)

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def is_connected(self) -> bool:
        return self.conn is not None

    def test_connection(self) -> tuple:
        if not self.conn:
            return False, "No hay conexión activa"
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT 1 FROM RDB$DATABASE")
            cur.fetchone()
            return True, "Conexión OK"
        except Exception as e:
            return False, str(e)

    def execute_query(self, query: str, params: Optional[dict] = None) -> tuple:
        if not self.conn:
            return False, "No hay conexión activa", []
        try:
            cur = self.conn.cursor()
            if params is not None:
                cur.execute(query, params)
            else:
                cur.execute(query)
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchall()
            return True, "", [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            return False, str(e), []


def get_firebird_from_config(configs: dict) -> tuple:
    fb = FirebirdService()
    ok, msg = fb.connect(
        configs.get("firebird_host", "localhost"),
        int(configs.get("firebird_port", 3050)),
        configs.get("firebird_database", ""),
        configs.get("firebird_user", "SYSDBA"),
        configs.get("firebird_password", "masterkey"),
    )
    return fb, ok, msg

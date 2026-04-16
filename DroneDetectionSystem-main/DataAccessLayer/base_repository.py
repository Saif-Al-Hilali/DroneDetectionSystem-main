import psycopg2
from scripts.config_manager import config

class BaseRepository:
    def __init__(self):
        self.conn_string = config.connection_string
    
    def _get_connection(self):
        return psycopg2.connect(self.conn_string)
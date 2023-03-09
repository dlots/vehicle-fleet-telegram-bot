import psycopg2


class DatabaseHandler:
    def __init__(self):
        self.__connection = psycopg2.connect(
            database='telegram',
            host='localhost',
            user='postgres',
            password='changeme',
            port='5432'
        )
        self.__cursor = self.__connection.cursor()

    def __execute(self, query: str, args: tuple):
        self.__cursor.execute(query, args)

    def is_logged_in(self, chat_id: int):
        self.__execute('SELECT chat_id FROM users WHERE chat_id=%s', (chat_id,))
        return self.__cursor.fetchone() is not None

    def persist_session(self, chat_id: int, username: str, password: str):
        self.__execute('INSERT INTO users (chat_id, username, password) values (%s, %s, %s)',
                       (chat_id, username, password,))
        self.__connection.commit()

    def remove_session(self, chat_id):
        self.__execute('DELETE FROM users where chat_id=%s', (chat_id,))

    def get_credentials(self, chat_id):
        self.__execute('SELECT * FROM users where chat_id=%s', (chat_id,))
        return self.__cursor.fetchone()


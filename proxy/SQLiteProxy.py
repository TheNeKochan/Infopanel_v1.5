import sqlite3
from threading import Thread, Event
from queue import Queue, LifoQueue
from time import time


class SQLiteProxy(Thread):
    def __init__(self):
        super().__init__()
        self.sql_connection = None
        self.command_queue = Queue()
        self.response_queue = LifoQueue()
        self.working = True

    def PutPage(self, url: str, page: bytes):
        self.command_queue.put(['put', url, page])

    def GetPage(self, url: str):
        event = Event()
        event.clear()
        self.command_queue.put(['get', url, event])
        event.wait()
        response = self.response_queue.get()
        return response

    def run(self) -> None:
        # Init database
        self.sql_connection = sqlite3.connect('proxy.db')
        cursor = self.sql_connection.cursor()
        cursor.execute(
            'CREATE TABLE IF NOT EXISTS "page_content" ('
            '"id"	INTEGER NOT NULL UNIQUE, '
            '"url" TEXT NOT NULL UNIQUE, '
            '"data" BLOB NOT NULL, '
            '"creation_time" INTEGER NOT NULL,'
            ' PRIMARY KEY("id" AUTOINCREMENT))'
        )
        while self.working:
            command = self.command_queue.get(True)
            if command[0] == 'put':
                cursor = self.sql_connection.cursor()
                cursor.execute(
                    'INSERT INTO page_content (url, data, creation_time) VALUES (?, ?, ?)',
                    (command[1], command[2], time())
                )
                cursor.close()
                self.sql_connection.commit()
            elif command[0] == 'get':
                cursor = self.sql_connection.cursor()
                cursor.execute(
                    'SELECT data, creation_time FROM page_content WHERE url = ?',
                    (command[1],)
                )
                result = cursor.fetchone()
                if result is None:
                    self.response_queue.put(None)
                else:
                    # print(result)
                    self.response_queue.put(result[0])
                command[2].set()
                cursor.close()

import os
import psycopg2
import json
import logging

dir = os.path.dirname(__file__)
configpath = os.path.join(dir, "../dbsettings.json")
with open(configpath) as configFile:
    config = json.load(configFile)

connection = psycopg2.connect(database=config["database"], host=config["host"], user=config["user"],
                              password=config["password"], port=config["port"])
connection.autocommit = True


class DBQueue:

    def __init__(self):
        # print("INITIALIZING SPECIAL QUEUE...")
        self.cursor = connection.cursor()
        self.size = 0

    def push(self, item):
        # print("Inserting with priority %d" % priority)

        # self.cursor.execute("SELECT count(1) FROM queue WHERE url=%s", (item.url, ))
        # exists = self.cursor.fetchone()[0]

        try:
            self.cursor.execute("INSERT INTO queue (priority, url, meta) VALUES (%s, %s, %s)",
                                (item['priority'], item['url'], json.dumps({})))
            self.size += 1
        except psycopg2.IntegrityError:
            logging.warning("Tried inserting \"%s\" into queue, but it already exists...", item.url)

    def pop(self):
        self.cursor.execute("DELETE FROM queue "
                            "WHERE url = (select url from queue order by priority desc, id asc limit 1) "
                            "RETURNING id, priority, url, meta")
        result = self.cursor.fetchone()
        if result is not None:
            # print(repr(result))
            # print("Deleting id %d" % result[0])
            self.size -= 1
            return {
                'url': result[2],
                'priority': int(result[1])
            }
        else:
            return None

    def close(self):
        self.cursor.close()

    def __len__(self):
        # Returns an estimate of the queue size, since count(*) is SUPER slow
        self.cursor.execute("SELECT reltuples AS approximate_row_count FROM pg_class WHERE relname = 'queue'")
        result = int(self.cursor.fetchone()[0])
        # if result < 1000:
        #     self.cursor.execute("SELECT count(*) FROM queue")
        #     return self.cursor.fetchone()[0]
        # else:
        #     return result
        return result

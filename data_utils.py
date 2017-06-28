import sqlite3
import logging
from datetime import time

logger = logging.getLogger(__name__)


class Database(object):
    """Class with methods to interact with database"""

    q_save = 'INSERT INTO jobs VALUES (?,?,?)'
    q_delete = 'DELETE FROM jobs WHERE context = ? AND hour = ?'

    @staticmethod
    def create():
        """Creates a new table called 'jobs'"""
        conn = sqlite3.connect('jobs.db')
        with conn:
            conn.execute('''DROP TABLE IF EXISTS jobs''')
            conn.commit()
            conn.execute('''CREATE TABLE jobs
                          (context text, hour text, name text,
                          CONSTRAINT hour_unique UNIQUE(context, hour))''')
        conn.close()

    def save(self, context, hour, name):
        """Saves a job's context and time to the db"""
        conn = sqlite3.connect('jobs.db')
        with conn:
            conn.execute(self.q_save, (context, hour, name))
        conn.close()

    def delete(self, context, hour):
        """Deletes a job's context and time"""
        conn = sqlite3.connect('jobs.db')
        try:
            with conn:
                conn.execute(self.q_delete, (context, hour))
            conn.close()
            return True
        except sqlite3.DatabaseError as e:
            logger.warning(e)
            conn.close()
            return False

    @staticmethod
    def load_jobs():
        """Returns all jobs in the database"""
        conn = sqlite3.connect('jobs.db')
        try:
            jobs = conn.execute('SELECT * from jobs').fetchall()
            conn.close()
            return jobs
        except sqlite3.DatabaseError as e:
            logger.warning(e)
            conn.close()
            return None

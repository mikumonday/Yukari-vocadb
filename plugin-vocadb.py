import json
import re

from connections.database import db
from yukari.customlogger import clog
from yukari.tools import getTime

syst = 'VocaDB(P)'

class VocaDB(object):
    def __init__(self):
        self.nicoRe = re.compile(r'sm[0-9]{6,9}|nm[0-9]{6-9}')

    def _q_checkSong(self, cy, fdict):
        pass

    def _cM_updatePanel(self, cy, fdict):
        pass

    def _com_vocadb(self, cy, username, args):
        pass

def makeDatabase():
    import sqlite3
    con = sqlite3.connect('data.db')
    clog.warning('Creating Song table...', syst)
    con.execute("""
        CREATE TABLE IF NOT EXISTS Song(
        songId INTEGER PRIMARY KEY,
        data TEXT NOT NULL,
        lastUpdate INTEGER NOT NULL);""")
    try:
        con.execute('INSERT INTO Song VALUES (?, ?, ?)', 
                    (-1, 'connection error', 0))
        con.execute('INSERT INTO Song VALUES (?, ?, ?)', (0, 'null', 0))
        clog.warning('Inserted default values to Song table.', syst)
    except(sqlite3.IntegrityError):
        pass
    clog.warning('Creating MediaSong table...', syst)
    con.execute("""
        CREATE TABLE IF NOT EXISTS MediaSong(
        mediaId INTEGER NOT NULL,
        songId INTEGER NOT NULL,
        userId INTEGER NOT NULL,
        time INTEGER NOT NULL,
        method INTEGER NOT NULL,
        UNIQUE (mediaId),
        FOREIGN KEY (mediaId) REFERENCES Media(mediaId),
        FOREIGN KEY (songId) REFERENCES Song(songId),
        FOREIGN KEY (userId) REFERENCES CyUser(userId));""")
    con.commit()
    con.close()

def setup():
    makeDatabase()
    return VocaDB()

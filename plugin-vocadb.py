import json
import re
import sqlite3

from connections.database import db
from yukari.customlogger import clog
from yukari.tools import getTime

syst = 'VocaDB(P)'

class VocaDB(object):
    def __init__(self):
        self.nicoRe = re.compile(r'sm[0-9]{6,9}|nm[0-9]{6-9}')

    def _q_checkSong(self, cy, mediad):
        mType = mediad['media']['type']
        mId = mediad['media']['id']
        self.checkMediaSong(mType, mId)

    def _cM_updatePanel(self, cy, fdict):
        pass

    def _com_vocadb(self, cy, username, args):
        #self.getSong('yt', 'abcdefg', args, 4, 123, 'na')
        self.checkMediaSong('yt', '01uN4MCsrCE')

    def getSongFromSongId(self, mType, mId, songId, userId, timeNow, method):
        #### DO LATER TODO"""
        """ Returns a deferred of a VocaDB Song data of songId """
        # Try to retrieve from Song table
        # If it doesn't exist, request from VocaDB
        ## Write new info from VocaDB to local db
        ## Then, save to MediaSong

        d = db.query('SELECT * FROM Song WHERE songId=?', (songId,))
        d.addCallback(self.cbGotSong)

    def cbGotSong(self, result):
        clog.warning(str(result), syst)

    def checkMediaSong(self, mType, mId):
        """Check database MediaSong table to see if row exists"""
        sql = ('SELECT 1 FROM MediaSong WHERE mediaid=( '
               'SELECT mediaId FROM Media WHERE type=? AND id=?)')
        binds = (mType, mId)
        d = db.query(sql, binds)
        d.addCallback(self.cbCheckMediaSong, mType, mId)

    def cbCheckMediaSong(self, result, mType, mId):
        clog.warning(str(result), syst)
        if not result:
            clog.warning('request vocadb here', syst)
            #self.requestVocadb(mType, mId)

    def requestSongById(self, mType, mId, songId, userId, timeNow, method):
        """ Returns a deferred of Vocadb data of Song songId"""
        # check Song table to see if it's already saved
        ##if not, request data from VocaDB
        # UPDATE (or add) row in MediaSong table

        d = database.dbQuery(('data',), 'Song', songId=songId)
        d.addCallback(database.queryResult)
        d.addErrback(self.requestApiBySongId, songId, timeNow) # res is (body, songId)
        d.addCallbacks(database.insertMediaSong, apiError,
                       (mType, mId, songId, userId, timeNow, method))
        d.addErrback(self.ignoreErr)
        return d

    def requestApiBySongId(self, res, songId, timeNow):
        """ Request video information from VocaDb API v2
        and save to the Song table """
        agent = Agent(reactor)
        url = 'http://vocadb.net/api/songs/%s?' % songId
        url += '&fields=artists,names&lang=romaji'
        clog.warning('(requestApiBySongId) %s' % url, syst)
        d = agent.request('GET', url, Headers({'User-Agent':[UserAgentVdb]}))
        d.addCallback(readBody)
        d.addCallbacks(self.processVdbJson, self.apiError)
        d.addCallback(database.insertSong, timeNow)
        return d

    def requestSongByPv(self, res, mType, mId, userId, timeNow, method):
        """ Returns a deferred of Vocadb data of Song songId"""
        # check mediaSong first
        # request data from VocaDB
        # UPDATE (or add) row in MediaSong table
        d = database.queryMediaSongRow(mType, mId)
        d.addCallback(self.mediaSongResult, mType, mId, userId, timeNow)
        d.addErrback(self.ignoreErr)
        return d

    def mediaSongResult(self, res, mType, mId, userId, timeNow):
        clog.info('(mediaSongResult) %s' % res, syst)
        if res:
            return defer.succeed(res[0])
        else:
            dd = self.requestApiByPv(mType, mId, timeNow)
            dd.addErrback(self.apiError)
            dd.addCallback(self.youtubeDesc, mType, mId, timeNow)
            dd.addCallback(database.insertMediaSongPv, mType, mId, userId, timeNow)
            return dd

    def requestApiByPv(self, mType, mId, timeNow):
        """ Request song information by Youtube or NicoNico Id,
        and save data to Song table """
        agent = Agent(reactor)
        if mType == 'yt':
            service = 'Youtube'
        else:
            service = 'NicoNicoDouga'
        url = 'http://vocadb.net/api/songs?pvId=%s&pvService=%s' % (mId, service)
        url += '&fields=artists,names&lang=romaji'
        clog.warning('(requestApiByPv) %s' % url, syst)
        dd = agent.request('GET', str(url), Headers({'User-Agent':[UserAgentVdb]}))
        dd.addCallback(readBody)
        dd.addCallbacks(self.processVdbJson, self.apiError)
        dd.addCallback(database.insertSong, timeNow)
        return dd

    def youtubeDesc(self, res, mType, mId, timeNow):
        if res[0] == 0: # no match
            clog.debug(('(youtubeDesc) No Youtube id match. Will attemp to retrieve'
                       'and parse description %s') % res, syst)
            d = apiClient.requestYtApi(mId, 'desc')
            d.addCallback(self.searchYtDesc, mType, mId, timeNow)
            d.addErrback(self.errNoIdInDesc)
            return d
        else:
            # pass-through the with method 0, results
            return defer.succeed((0, res[0]))

    def errNoIdInDesc(self, res):
        clog.warning('errNoIdInDesc %s' % res, syst)
        return defer.succeed((1, 0))

    def nicoAcquire(self, res):
        clog.debug('nicoAcquire %s' % res, syst)
        if res[0] == 0: # no match
            clog.debug('(youtubeDesc) No Nico id match.', syst)
        return defer.succeed((1, res[0]))

    def searchYtDesc(self, res, mType, mId, timeNow):
        m = nicoMatch.search(res)
        if m:
            nicoId = m.group(0)
            clog.debug(nicoId, 'searchYtDesc')
            d = self.requestApiByPv('NicoNico', nicoId, timeNow)
            d.addCallback(self.nicoAcquire)
            d.addCallback(database.insertMediaSongPv, mType, mId, 1, timeNow)
            return d
        else:
            database.insertMediaSongPv(0, mType, mId, 1, timeNow)
            return defer.fail(Exception('No NicoId in Description found'))

    def apiError(self, err):
        clog.error('(apiError) There was a problem with VocaDB API. %s' %
                   err.value, syst)
        err.printDetailedTraceback()
        return err

    def dbErr(self, err):
        clog.error('(dbErr) %s' % err.value, syst)
        return err

    def ignoreErr(self, err):
        'Consume error and return a success'
        clog.error('(ignoreErr) %s' % err.value, syst)
        return defer.succeed(None)

def makeDatabase():
    con = sqlite3.connect('data.db')
    try:
        con.execute('SELECT 1 FROM Song')
        return
    except(sqlite3.OperationalError):
        clog.warning('Song table does not exist.')
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

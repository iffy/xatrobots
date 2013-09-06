try:
    from pysqlite2 import dbapi2
    sqlite = dbapi2
except:
    import sqlite3 as sqlite

from twisted.internet import defer
from txscrypt import computeKey, checkPassword

from xatro.error import NotFound, BadPassword



class FileStoredPasswords(object):
    """
    I authenticate passwords from data stored in an sqlite3 file
    """


    def __init__(self, filename):
        self.db = sqlite.connect(filename)
        self.db.execute('create table if not exists entity '
                        '(name blob primary key, pw blob)')


    def _get(self, name):
        c = self.db.cursor()
        c.execute('select pw from entity where name=?', (buffer(name),))
        row = c.fetchone()
        if not row:
            raise NotFound(name)
        return str(row[0])
    

    def _set(self, name, pw_hash):
        self.db.execute('insert into entity (name, pw) values (?, ?)',
                        (buffer(name), buffer(pw_hash)))
        self.db.commit()


    def createEntity(self, name, password):
        return computeKey(password).addCallback(self._gotHash, name)


    def _gotHash(self, pw_hash, name):
        self._set(name, pw_hash)
        return name


    def checkPassword(self, name, password):
        try:
            pw_hash = self._get(name)
        except NotFound:
            return defer.fail(BadPassword('Bad password: %r' % (name,)))
        d = checkPassword(pw_hash, password)
        d.addCallback(self._passwordMatches, name)
        return d


    def _passwordMatches(self, matches, name):
        if matches:
            return name
        raise BadPassword('Bad password: %r' % (name,))
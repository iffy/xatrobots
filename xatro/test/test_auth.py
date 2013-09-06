from twisted.trial.unittest import TestCase
from twisted.internet import defer
from twisted.python.filepath import FilePath


from xatro.error import BadPassword
from xatro.auth import FileStoredPasswords


class FileStoredPasswordsTest(TestCase):


    @defer.inlineCallbacks
    def test_createEntity(self):
        """
        You can create an entity with a password.
        """
        f = self.mktemp()
        auth = FileStoredPasswords(f)
        name = yield auth.createEntity('foo', 'password')
        self.assertEqual(name, 'foo')


    @defer.inlineCallbacks
    def test_checkPassword(self):
        """
        You can verify that the correct password is given.
        """
        f = self.mktemp()
        auth = FileStoredPasswords(f)
        yield auth.createEntity('foo', 'password')
        name = yield auth.checkPassword('foo', 'password')
        self.assertEqual(name, 'foo')


    @defer.inlineCallbacks
    def test_checkPassword_fail(self):
        """
        The wrong password should result in a BadPassword exception.
        """
        f = self.mktemp()
        auth = FileStoredPasswords(f)
        yield auth.createEntity('foo', 'password')
        self.assertFailure(auth.checkPassword('foo', 'not the password'),
                           BadPassword)


    def test_checkPassword_dne(self):
        """
        If the entity doesn't exist, it should raise BadPassword
        """
        f = self.mktemp()
        auth = FileStoredPasswords(f)
        self.assertFailure(auth.checkPassword('foo', 'password'),
                           BadPassword)


    @defer.inlineCallbacks
    def test_persist(self):
        """
        Passwords should persist in the file.
        """
        f = self.mktemp()
        auth = FileStoredPasswords(f)
        yield auth.createEntity('foo', 'password')

        auth2 = FileStoredPasswords(f)
        yield auth.checkPassword('foo', 'password')




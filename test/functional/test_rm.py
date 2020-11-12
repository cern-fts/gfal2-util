from builtins import bytes
import unittest
import os

from base import TestBase
import utils

class UtilRmTest(TestBase):
    def test_recursive(self):
        self.assertTrue(os.path.exists(self.dirname))
        (ret, out, err) = utils.run_command('gfal-rm', '-r ' + ' file://' + self.dirname)
        self.assertFalse(os.path.exists(self.dirname))
        self.assertEqual(ret, 0)


    def test_dir_non_rec(self):
        self.assertTrue(os.path.exists(self.dirname))
        (ret, out, err) = utils.run_command('gfal-rm', 'file://' + self.dirname)
        self.assertTrue(os.path.exists(self.dirname))
        self.assertTrue(bytes("directory", 'utf-8') in err)
        self.assertEqual(ret, 21)

    def test_multiple(self):
        self.assertTrue(os.path.exists(self.ffname1))
        self.assertTrue(os.path.exists(self.ffname2))
        (ret, out, err) = utils.run_command('gfal-rm',\
                        'file://' + self.ffname1 + ' file://' + self.ffname2)
        self.assertFalse(os.path.exists(self.ffname1))
        self.assertFalse(os.path.exists(self.ffname2))
        self.assertEqual(ret, 0)

if __name__ == '__main__':
    unittest.main()

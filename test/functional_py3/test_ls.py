import unittest
from . import utils
import shutil
import os
from .base import TestBase

class UtilLsTest(TestBase):    
    def test_size(self):
        (ret, out, err) = utils.run_command('gfal-ls', '-lH ' + ' file://' + self.ffname1)
        self.assertTrue(bytes(' 1.1K ',  'utf-8')  in out)
        self.assertEqual(ret, 0)

        (ret, out, err) = utils.run_command('gfal-ls', '-l' + ' file://' + self.ffname1)
        self.assertTrue(bytes(' 1025 ', 'utf-8') in out)
        self.assertEqual(ret, 0)
    
    def test_invalid(self):
        inv_name = self.ffname1 + "INVALID"
        (ret, out, err) = utils.run_command('gfal-ls', '-lH ' + ' file://' + inv_name)
        self.assertEqual(ret, 2)
        self.assertTrue(bytes('No such file or directory', 'utf-8') in err)
        self.assertEqual(len(out), 0)

    def test_basic(self):
        (ret, out, err) = utils.run_command('gfal-ls', 'file://' + self.dirname)
        self.assertEqual(len(out.splitlines()), utils.num_entries(self.dirname))
        self.assertTrue(bytes(self.fname1,  'utf-8')  in out)
        self.assertTrue(bytes(self.fname2, 'utf-8')  in out)
        self.assertEqual(ret, 0)
        
    def test_directory(self):
        (ret, out, err) = utils.run_command('gfal-ls', '-ld' + ' file://' + self.ffname1)
        self.assertEqual(len(out.splitlines()), 1)
        self.assertEqual(ret, 0)
        
        
    def test_name(self):
        (ret, out, err) = utils.run_command('gfal-ls', '-l' + ' file://' + self.ffname1)
        self.assertTrue(bytes(' file://' + self.ffname1,  'utf-8') in out)
        self.assertEqual(ret, 0)
        
        (ret, out, err) = utils.run_command('gfal-ls', '-dl' + ' file://' + self.ffname1)
        self.assertTrue(bytes(' file://' + self.ffname1,  'utf-8') in out)
        self.assertEqual(ret, 0)
    
    def tearDown(self):
        shutil.rmtree(self.dirname)
    
if __name__ == '__main__':
    unittest.main()

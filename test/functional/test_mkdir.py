from __future__ import absolute_import

from .base import TestBase
import unittest
import os
import shutil
from . import utils

class UtilMkdirTest(TestBase):    
    def test_mkdir(self):
        shutil.rmtree(self.dirname)
        self.assertFalse(os.path.isdir(self.dirname))
        
        (ret, out, err) = utils.run_command('gfal-mkdir', 'file://' + self.dirname)
        
        self.assertTrue(os.path.isdir(self.dirname))
        self.assertEqual(utils.get_permissions(self.dirname), '755')
        self.assertEqual(len(out), 0)
        self.assertEqual(ret, 0)
        
    def test_mkdir_mode(self):
        shutil.rmtree(self.dirname)
        self.assertFalse(os.path.isdir(self.dirname))
        
        (ret, out, err) = utils.run_command('gfal-mkdir', '-m 0700 file://' + self.dirname)
        
        self.assertTrue(os.path.isdir(self.dirname))
        self.assertEqual(utils.get_permissions(self.dirname), '700')
        self.assertEqual(len(out), 0)
        self.assertEqual(ret, 0)
        
    def test_mkdir_recursive(self):
        d = self.dirname + '/subdir/subdir'
        shutil.rmtree(self.dirname)
        self.assertFalse(os.path.isdir(d))
        
        (ret, out, err) = utils.run_command('gfal-mkdir', '-p file://' + d)
        
        self.assertTrue(os.path.isdir(d))
        self.assertEqual(utils.get_permissions(d), '755')
        self.assertEqual(len(out), 0)
        self.assertEqual(ret, 0)
        
    def test_already_exists(self):
        self.assertTrue(os.path.isdir(self.dirname))
        
        (ret, out, err) = utils.run_command('gfal-mkdir', 'file://' + self.dirname)
        
        self.assertTrue(os.path.isdir(self.dirname))
        self.assertEqual(len(out), 0)
        self.assertTrue(len(err) > 0)
        self.assertTrue(bytes('File exists',  'utf-8')  in err)
        self.assertEqual(ret, 17)
        
    def test_already_exists_p(self):
        self.assertTrue(os.path.isdir(self.dirname))
        
        (ret, out, err) = utils.run_command('gfal-mkdir', '-p file://' + self.dirname)
        
        self.assertTrue(os.path.isdir(self.dirname))
        self.assertEqual(len(out), 0)
        self.assertEqual(ret, 0)
        
    def test_invalid_mode(self):
        shutil.rmtree(self.dirname)
        self.assertFalse(os.path.isdir(self.dirname))
        
        (ret, out, err) = utils.run_command('gfal-mkdir', '-m A file://' + self.dirname)

        self.assertFalse(os.path.isdir(self.dirname))
        self.assertFalse(ret == 0)
        
if __name__ == '__main__':
    unittest.main()
    

import unittest
from . import utils
import shutil
import os
from .base import TestBase

class UtilGeneralTest(TestBase): 
    def test_protocol_not_supported(self):
        (ret, out, err) = utils.run_command('gfal-ls', 'xyzf://fakepath')
        self.assertEqual(len(out), 0)
        self.assertTrue(bytes('Protocol not supported', 'utf-8') in err)
        self.assertEqual(ret, 93)
        
    def _test_full_path(self):
        (ret, out, err) = utils.run_command('/usr/local/bin/gfal-ls', 'file://' + self.dirname)
        self.assertEqual(len(err), 0)
        self.assertEqual(ret, 0)
        
    def _test_non_verbose_error(self):
        (ret, out, err) = utils.run_command('/usr/local/bin/gfal-ls', self.dirname)
        self.assertEqual(len(out), 0)
        self.assertEqual(len(err.splitlines()), 1)
        self.assertTrue(err.startswith('gfal-ls:'))

if __name__ == '__main__':
    unittest.main()

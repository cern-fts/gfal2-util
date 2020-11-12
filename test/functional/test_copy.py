import unittest
import os

from base import TestBase
import utils

class UtilCopyTest(TestBase):
    def test_copy(self):
        ffname3 = self.ffname1 + "_copy"
        self.assertFalse(os.path.isfile(ffname3))

        (ret, out, err) = utils.run_command('gfal-copy', \
                            'file://' + self.ffname1 + ' file://' + ffname3)

        self.assertTrue(os.path.isfile(ffname3))
        self.assertEqual(ret, 0)

        if os.path.isfile(ffname3):
            os.remove(ffname3)

    def test_copy_no_basename(self):
        self.assertTrue(os.path.isfile(self.ffname1))
        dst_path = '/tmp/'
        dst = dst_path + os.path.basename(self.ffname1)

        self.assertFalse(os.path.isfile(dst))

        (ret, out, err) = utils.run_command('gfal-copy', \
                            'file://' + self.ffname1 + ' file://' + dst_path)

        self.assertTrue(os.path.isfile(dst))
        self.assertEqual(ret, 0)

        if os.path.isfile(dst):
            os.remove(dst)

    def test_chain_copy(self):
        self.assertTrue(os.path.isfile(self.ffname1))
        d1 = self.ffname1 + '_cp1'
        d2 = self.ffname1 + '_cp2'
        d3 = '/tmp'
        d4 = self.ffname1 + '_cp3'

        args = 'file://' + self.ffname1 + ' file://' + d1 + ' file://' + d2 \
                         + ' file://' + d3 + ' file://' + d4
        (ret, out, err) = utils.run_command('gfal-copy', args)

        self.assertTrue(os.path.isfile(d1))
        self.assertTrue(os.path.isfile(d2))
        self.assertTrue(os.path.isfile(d3 + '/' +  os.path.basename(d2)))
        self.assertTrue(os.path.isfile(d4))

        if os.path.isfile(d1):
            os.remove(d1)
        if os.path.isfile(d2):
            os.remove(d2)
        if os.path.isfile(d3):
            os.remove(d3)

    def test_copy_dst_dir(self):
            self.assertTrue(os.path.isfile(self.ffname1))
            dst_path = '/tmp'
            dst = dst_path + '/' + os.path.basename(self.ffname1)

            self.assertFalse(os.path.isfile(dst))

            (ret, out, err) = utils.run_command('gfal-copy', \
                                'file://' + self.ffname1 + ' file://' + dst_path)

            self.assertTrue(os.path.isfile(dst))
            self.assertEqual(ret, 0)

            if os.path.isfile(dst):
                os.remove(dst)

    def test_copy_dir(self):
            self.assertTrue(os.path.isfile(self.ffname1))
            src = os.path.dirname(self.ffname1)
            self.assertTrue(os.path.isdir(src))
            dst = '/tmp/'

            (ret, out, err) = utils.run_command('gfal-copy', \
                                'file://' + src + ' file://' + dst)

            self.assertFalse(os.path.isfile(dst + os.path.basename(self.ffname1)))
            self.assertTrue(ret >= 0)

    def test_copy_parent_enoent(self):
        self.assertTrue(os.path.isfile(self.ffname1))
        dst_path = '/tmp/make/parent'
        self.assertFalse(os.path.isfile(dst_path))

        (ret, out, err) = utils.run_command('gfal-copy', 'file://' + self.ffname1 + ' file://' + dst_path)

        self.assertFalse(os.path.isfile(dst_path))
        self.assertTrue(ret >= 0)

    def test_copy_parent_mkdir(self):
        self.assertTrue(os.path.isfile(self.ffname1))
        dst_path = '/tmp/make/parent'
        self.assertFalse(os.path.isfile(dst_path))

        (ret, out, err) = utils.run_command('gfal-copy', '-p file://' + self.ffname1 + ' file://' + dst_path)

        self.assertTrue(os.path.isfile(dst_path))
        self.assertTrue(ret >= 0)

        os.unlink(dst_path)
        os.rmdir('/tmp/make/')

    def test_copy_pseudotty(self):
        """
        Regression test for DMC-522
        Trick gfal-copy into thinking it is inside a tty so we trigger some logic that would not
        be executed otherwise
        """
        ffname3 = self.ffname1 + "_copy"
        self.assertFalse(os.path.isfile(ffname3))

        (ret, out, err) = utils.run_command_pty('gfal-copy', \
                            'file://' + self.ffname1 + ' file://' + ffname3)

        self.assertTrue(os.path.isfile(ffname3))
        self.assertNotEqual(len(out), 0) # this makes sure the interactive mode works!
        self.assertEqual(ret, 0)

        if os.path.isfile(ffname3):
            os.remove(ffname3)

if __name__ == '__main__':
    unittest.main()

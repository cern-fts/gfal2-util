import unittest
import utils
import shutil
import os

class TestBase(unittest.TestCase):
    def setUp(self):
        #create dir
        self.dirname = '/tmp/test_' + utils.create_random_suffix()
        os.mkdir(self.dirname)
        
        self.subdir = self.dirname + '/test_' + utils.create_random_suffix()
        os.mkdir(self.subdir)
        
        self.fname1 = 'f1_' + utils.create_random_suffix()
        self.fname2 = 'f2_' + utils.create_random_suffix()
        
        self.ffname1 = self.dirname + '/' + self.fname1
        self.ffname2 = self.dirname + '/' + self.fname2
        
        utils.create_file(self.ffname1, 1025)
        utils.create_file(self.ffname2, 1025)
        
    def tearDown(self):
        if os.path.isdir(self.dirname):
            shutil.rmtree(self.dirname)
            
        if(os.path.isfile(self.ffname2)):
            os.remove(self.ffname2)
        
        if(os.path.isfile(self.ffname1)):
            os.remove(self.ffname1)
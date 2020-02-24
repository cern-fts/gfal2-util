from xmlrunner import XMLTestRunner
import sys

from test_ls import *
from test_copy import *
from test_general import *
from test_rm import *
from test_mkdir import *

fname = 'test_results.xml'

if __name__ == '__main__':
    s = open(fname, 'w')
    unittest.main(testRunner=XMLTestRunner(stream=sys.stdout))

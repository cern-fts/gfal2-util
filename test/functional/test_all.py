import sys

if __name__ == '__main__' and __package__:
    import os
    sys.path.append(os.path.dirname(__file__))

from test_ls import *
from test_copy import *
from test_general import *
from test_rm import *
from test_mkdir import *
from xmlrunner import XMLTestRunner

if __name__ == '__main__':
    s=open('test_results.xml', 'w')
    unittest.main(testRunner=XMLTestRunner(stream=sys.stdout))

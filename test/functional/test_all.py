from __future__ import absolute_import

from .test_ls import *
from .test_copy import *
from .test_general import *
from .test_rm import *
from .test_mkdir import *
from .xmlrunner import XMLTestRunner
import sys

if __name__ == '__main__':
    s=open('test_results.xml', 'w')
    unittest.main(testRunner=XMLTestRunner(stream=sys.stdout))

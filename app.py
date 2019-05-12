import os
from pydxcc import dxcc
import configparser

CFG = configparser.ConfigParser()
CFG.read(os.path.expanduser(os.path.dirname(os.path.abspath(__file__)) + '/pydxcc.cfg'))
CTYFILES_PATH = os.path.expanduser(CFG.get('CTYFILES', 'path'))
CTYFILES_URL = CFG.get('CTYFILES', 'url')
AUTOFETCH_FILES = CFG.getboolean('CTYFILES', 'autofetch')

pydxcc_instance = dxcc(CTYFILES_PATH, CTYFILES_PATH, AUTOFETCH_FILES)
for pattern in pydxcc_instance.GLOBAL_DXCC_LIST:
    print(pattern)
from timeit import default_timer as timer
start = timer()
print(pydxcc_instance.call2dxcc('DL/ZL1IO', None))
print(pydxcc_instance.call2dxcc('DP1POL', None))
print(pydxcc_instance.dxcc2json(pydxcc_instance.call2dxcc('DL0ABC', None)))
print(pydxcc_instance.call2dxcc('RP74ABC', None))
print(pydxcc_instance.call2dxcc('FW5JG', None))
end = timer()
print(end - start)
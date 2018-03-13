#!/usr/bin/python3
"""simple dxcc-resolution program to be used with cqrlogs dxcc-tables"""
import os
import csv
import re
from collections import OrderedDict
from datetime import datetime
import dicttoxml
import json
import configparser

CFG = configparser.ConfigParser()
CFG.read(os.path.expanduser(os.path.dirname(__file__) + '/pydxcc.cfg'))
CTYFILES_PATH = os.path.expanduser(CFG.get('CTYFILES', 'path'))

DEBUG = 3
TRACE1 = 4
TRACE2 = 5
VERBOSE = DEBUG

NODXCC = { 'long': None, 'lat': None, 'valid_to': None, 'utc': None, 'waz': None, 'adif': None, 'itu': None, 'valid_from': None, 'name': 'No DXCC', 'continent': None }

def pattern_to_regex(patternlist):
    """transform pattern from file to regex"""
    # = is the hint in country.tab, that an explicit call is given
    returnlist = []
    patternlist = patternlist.replace('  ', ' ')
    for pattern in patternlist.split(' '):
        if '%' in pattern or '#' in pattern or '=' in pattern:
            pattern = pattern.replace('%', '[A-Z]').replace('#', '[0-9]')
            pattern += '$'
        pattern = '^' + pattern
        returnlist.append(pattern)
    return returnlist
        

def date_country_tab(date = None):
    """initializes a dict with data from the dxcc-tables from file, filtered by date"""
    if not date:
        date = datetime.utcnow()
    date_dxcc_regex = re.compile(r'((?P<from>\d\d\d\d/\d\d/\d\d)*-(?P<to>\d\d\d\d/\d\d/\d\d)*)*(=(?P<alt_dxcc>\d*))*')
    with open(CTYFILES_PATH + 'country.tab', "r", encoding='utf-8') as countrytab:
        # split country.tab to list linewise
        countrytabcsv = csv.reader(countrytab, delimiter='|')
        dxcc_list = {}
        for row in countrytabcsv:
            row_list = list(row)
            if True:
                indaterange = True
                try:
                    date_dxcc_string = date_dxcc_regex.search(row_list[10])
                except IndexError as error:
                    if VERBOSE >= DEBUG:
                        print('{} for line {}'.format(error, row_list))
                else:
                    dateto_string = None
                    dateto = None
                    datefrom_string = None
                    datefrom = None
                    # check, if timerange is (partly) given
                    if date_dxcc_string.group('to'):
                        try:
                            dateto = datetime.strptime(date_dxcc_string.group('to'), '%Y/%m/%d')
                            dateto_string = dateto.strftime("%Y-%m-%d")
                        except ValueError as valerr:
                            if VERBOSE >= DEBUG:
                                print('{} in date_to of line {}'.format(valerr,row_list))
                    if date_dxcc_string.group('from'):
                        try:
                            datefrom = datetime.strptime(date_dxcc_string.group('from'), '%Y/%m/%d')
                            datefrom_string = datefrom.strftime("%Y-%m-%d")
                        except ValueError as valerr:
                            if VERBOSE >= DEBUG:
                                print('{} in date_from of line {}'.format(valerr,row_list))
                    if dateto is not None:
                        if date > dateto:
                            indaterange = False
                    if indaterange and not datefrom is None:
                        if date < datefrom:
                            indaterange = False
                    if indaterange:
                        pattern = row_list[0]
                        if row_list[9] == "R":
                            adif = date_dxcc_string.group('alt_dxcc')
                        else:
                            adif = row_list[8]
                        attributes = {
                            'details' : row_list[1],
                            'continent' : row_list[2],
                            'utc' : row_list[3],
                            'lat' : row_list[4],
                            'lng' : row_list[5],
                            'itu' : row_list[6],
                            'waz' : row_list[7],
                            'valid_from' : datefrom_string,
                            'valid_to' : dateto_string,
                            'adif' : adif
                        }
                        for singlepattern in pattern_to_regex(pattern.strip()):
                            # prefix non-REGEX patterns with ~
                            if row_list[9] != "R":
                                singlepattern = '~' + singlepattern
                            dxcc_list[singlepattern] = attributes

    if VERBOSE >= DEBUG:
        print("{} calls parsed".format(len(dxcc_list)))
    return dxcc_list

def dxcc2xml(dxcc):
    return dicttoxml.dicttoxml(dxcc[1], attr_type=False)

def dxcc2json(dxcc):
    return json.dumps(dxcc[1])

def init_country_tab(date = None):
    """builds an initial GLOBAL_DXCC_LIST, if date not defined with date from today"""
    if not date:
        date = datetime.utcnow()
        if VERBOSE >= DEBUG:
            print("initializing GLOBAL_DXCC_LIST with date {}".format(date.strftime("%Y-%m-%d")))
    GLOBAL_DXCC_LIST[date.strftime("%Y-%m-%d")] = date_country_tab(date)

def get_date_country_tab(date):
    """returns date-specific country-tab, builds it, if needed"""
    if not date:
        date = datetime.utcnow()
    if not GLOBAL_DXCC_LIST.get(date.strftime("%Y-%m-%d")):
        if VERBOSE >= DEBUG:
            print("{} not found in GLOBAL_DXCC_LIST, adding".format(date.strftime("%Y-%m-%d")))
        GLOBAL_DXCC_LIST[date.strftime("%Y-%m-%d")] = date_country_tab(date)
    else:
        if VERBOSE >= DEBUG:
            print("{} found in GLOBAL_DXCC_LIST, using that".format(date.strftime("%Y-%m-%d")))
    return GLOBAL_DXCC_LIST[date.strftime("%Y-%m-%d")]

def call2dxcc(callsign, date = None):
    """does the job in resolving the callsign"""
    ORIGINALCALLSIGN = callsign
    # if date is not given, assume date is now
    if not date:
        date = datetime.utcnow()
    else:
        date = datetime.strptime(date, "%Y-%m-%d")
    direct_hit_list = {}
    prefix_hit_list = {}
    regex_hit_list = OrderedDict()
#    DXCC_DATE_LIST =  DXCC_LIST[date.strftime("%Y-%m-%d")]
    DXCC_LIST = get_date_country_tab(date)
    for pattern in DXCC_LIST:
        #print(pattern)
        if "=" in pattern and len(callsign) == (len(pattern) -3):
            direct_hit_list[pattern.replace('=', '')] = DXCC_LIST[pattern]
        # ~ indicates, that a PREFIX and not a REGEX is given for CEPT based resolution
        elif "~" in pattern:
            prefix_hit_list[pattern.replace('~', '')] = DXCC_LIST[pattern]
        else:
            regex_hit_list[pattern] = DXCC_LIST[pattern]
    # chech for direct hits
    for pattern in direct_hit_list:
        if re.match(pattern, callsign):
            pattern = pattern.replace('^', '^=')
            if VERBOSE >= DEBUG:
                print("found direct hit {} {}".format(pattern, DXCC_LIST[pattern]))
            DXCC_LIST[pattern]["callsign"] = ORIGINALCALLSIGN
            return [pattern, DXCC_LIST[pattern]]
    # check for portable calls, after testing for direct hits
    if '/' in callsign:
        callsign = handleExtendedCalls(callsign)
        if callsign == False:
            if VERBOSE >= DEBUG:
                print("callsign not valid for DXCC")
                NODXCC["callsign"] = ORIGINALCALLSIGN
            return [None, NODXCC]
    # check for regex hits
    for pattern in regex_hit_list:
        if pattern[1] in [callsign[0],'[']:                    
            if VERBOSE >= TRACE1:
                print(pattern)
            if re.match(pattern, callsign):
                if VERBOSE >= DEBUG:
                    print("found {} {}".format(pattern, DXCC_LIST[pattern]))
                DXCC_LIST[pattern]["callsign"] = ORIGINALCALLSIGN
                return [pattern, DXCC_LIST[pattern]]
    # check for prefix hits
    for pattern in prefix_hit_list:
        if VERBOSE >= TRACE1:
            print(pattern)
        if re.match(pattern, callsign):
            pattern = pattern.replace('^', '~^')
            if VERBOSE >= DEBUG:
                print("found {} {}".format(pattern, DXCC_LIST[pattern]))
            DXCC_LIST[pattern]["callsign"] = ORIGINALCALLSIGN
            return [pattern, DXCC_LIST[pattern]]
    if VERBOSE >= DEBUG:
        print("no matching dxcc found")
    NODXCC["callsign"] = ORIGINALCALLSIGN
    return[None, NODXCC]

def handleExtendedCalls(callsign):
    """handles complexer callsigns with occurences of /"""
    if VERBOSE >= DEBUG:
        print('{} is an extended callsign'.format(callsign))
    callsign_parts = callsign.split('/')
    # Callsign has to parts, example 5B/DL8BH
    if len(callsign_parts) == 2:
        if VERBOSE >= DEBUG:
            print('callsign has 2 parts')
        prefix = callsign_parts[0]
        suffix = callsign_parts[1]
        if suffix in ['MM', 'MM1', 'MM2', 'MM3', 'AM']:
            return False
        # only one character of suffix: DL8BH/P DL8BH/1
        if len(suffix) == 1:
            if suffix in ['M', 'P'] and not re.match(r'^LU', prefix):
                return prefix
            # KL7AA/1 -> W1
            if re.match(r'[0-9]', suffix[0]):
                if VERBOSE >= DEBUG:
                    print('{} matches pattern KL7AA/1'.format(callsign))
                if re.match(r'^A[A-L]|^[KWN]',prefix):
                    print('resulting callsign is: {}'.format('W{}'.format(suffix[0])))
                    return 'W{}'.format(suffix[0])
                # RA1AAA/2 -> RA2AAA
                else:
                    prefix_to_list = list(prefix)
                    prefix_to_list[2] = suffix[0]
                    prefix = ''.join(prefix_to_list)
                    if VERBOSE >= DEBUG:
                        print('resulting callsign is: {}'.format(prefix))
                    return prefix
            # handle special suffixes from argentina
            elif re.match(r'^[A-DEHJL-VX-Z]', suffix):
                if VERBOSE >= DEBUG:
                    print('{} suffix from argentina?'.format(callsign))
                # list of argenitian prefixes AY, AZ, LO-LW
                if re.match(r'^(AY|AZ|L[O-W])', prefix):
                    # LU1ABC/z -> LU1zAB
                    prefix_to_list = list(prefix)
                    prefix_to_list[3] = suffix
                    prefix = ''.join(prefix_to_list)
                    print('resulting callsign is: {}'.format(prefix))
                    return prefix
                else:
                    return callsign
        if len(prefix) <= 3 < len(suffix):
            return prefix
        if 1 < len(suffix) < 5:
            if suffix in ['QRP', 'QRPP']:
                return prefix
            else:
                return prefix

    elif len(callsign_parts) == 3:
        if VERBOSE >= DEBUG:
            print('callsign has 3 parts')
        prefix = callsign_parts[0]
        middle = callsign_parts[1]
        suffix = callsign_parts[2]
        # maritime mobile and aeronautic mobile is not valid for DXCC
        if suffix in ['MM', 'AM']:
            return False
        if suffix in ['M', 'QRP', 'P']:
            return handleExtendedCalls('{}/{}'.format(prefix, middle))
        if len(middle) > 0:
            # KL7AA/1/M -> W1
            if re.match(r'[0-9]', middle[0]):
                if VERBOSE >= DEBUG:
                    print('{} matches pattern KL7AA/1/M'.format(callsign))
                if re.match(r'^A[A-L]|^[KWN]',prefix):
                    return 'W{}'.format(middle[0])
                # RA1AAA/2/M -> RA2AAA
                else:
                    prefix_to_list = list(prefix)
                    prefix_to_list[2] = middle[0]
                    prefix = ''.join(prefix_to_list)
                    if VERBOSE >= DEBUG:
                        print('resulting callsign is: {}'.format(prefix))
                    return prefix
        # Fuzzy match for implausible suffixes like MM0/DL8BH/FOO
        if len(middle) > len(prefix) and len(middle) > len(suffix) and handleExtendedCalls(prefix + '/' + middle) != None:
            return handleExtendedCalls(prefix + '/' + suffix)
        else:
             return None


GLOBAL_DXCC_LIST = {}
init_country_tab(None)
for pattern in GLOBAL_DXCC_LIST:
    print(pattern)
from timeit import default_timer as timer
start = timer()
print(call2dxcc('DL/ZL1IO', None))
print(call2dxcc('DP1POL', None))
print(dxcc2json(call2dxcc('DL0ABC', None)))
end = timer()
print(end - start)

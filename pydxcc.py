#!/usr/bin/python3
"""simple dxcc-resolution program to be used with cqrlogs dxcc-tables"""
import csv
import re
from collections import OrderedDict
from datetime import datetime
DEBUG = 3
TRACE1 = 4
TRACE2 = 5
VERBOSE = 3

def pattern_to_regex(patternlist):
    """transform pattern from file to regex"""
    # = is the hint in country.tab, that an explicit call is given
    returnlist = []
    patternlist = patternlist.replace('  ', ' ')
    for pattern in patternlist.split(' '):
        pattern = pattern.replace('%', '[A-Z]').replace('#', '[0-9]')
        pattern += '$'
        pattern = '^' + pattern
        returnlist.append(pattern)
    return returnlist
        

def init_country_tab():
    """initializes a dict with data from the dxcc-tables from file"""
    date_dxcc_regex = re.compile(r'((?P<from>\d\d\d\d/\d\d/\d\d)*-(?P<to>\d\d\d\d/\d\d/\d\d)*)*(=(?P<alt_dxcc>\d*))*')
    with open("/home/bernhard/.config/cqrlog/dxcc_data/country.tab", "r") as countrytab:
        # split country.tab to list linewise
        countrytabcsv = csv.reader(countrytab, delimiter='|')
        dxcc_list = OrderedDict()
        for row in countrytabcsv:
            row_list = list(row)
            # only check Regexp-Entries
            # if row_list[9] == "R":
            if True:
                indaterange = True
                date_dxcc_string = date_dxcc_regex.search(row_list[10])
                dateto = None
                datefrom = None
                # check, if timerange is (partly) given
                if date_dxcc_string.group('to'):
                    dateto = datetime.strptime(date_dxcc_string.group('to'), '%Y/%m/%d')
                if indaterange and date_dxcc_string.group('from'):
                    datefrom = datetime.strptime(date_dxcc_string.group('from'), '%Y/%m/%d')
                pattern = row_list[0]
                attributes = {
                    'name' : row_list[1],
                    'continent' : row_list[2],
                    'utc_offset' : row_list[3],
                    'coord_n' : row_list[4],
                    'coord_e' : row_list[5],
                    'itu' : row_list[6],
                    'waz' : row_list[7],
                    'valid_from' : datefrom,
                    'valid_to' : dateto,
                    'alt_dxcc' : date_dxcc_string.group('alt_dxcc')
                }
                for singlepattern in pattern_to_regex(pattern.strip()):
                    dxcc_list[singlepattern] = attributes
    if VERBOSE >= DEBUG:
        print("{} calls parsed".format(len(dxcc_list)))
    return dxcc_list


def call2dxcc(callsign, date = None):
    """does the job in resolving the callsign"""
    # if date is not given, assume date is now
    if not date:
        date = datetime.utcnow()
    direct_hit_list = {}
    regex_hit_list = OrderedDict()
    for pattern in DXCC_LIST:
        indaterange = True
        valid_to = DXCC_LIST[pattern]['valid_to']
        valid_from = DXCC_LIST[pattern]['valid_from']
        if valid_to is not None:
            if date > valid_to:
                indaterange = False
        if indaterange and not valid_from is None:
            if date < valid_from:
                indaterange = False
        # if in the valid date range, build two lists, one complete call hits
        # one with the regex hits
        if indaterange:
            if "=" in pattern:
                direct_hit_list[pattern.replace('=', '')] = DXCC_LIST[pattern]
            else:
                regex_hit_list[pattern] = DXCC_LIST[pattern]
    # chech for direct hits
    for pattern in direct_hit_list:
        if re.match(pattern, callsign):
            if VERBOSE >= DEBUG:
                print("found direct hit {} {}".format(pattern, DXCC_LIST[pattern]))
            return [pattern, DXCC_LIST[pattern]]
    # check for portable calls, after testing for direct hits
    if '/' in callsign:
        callsign = handleExtendedCalls(callsign)
    # check for regex hits
    for pattern in regex_hit_list:
        if pattern[1] in [callsign[0],'[']:                    
            if VERBOSE >= TRACE1:
                print(pattern)
            if re.match(pattern, callsign):
                if VERBOSE >= DEBUG:
                    print("found {} {}".format(pattern, DXCC_LIST[pattern]))
                return [pattern, DXCC_LIST[pattern]]

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

DXCC_LIST = init_country_tab()
#for pattern in DXCC_LIST:
#    print(pattern)
from timeit import default_timer as timer
start = timer()
print(call2dxcc('DL', None))
end = timer()
print(end - start)      
#!/usr/bin/python3.5
"""simple dxcc-resolution program to be used with cqrlogs dxcc-tables"""
import csv
import re
from datetime import datetime
DEBUG = 3
TRACE1 = 4
TRACE2 = 5
VERBOSE = DEBUG

def pattern_to_regex(pattern):
    """transform pattern from file to regex"""
    # = is the hint in country.tab, that an explicit call is given
    if '=' in pattern:
        pattern = pattern.replace('  ', ' ').replace('%', '[A-Z]').replace('#', '[0-9]').replace(' ', '$|^').replace('=', '')
        if not pattern.endswith('$'):
            pattern += '$'
    # regex else
    else:
        pattern = pattern.replace('  ', ' ').replace('%', '[A-Z]').replace('#', '[0-9]').replace(' ', '|^').replace('=', '')
    if not pattern[0] == '^':
        pattern = '^' + pattern
    return pattern

def init_country_tab():
    """initializes a dict with data from the dxcc-tables from file"""
    date_dxcc_regex = re.compile(r'((?P<from>\d\d\d\d/\d\d/\d\d)*-(?P<to>\d\d\d\d/\d\d/\d\d)*)*(=(?P<alt_dxcc>\d*))*')
    with open("/home/bernhard/.config/cqrlog/dxcc_data/country.tab", "r") as countrytab:
        # split country.tab to list linewise
        countrytabcsv = csv.reader(countrytab, delimiter='|')
        dxcc_list = {}
        for row in countrytabcsv:
            row_list = list(row)
            # only check Regexp-Entries
            if row_list[9] == "R":
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
                dxcc_list[pattern_to_regex(pattern.strip())] = attributes
    if VERBOSE >= DEBUG:
        print("{} calls parsed".format(len(dxcc_list)))
    return dxcc_list


def call2dxcc(callsign, date):
    """does the job in resolving the callsign"""
    # if date is not given, assume date is now
    if not date:
        date = datetime.utcnow()
    if '/' in callsign:
        callsign = handleExtendedCalls(callsign)
    direct_hit_list = {}
    regex_hit_list = {}
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
            if "$" in pattern:
                direct_hit_list[pattern] = DXCC_LIST[pattern]
            else:
                regex_hit_list[pattern] = DXCC_LIST[pattern]
    # chech for direct hits
    for pattern in direct_hit_list:
        if re.match(pattern, callsign):
            if VERBOSE >= DEBUG:
                print("found direct hit {} {}".format(pattern, DXCC_LIST[pattern]))
            return [pattern, DXCC_LIST[pattern]]
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
                    return 'W{}'.format(suffix[0])
                else:
                    prefix_to_list = list(prefix)
                    prefix_to_list[2] = suffix[0]
                    prefix = ''.join(prefix_to_list)
                    if VERBOSE >= DEBUG:
                        print('resulting callsign is: {}'.format(prefix))
                    return prefix
            # handle special suffixes from argentinia
            elif re.match(r'^[A-DEHJL-VX-Z]', suffix):
                if VERBOSE >= DEBUG:
                    print('{} suffix from argentinia?'.format(callsign))
                # list of argenitian prefixes AY, AZ, LO-LW
                if re.match(r'^(AY|AZ|L[O-W])', prefix):
                    # LU1ABC/z -> LU1zAB
                    prefix_to_list = list(prefix)
                    prefix_to_list[3] = suffix
                    prefix = ''.join(prefix_to_list)
                    return prefix
                else:
                    return callsign
                
    elif len(callsign_parts) == 3:
        if VERBOSE >= DEBUG:
            print('callsign has 3 parts')
        
DXCC_LIST = init_country_tab()
call2dxcc('LU1ABC/M', None)

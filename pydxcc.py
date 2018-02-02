#!/usr/bin/python3.5
"""simple dxcc-resolution program to be used with cqrlogs dxcc-tables"""
import csv
import re
from datetime import datetime
DEBUG = False

def pattern_to_regex(pattern):
    """transform pattern from file to regex"""
    pattern = pattern.replace('  ', ' ').replace('%', '[A-Z]').replace('#', '[0-9]').replace(' ', '$|^').replace('=', '')
    if not pattern.endswith('$'):
        pattern += '$'
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
    return dxcc_list


def call2dxcc(callsign, date):
    """does the job in resolving the callsign"""
    # if date is not given, assume date is now
    if not date:
        date = datetime.utcnow()
    if '/' in callsign:
        callsign = handleExtendedCalls(callsign)
    for pattern in DXCC_LIST:
        indaterange = True
        valid_to = DXCC_LIST[pattern]['valid_to']
        valid_from = DXCC_LIST[pattern]['valid_from']
        #print(valid_from)
        if valid_to is not None:
            if date > valid_to:
                indaterange = False
        if indaterange and not valid_from is None:
            if date < valid_from:
                indaterange = False
        if indaterange:
            print(pattern)
            # chech for direct hits
            if pattern.startswith('^'):
                if re.match(pattern, callsign):
                    if DEBUG:
                        print("found {} {}".format(pattern, DXCC_LIST[pattern]))
                    return [pattern, DXCC_LIST[pattern]]
            # check for regex hits
            if pattern.startswith(callsign[0]) or pattern.startswith('['):
                if re.match(pattern, callsign):
                    if DEBUG:
                        print("found {} {}".format(pattern, DXCC_LIST[pattern]))
                    return [pattern, DXCC_LIST[pattern]]

def handleExtendedCalls(callsign):
    """handles complexer callsigns with occurences of /"""
    callsign_parts = callsign.split('/')
    # Callsign has to parts, example 5B/DL8BH
    if len(callsign_parts) == 2:
        prefix = callsign_parts[0]
        suffix = callsign_parts[1]
        print(suffix)
        if suffix in ['MM', 'MM1', 'MM2', 'MM3', 'AM']:
            return False
        if re.match(r'[0-9]', suffix[0]):
            print('foo')
            if re.match(r'^A[A-L]|^[KWN]',prefix):
                return 'W{}'.format(suffix[0])
        else:
            prefix[2] = suffix[0]
            return prefix

DXCC_LIST = init_country_tab()

#print(handleExtendedCalls('W7ABC/2'))
call2dxcc('W7ABC/2', None)

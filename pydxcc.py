#!/usr/bin/python3.5
"""simple dxcc-resolution program to be used with cqrlogs dxcc-tables"""
import csv
import re
from datetime import datetime
def pattern_to_regex(pattern):
    """transform pattern from file to regex"""
    pattern = pattern.replace('  ', ' ').replace('%', '[A-Z]').replace('#', '[0-9]').replace(' ', '$|')
    if not pattern.endswith('$'):
        pattern += '$'
    return pattern

def init_country_tab(date):
    """initializes a dict with data from the dxcc-tables from file"""
    # if date is not given, assume date is now
    if not date:
        date = datetime.utcnow()
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
                # check, if in valid timerange
                if date_dxcc_string.group('to'):
                    dateto = datetime.strptime(date_dxcc_string.group('to'), '%Y/%m/%d')
                    if date > dateto:
                        indaterange = False
                if indaterange and date_dxcc_string.group('from'):
                    print(indaterange)
                    datefrom = datetime.strptime(date_dxcc_string.group('from'), '%Y/%m/%d')
                    if date < datefrom:
                        indaterange = False
                if indaterange:
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



DXCC_LIST = init_country_tab(None)
for x in DXCC_LIST:
    if re.match(x, 'DA0HQ'):
        print("found {} {}".format(x, DXCC_LIST[x]))

#!/usr/bin/env python
'''
GPX to JSON Converter for "pocket queries" from geocaching.com (zip files)

by matthias schneider

http://beached.org
http://github.com/dermatthias

'''

import sys
import xml.dom.minidom as dom
import json
import zipfile
import re
import StringIO

def quit(message):
    print >> sys.stderr, message
    if __name__ == "__main__":
        sys.exit(1)

ctid_dic = {'Geocache|Unknown Cache': 8,
                    'Geocache|Traditional Cache': 2,
                    'Geocache|Multi-cache': 3,
                    'Geocache|Letterbox Hybrid': 5,
                    'Geocache|Webcam Cache': 11,
                    'Geocache|Virtual Cache': 4,
                    'Geocache|Event Cache': 6,
                    'Geocache|Mega-Event Cache': 453,
                    'Geocache|Earthcache': 137,
                    'Geocache|Cache In Trash Out Event': 13,
                    'Geocache|Wherigo Cache': 1858,
                    }

def main():
    if len(sys.argv) != 2:
        quit('error, wrong number of arguments')

    in_file = sys.argv[1]
    if zipfile.is_zipfile(in_file):
        zip_file = zipfile.ZipFile(in_file)
        regex_normal = re.compile('^.*[^-][^w][^p][^t][^s]\.gpx$')
        for name in zip_file.namelist():
            result = regex_normal.search(name)
            if result:
                gpx_filename = result.group()
        gpx_file = zip_file.open(gpx_filename)
    else:
        quit('error, input not a zip file')


    # parse gpx, remove \r from gpx first
    gpx_file_cleaned = StringIO.StringIO()
    for line in gpx_file:
        cline = line.rstrip('\r')
        gpx_file_cleaned.write(cline)            
    gpx_file.close()
    
    gpx_file_cleaned.seek(0)
    # parse
    gpx = dom.parse(gpx_file_cleaned)

    # search for wpt nodes
    all_wpts = []
    for entry in gpx.firstChild.getElementsByTagName('wpt'):
        all_wpts.append(generateWpt(entry))

    json_dic = {'wpts': all_wpts}

    # meta data at top of file
    for entry in gpx.firstChild.childNodes:
        if entry.nodeType != 3 and entry.nodeName != 'wpt':
            if entry.firstChild:
                json_dic[entry.nodeName] = entry.firstChild.nodeValue
            else:
                json_dic[entry.nodeName] = 'intentionally_left_blank'

    # json export
    json_data = json.dumps(json_dic)
    f = open(sys.argv[1].replace('.zip','.json'), 'w')
    f.write(json_data)
    f.close()

    return 0


def generateWpt(wpt):
    d = {}
    # add attributes
    if wpt.nodeType != 3 and wpt.nodeName != 'groundspeak:cache':
        d['lat'] = float(wpt.getAttribute('lat'))
        d['lon'] = float(wpt.getAttribute('lon'))

    for e in wpt.childNodes:
        if e.nodeType != 3:
            # recursive call
            if e.nodeName == 'groundspeak:cache':
                d['id'] = int(e.getAttribute('id'))
                d[e.nodeName.replace(':', '_')] = generateWpt(e)
            # or not
            else:
                name = e.nodeName.replace(':', '_')
                if e.firstChild:
                    if name == 'type':
                        d['ctid'] = ctid_dic[e.firstChild.nodeValue]
                    else:
                        value = e.firstChild.nodeValue                        
                else:
                    value = ''

                if name == 'groundspeak_long_description':
                    d[name] = value.strip()
                else:
                    d[name] = value.strip()
    return d

if __name__ == "__main__":
        sys.exit(main())

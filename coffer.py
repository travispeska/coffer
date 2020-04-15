#!/usr/bin/env python3

import os
import re
import sys
import json
import requests
import optparse
from ast import literal_eval
from datetime import datetime,timedelta
from pathlib import Path
path = Path(__file__).parent

OUI_URI='http://standards-oui.ieee.org/oui.txt'
COFFER_DB = '{0}/._coffer.db'.format(path)

global oui_dict
try:
  oui_dict = literal_eval(open(COFFER_DB,'r').readlines()[1].split(' = ')[1])
except Exception as e:
  oui_dict = {}

NO_FORMAT = '([a-f0-9]{12})'
NORMAL_FORMAT = '(([a-f0-9]{2}[-:]){5}[a-f0-9]{2})'
CISCO_FORMAT = '(([a-f0-9]{4}\.){2}[a-f0-9]{4})'
pattern = re.compile('|'.join([NO_FORMAT, NORMAL_FORMAT, CISCO_FORMAT]))

def checkDB(skip):
  if not os.path.isfile(COFFER_DB):
    print('No Database exists. Creating {0} database'.format(COFFER_DB))
    updateDB()
  if skip:
    return
  else:
    last_update = open(COFFER_DB,'r').readline().split(' = ')[1].rstrip()
    difference = datetime.now() - datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S.%f')
    print('Database last updated: {}'.format(last_update))
    if difference < timedelta(days=7):
      return
    else:
      updateDB()

def updateDB():
  print('Pulling Most Up-to-date OUI Database')
  res = requests.get(OUI_URI).text
  for line in res.split('\r\n'):
    if '(base 16)' in line:
      oui = line.split('(base 16)')[0].lstrip().rstrip().lower()
      vendor = line.split('(base 16)')[1].lstrip().rstrip()
      if oui not in oui_dict:
        oui_dict[oui] = vendor

  time_now = datetime.now()
  with open(COFFER_DB, 'w') as db:
    db.write('last_update = {0}\n'.format(time_now))
    db.write('db = {0}'.format(oui_dict))

def parseMac(line):
  m = pattern.search(line)
  if m:
    mac = ''.join(re.split('[-:\.]', m.group(0)))
    oui = mac[:6]
    mac = ':'.join(mac[i:i+2] for i in range(0, len(mac), 2))
    print('{0}\t{1}'.format(mac, oui_dict.get(oui, 'Unknown')))

def getInput():
  data = []
  print('Paste MAC addresses here, one per line')
  print('Press Ctrl+D when finished adding MACs')
  print('======================================')
  try:
    while True:
      data.append(input())
  except EOFError:
    print('======================================')
    return data

def buildParser():
  parser = optparse.OptionParser(usage='%prog [options]', description='Pulls out MAC addresses and identifies OUIs.')
  parser.add_option('-i', '--input', action='store', dest='file', help='File to ingest.')
  parser.add_option('-u', '--update-only', action='store_true', default=False, dest='update', help='Update the database only.')
  parser.add_option('-s', '--skip-update', action='store_true', default=False, dest='skip', help='Do not upgrade the database.')
  parser.add_option('-f', '--force-update', action='store_true', default=False, dest='force', help='Force upgrade of the database.')
  return parser

def main(argv):
  parser = buildParser()
  opts, args = parser.parse_args(argv)
  if opts.update:
    updateDB()
  elif opts.force:
    updateDB()
    data = getInput()
    for line in data:
      parseMac(line.lower())
  else:
    checkDB(opts.skip)
    data = getInput()
    for line in data:
      parseMac(line.lower())


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))

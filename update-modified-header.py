#!/usr/bin/python2
##############################################################################
#
# $RCSfile: update-modified-header.py $
# $Revision: 1.15 $
# $Date: 16-01-2021 17:11:47 $
# $Author: Jason <jason@seagate.com> $
# $Source: hooks/update-modified-header.py $
#
#  Pre-commit hook for updating the file header
#  Command: git config --local core.hooksPath $(pwd)/hooks
#
##############################################################################

from datetime import datetime

import os
import mmap
import sys
import subprocess
import time
import re

def modifiedfiles():
  fnl = []
  args = ['git', 'diff', 'HEAD', '--name-only', '-r', '--diff-filter=M']
  with open(os.devnull, 'w') as bb:
      fnl = subprocess.check_output(args, stderr=bb).splitlines()
      
  fnl = [i for i in fnl if os.path.isfile(i)]
  return fnl


def updateRevision(line):
    strVer = line.split("$Revision: ")[1].split()[0]
    version = [x for x in strVer.split('.')]

    ver = [int(i) for i in version]

    if ver[1] == 99:
      ver[0] += 1
      ver[1] = 0
    else:
      ver[1] += 1

    strVer = "%d.%02d" % (ver[0], ver[1])
    return str.replace(line, line.split("$Revision: ")[1].split()[0], strVer)


def main(args):
  filelist = modifiedfiles()
  for fn in filelist:
    lines = open(fn).readlines()
    
    i = 0
    for line in lines:
        if '$Revision:' in line:
          lines[i] = updateRevision(line)            
        i += 1
   
    with open(fn, 'w') as r:
      r.writelines(lines)


  args = ['git', 'add', '.']
  subprocess.call(args)
  
  
if __name__ == '__main__':
    main(sys.argv)


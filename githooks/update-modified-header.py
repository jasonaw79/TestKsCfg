#!/usr/bin/env fofpython
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

def checkfor(args):
  if isinstance(args, str):
    if ' ' in args:
      raise ValueError('No spaces in single command allowed.')
    args = [args]
  try:
    with open(os.devnull, 'w') as bb:
      subprocess.check_call(args, stdout=bb, stderr=bb)
  except subprocess.CalledProcessError:
    print("Required program '{}' not found! exiting.".format(args[0]))
    sys.exit(1)

def modifiedfiles():
  fnl = []
  try:
    args = ['git', 'diff', 'HEAD', '--name-only', '-r', '--diff-filter=M']
    with open(os.devnull, 'w') as bb:
      fnl = subprocess.check_output(args, stderr=bb).splitlines()
      # Deal with unmodified repositories
      if len(fnl) == 1 and fnl[0] is 'clean':
        return []
  except subprocess.CalledProcessError as e:
    if e.returncode == 128: # new repository
      args = ['git', 'ls-files']
      with open(os.devnull, 'w') as bb:
        fnl = subprocess.check_output(args, stderr=bb).splitlines()
  # Only return regular files.
  fnl = [i for i in fnl if os.path.isfile(i)]
  print("Modified files list:")
  print(fnl)
  return fnl

def keywordfiles(fns):
  datekw = '$Date'.encode()
  revkw = '$Revision'.encode()
  authorkw = '$Author'.encode()

  rv = []
  for fn in fns:
    with open(fn, 'rb') as f:
      try:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        if mm.find(datekw) > -1 or mm.find(revkw) > -1 or mm.find(authorkw) > -1:
          rv.append(fn)
        mm.close()
      except ValueError:
        pass
  print("Files with keyword:")
  print(rv)
  return rv

def gitdate(line):
  now = datetime.now()

  strDate = now.strftime("%d-%m-%Y %H:%M:%S")
  return str.replace(line, line.split("$Date: ")[1], strDate) + ' $\n'
    

def gitauthor(line):
  try:
    args = ['git', 'var', 'GIT_AUTHOR_IDENT']

    author = subprocess.check_output(args, universal_newlines=True).split(' ')
    
    strAuthor = '%s %s' % (author[0], author[1])
    return str.replace(line, line.split("$Author: ")[1], strAuthor) + ' $\n'
  except IndexError:
    raise ValueError('Author not found in git output')

def updateRevision(line):
  try:
    strVer = line.split("$Revision: ")[1].split()[0]
    version = [x for x in strVer.split('.')]

    digit = len(version[1])
    ver = [int(i) for i in version]

    if ver[1] == 99:
      ver[0] += 1
      ver[1] = 0
    else:
      ver[1] += 1

    if digit == 1:
      strVer = "%d.%d" % (ver[0], ver[1])
    else:
      strVer = "%d.%02d" % (ver[0], ver[1])

    return str.replace(line, line.split("$Revision: ")[1].split()[0], strVer)

  except IndexError:
    raise ValueError('Revision not found in file header')

def main(args):
  print("Running update-modified-header.py")
  checkfor(['git', '--version'])
  if not os.access('.git', os.F_OK):
    print('No .git directory found!')
    sys.exit(1)
  print('{}: Updating modified files.'.format(args[0]))
  # Get modified files
  files = modifiedfiles()
  if not files:
    print('{}: Nothing to do.'.format(args[0]))
    sys.exit(0)
  files.sort()

  # Find files that have keywords in them
  kwfn = keywordfiles(files)
  for fn in kwfn:
    myfile_list = open(fn).readlines()
    newList = []

    idx = 0
    total = 0
    for line in myfile_list:
      if line and line.startswith("#"):
        if '$Revision:' in line:
          myfile_list[idx] = updateRevision(line)
          print("Updated:", myfile_list[idx])
          total += 1
        elif "$Date:" in line:
          myfile_list[idx] = gitdate(line)
          print("Updated:", myfile_list[idx])
          total += 1
        elif "$Author:" in line:
          myfile_list[idx] = gitauthor(line)
          print("Updated:", myfile_list[idx])
          total += 1
        
        if total == 3:
          break
        
        idx += 1
      
      elif line and not line.startswith("#"):
        break

    # Only re-write if we updated something
    if total:
       with open(fn, 'w') as r:
          r.writelines(myfile_list)
          

  #args = ['git', 'add'] + kwfn
  args = ['git', 'add', '.']
  subprocess.call(args)
  print("Re-add modified file(s)")
  
if __name__ == '__main__':
    main(sys.argv)


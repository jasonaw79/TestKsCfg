
from datetime import datetime

import os
import mmap
import sys
import subprocess


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
        version = [int(x) for x in strVer.split('.')]

        if version[1] == 99:
            version[0] += 1
            version[1] = 0
        else:
            version[1] += 1

        strVer = "%d.%02d" % (version[0], version[1])
        return str.replace(line, line.split("$Revision: ")[1].split()[0], strVer)

    except IndexError:
        raise ValueError('Revision not found in file header')

def main(args):
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
        for line in myfile_list:
            if '$Revision:' in line:
                newList.append(updateRevision(line))
            elif "$Date:" in line:
                newList.append(gitdate(line))
            elif "$Author:" in line:
                newList.append(gitauthor(line))
            else:
                newList.append(line)

        with open(fn, 'w') as r:
            for line in newList:
                r.writelines(line)

    args = ['git', 'add'] + kwfn
    subprocess.call(args)

if __name__ == '__main__':
    main(sys.argv)

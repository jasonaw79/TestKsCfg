# $Revision: 1.05 $
# $Date: 05-11-2020 04:32:15 $
# $Author: Jason <lam.aw@seagate.com> $
#


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
        args = ['git', 'diff-tree', '--no-commit-id', '--name-only', '-r', '${{ github.sha }}']
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
    print(files)

if __name__ == '__main__':
    main(sys.argv)

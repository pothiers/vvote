#!/bin/bash -e

#!SCRIPT=$(readlink -f $0)        # Absolute path to this script
#!SCRIPTPATH=$(dirname $SCRIPT)   # Absolute path this script is in
SCRIPTPATH=`dirname $0`  # works on MacOS, I hope

PROJDIR=$SCRIPTPATH
installprefix="$PROJDIR/venv"

pushd $PROJDIR > /dev/null
source $PROJDIR/venv/bin/activate
pip install -r $PROJDIR/requirements.txt
pylint -E vvote/
pylintstatus=$?
if [ $pylintstatus -eq 1 ]; then
    echo "pylint FATAL message for VVOTE"
    exit 1
fi
if [ $pylintstatus -eq 2 ]; then
    echo "pylint ERROR message for VVOTE"
    exit 2
fi
if [ $pylintstatus -gt 0 ]; then
    echo "pylint returned non-zero status for VVOTE"
    exit 2
fi

python setup.py install --force --prefix $installprefix

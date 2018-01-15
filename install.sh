#!/bin/bash

installprefix=~/sandbox/vvote/venv
repodir=${1:-$HOME/sandbox}

pushd $repodir/vvote > /dev/null
source ~/sandbox/vvote/venv/bin/activate
pip install -r ~/sandbox/vvote/requirements.txt
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

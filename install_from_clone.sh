#!/bin/bash
# After git clone (or pull), run this to install CLI.
#
# Requirements:
#   python3
#
SCRIPT=$(readlink -f $0)        # Absolute path to this script
repodir=$(dirname $SCRIPT)   # Absolute path this script is in

installprefix=$repodir/venv

pushd $repodir > /dev/null

python3 -m venv --without-pip venv
source venv/bin/activate
curl https://bootstrap.pypa.io/get-pip.py | python
deactivate
source venv/bin/activate

pip install -r $repodir/requirements.txt
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

python3 setup.py install --force --prefix $installprefix


echo "VVOTE installed."
echo "You can now do:"
echo "  source $repodir/venv/bin/activate"
echo "  cli"

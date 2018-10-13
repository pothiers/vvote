#!/bin/sh
# Run ALL vvote tests.  
# 

cd ~/sandbox/vvote/vvote
python -m unittest tests/test_cli.py

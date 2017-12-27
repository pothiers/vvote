# vvote [![Build Status](https://travis-ci.org/pothiers/vvote.svg?branch=master)](https://travis-ci.org/pothiers/vvote)
Vote counting and data validation

Given XSL file representing data from ballots: count votes for
multiple races, handle out-of-district, overvote, undervote, write-in,
handle various edge cases.


"python3 setup.py install" will install programs:
- countvote :: count ballots
- sovc :: Extract from Statement Of Votes Cast (SOVC) 
- transpose :: Transpose rows/columns from one Excel file to another
- genmap :: Create string mapping (SOVC to CVR)

All programs can be run with "--help" option (e.g. "countvote --help") to get
more help.



After installing (from master branch), you should always be able to execute
"tests/smoke/smoke.all.sh" and get a message: "ALL smoke tests PASSED".
If not, there is a problem and it should be reported.


I suggest using Anaconda (https://docs.anaconda.com/) to install lots
of python goodies including data analysis packages.
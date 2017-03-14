#!/bin/bash

for prog in countvote sovc transpose genmap xls2csv
do
    $prog --help
    echo
    echo "########################"
done

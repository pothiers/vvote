#! /usr/bin/env python
"""Manage CVR database.
- Load from Official Election Results excel file(s).
- Export as CSV. 

LVR :: List of CVR records (an excel file, each row is CVR except
     header row=1) Each record is the ballot results from one person.

Underlying dimensionality of LVR Data (value is Choice(string)):
1. CVR
2. Race
"""

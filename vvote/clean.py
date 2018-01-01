#!/usr/bin/python
# -*- coding: latin-1 -*-
"""\
Transformations to make LVR strings (Race and Choice titles) more like SOVC
strings.
"""

import copy

def rem_party(name):
    """Remove Party prefix from start of name."""
    party_prefixs = ['DEM ', 'REP ', 'GRN ', 'LBT ']
    if name[:4] in party_prefixs:
        return name[4:]
    else:
        return name


replace_strs = [
    #LVR        SOVC
    ('Á',        'A'),
    ('Í',        'I'),
    ('Ó',        'O'),
    ('Ú',        'U'),
    ('YES/SÍ',   'YES'),
    ('YES/Sí',   'YES'),
    ('YES/SI',   'YES'),
]


# Normalize differentces between LVR and SOVC choices
# LVR may contain unicode
def clean_races(lut):
    """Normalize dict of races.  
lut[raceId] => newRaceTitle
RETURN: [(raceId,newRaceTitle), ...];  Sorted by TITLE.
"""
    newlut = copy.copy(lut) # newlut[cid] => title
    #
    # (no change)
    #
    return sorted(newlut.items(), key=lambda x: x[1])    

# Normalize differentces between LVR and SOVC choices
# LVR may contain unicode
def clean_choices(lut):
    """Normalize dict of choices.
lut[choiceId] => newChoiceTitle
RETURN: [(choiceId,newChoiceTitle), ...];  Sorted by TITLE.
"""
    newlut = copy.copy(lut) # newlut[cid] => title
    # remove chars: parens, double-quotes
    nukechars = str.maketrans(dict.fromkeys('()"'))
    #! ('overvote', 'OVER VOTES'),
    #! ('undervote','UNDER VOTES'),
    #! ('Write-in', 'WRITE-IN'),

    for k in lut.keys():
        newlut[k] = rem_party(newlut[k])
        newlut[k] = newlut[k].translate(nukechars)
        for (a,b) in replace_strs:
            newlut[k] = newlut[k].replace(a,b)
    return sorted(newlut.items(), key=lambda x: x[1])


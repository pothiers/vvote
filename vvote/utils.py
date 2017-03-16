import csv

def read_lut(racemap):
    lut = dict() # dict[sovc_title] => lvr_title
    
    with open(racemap) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            lut[row['SOVC']] = row['LVR']
    return lut

def invert_lut(lut):
    invlut = dict()
    for k,v in lut.items():
        assert v not in invlut
        invlut[v] = k

Installing and Running VVOTE

* Installing

cd $HOME/sandbox
git clone https://github.com/pothiers/vvote.git"
cd vvote
python3 -m venv $HOME/sandbox/vvote/venv
source $HOME/sandbox/vvote/venv/bin/activate
./install.sh


* Running

export PATH=$HOME/sandbox/vvote/scripts:$PATH

edata="/data/vvote/Elections/Primary2018/PCE/vv"
lvrdb -s $edata/P-2018-CRV-?.csv

count-totals.sh

count-race.sh "U.S. SENATOR DEM"

sqlite3 -header -column LVR.db "select precinct from cvr" | head
count-precinct.sh 249

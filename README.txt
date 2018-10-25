Installing and Running VVOTE

* Installing

cd $HOME/repos
git clone git@github.com:pothiers/vvote.git
cd vvote
python3 -m venv $HOME/repos/vvote/venv
source $HOME/repos/vvote/venv/bin/activate
./install.sh


* Running

export PATH=$HOME/repos/vvote/scripts:$PATH
edata="/data/vvote/Elections/Primary2018/PCE/vv"

lvrdb -s $edata/P-2018-CRV-?.csv

count-totals.sh

count-race.sh U.S. SENATOR DEM

count-precinct.sh 249

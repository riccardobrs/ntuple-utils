# ntuple-utils

## sumNtuple.py

It merges _*.root_ files where a TNtuple object and a global numbers histogram (TH1F) are stored in. 
 
A config file has to be provided when running the script:

    python sumNtuple.py --cfg configs/ntuple_config.cfg

Output are stored as _*.root_ files by default. If needed, the output can be _.csv_ files (with related _.cfg_ files automatically produced).
 
    python sumNtuple.py --cfg configs/ntuple_config.cfg --csv

To process _.csv_ files, the _text2root.py_ script is provided.

## text2root.py

This executable script needs the directory of _.cfg_ files produced by _sumNtuple.py_ runned with --csv option:
 
    ./text2root.py ../ntuple/configs

The mandatory argument may be provided as a relative path as well as an absolute one.

## extractComponents.py

It process _*.root_ files where a TNtuple object and a global numbers histogram (TH1F) are stored in. For each _*\_SM\_LI\_QU.root_ input file (which contains SM + BSM + SM/BSM interference components) the corresponding  _*\_LI.root_ and _*\_QU.root_ output files can be produced, referred to the SM/BSM interference and BSM components, respectively.

A config file has to be provided when running the script:

    python extractComponents.py --cfg configs/ntuple_config_1D.cfg

Linear/quadratic component extraction can be disabled through _li/qu_ options:

    python extractComponents.py --cfg=configs/ntuple_config_1D.cfg --li=False

To enable the LI/QU parameters estimation by means of a parabolic fit: --fit 
 
More than 3 reweight points are reccomended for the parabolic fit. If fit option is on, a certain number of plots (for each operator) can be saved:

    python extractComponents.py --cfg configs/ntuple_config_1D.cfg --fit --png 100

These plots shows reweights and fit / analyical comparison. Be careful since the execution becomes slower.

## extractInterference.py

Quite similar to _extractComponents.py_: from _*\_SM\_LI\_QU\_IN.root_ to _*\_IN.root_

    python extractComponents.py --cfg configs/ntuple_config_2D.cfg

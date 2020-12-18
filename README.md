# ntuple-utils

## mkNtupleQU.py

It process _*.root_ files where a TNtuple object and a global numbers histogram (TH1F) are stored in. For each _*.root_ input file (which contains SM + BSM + SM/BSM interference components) a corresponding  _*\_QU.root_ output file is produced, referred to the BSM component only.

A config file has to be provided when running the script:

    python mkNtupleQU.py --cfg=configs/ntuple_config.cfg
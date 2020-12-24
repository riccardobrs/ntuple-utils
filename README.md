# ntuple-utils

## extractComponents.py

It process _*.root_ files where a TNtuple object and a global numbers histogram (TH1F) are stored in. For each _*\_SM\_LI\_QU.root_ input file (which contains SM + BSM + SM/BSM interference components) the corresponding  _*\_LI.root_ and _*\_QU.root_ output files can be produced, referred to the SM/BSM interference and BSM components, respectively.

A config file has to be provided when running the script:

    python extractComponents.py --cfg=configs/ntuple_config.cfg

Linear/quadratic component extraction can be disabled through _li/qu_ options:

    python extractComponents.py --cfg=configs/ntuple_config.cfg --li=False


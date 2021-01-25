import ROOT
import argparse
import configparser
from array import array
import sys
import glob
import os
from common.ntupleCommon import getTreeName, writeNtuple


def getEvents (ntuple, variables, eventsList):

    leaves = {k: ntuple.GetLeaf(k) for k in variables}
    
    for i in range(0, ntuple.GetEntries()):

        values = []
        ntuple.GetEntry(i)

        for (key, val) in sorted(leaves.items(), key=lambda x: x[1]):
            values.append(float(val.GetValue ()))

        eventsList.append (array('f', values))

    return eventsList


def writeHisto (name, title, XS, sum_wgt_overall, sum_wgt_passed):

    print ('[INFO] writing global numbers histogram')

    histo = ROOT.TH1F (name, title, 3, 0, 3)
    histo.SetBinContent(1, XS)
    histo.SetBinContent(2, sum_wgt_overall)
    histo.SetBinContent(3, sum_wgt_passed)
    histo.Write()


if __name__ == '__main__':

    print("""
 _______________ 
  Ntuple merger 
 --------------- """)

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('--cfg', dest='config', help='Config .cfg file path containing ntuple infos', required=True)
    args = parser.parse_args()

    cfg = configparser.ConfigParser()
    cfg.readfp(open(args.config, 'r')) # this method will be deprecated

    # retrieve infos from config
    ntupleDir = cfg.get('ntuple', 'dir')
    staticParts = cfg.get('ntuple', 'static').split(',')
    ntupleSuffix = cfg.get('ntuple', 'suffix').strip()
    histoSuffix = cfg.get('histogram', 'suffix').strip()
    histoTitle = cfg.get('histogram', 'title').strip()
    statesIn = cfg.get('tobemerged', 'in').split(',')
    stateOut = cfg.get('tobemerged', 'out').strip()
    operators = cfg.get('operator', 'name').split(',')

    for operator in operators:

        files = [f for f in glob.glob(ntupleDir + '/ntuple*' + ntupleSuffix + '.root') if (operator.strip()+'_') in f]
        toBeSkipped = 0
        for state in statesIn:
            if not any(state.strip() in os.path.basename(f) for f in files):
                toBeSkipped = 1 + toBeSkipped
        if toBeSkipped > 0:
            print ('\n[WARNING] skipping operator {0} because of missing files'.format(operator.strip()))
            continue
        if len(files) > len(statesIn):
            print ('\n[WARNING] skipping operator {0} because of ambiguous files names'.format(operator.strip()))
            continue

        print ('\n[INFO] working on operator ' + operator.strip())

        eventsList = []

        XS = 0.0
        sw_overall = 0.0
        sw_passed = 0.0

        for ntupleFileIn in files:

            ntupleFileIn = ntupleFileIn.strip()
            ntupleNameIn = getTreeName (os.path.basename(ntupleFileIn), staticParts)
            histoNameIn = ntupleNameIn + histoSuffix

            print ('\n[INFO] ntuple file-in   =  ' + ntupleFileIn)
            print ('[INFO] TNtuple name-in  =  ' + ntupleNameIn)
            print ('[INFO] TH1F name-in     =  ' + histoNameIn + '\n')

            f_in = ROOT.TFile (ntupleFileIn, 'READ')
            t = ROOT.gDirectory.Get (ntupleNameIn)
            h = ROOT.gDirectory.Get (histoNameIn)

            leaves = t.GetListOfLeaves()
            vars = [leaves.At(i).GetName() for i in range(0, leaves.GetEntries())]
            vars.sort()

            print ('[INFO] reading ntuple')
            eventsList = getEvents (t, vars, eventsList)

            print ('[INFO] reading global histogram')
            XS = XS + h.GetBinContent(1)
            sw_overall = sw_overall + h.GetBinContent(2)
            sw_passed = sw_passed + h.GetBinContent(3)

            f_in.Close()

        ntupleFileOut = files[0].strip()
        for stIn in statesIn: ntupleFileOut = ntupleFileOut.replace(stIn.strip(), stateOut)
        ntupleNameOut = getTreeName (os.path.basename(ntupleFileOut), staticParts)
        histoNameOut = ntupleNameOut + histoSuffix

        print ('\n[INFO] ntuple file-out  =  ' + ntupleFileOut)
        print ('[INFO] TNtuple name-out =  ' + ntupleNameOut)
        print ('[INFO] TH1F name-out    =  ' + histoNameOut + '\n')
            
        f_out = ROOT.TFile (ntupleFileOut, 'RECREATE')
        writeNtuple (ntupleNameOut, ntupleNameOut, vars, eventsList)
        writeHisto (histoNameOut, histoTitle, XS, sw_overall, sw_passed)
        f_out.Close()

    print ('\n[INFO] end process')
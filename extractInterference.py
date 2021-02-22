import ROOT
import argparse
import configparser
from array import array
import sys
import glob
import os
from common.ntupleCommon import *


def getEvents (ntuple, variables, nominal_wgt, rwgt):

    outevents_in = []

    sum_nominal_weight = 0.
    sum_rwgt_in = 0.

    leaves = {k: ntuple.GetLeaf(k) for k in variables}
    w = ntuple.GetLeaf(nominal_wgt)
    rwgt00 = ntuple.GetLeaf(rwgt['0:0'])
    rwgt10 = ntuple.GetLeaf(rwgt['1:0'])
    rwgt01 = ntuple.GetLeaf(rwgt['0:1'])
    rwgt11 = ntuple.GetLeaf(rwgt['1:1'])

    print ('[INFO] reading SM + LI + QU + IN ntuple')
    
    for i in range(0, ntuple.GetEntries()):

        values_in = []

        ntuple.GetEntry(i)

        sum_nominal_weight += w.GetValue ()
        r00 = rwgt00.GetValue ()
        r10 = rwgt10.GetValue ()
        r01 = rwgt01.GetValue ()
        r11 = rwgt11.GetValue ()

        w_in = r11 + r00 - r10 - r01

        sum_rwgt_in += w_in

        for (key, val) in sorted(leaves.items(), key=lambda x: x[1]):
            if key == nominal_wgt:
                values_in.append(w_in)
            else:
                values_in.append(float(val.GetValue ()))
        outevents_in.append (array('f', values_in))

    print ('[INFO] sum of SM + LI + QU + IN nominal weights: ' + str(sum_nominal_weight))
    print ('[INFO] sum of new IN nominal weights: ' + str(sum_rwgt_in))

    resultsDict = {
        'events_in': outevents_in,
        'sum_nominal_weight': sum_nominal_weight,
        'sum_rwgt_in': sum_rwgt_in,
    }

    return resultsDict


if __name__ == '__main__':

    print("""
 ___________________________________ 
  Extract IN from SM + LI + QU + IN
 ----------------------------------- """)

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('--cfg', dest='config', help='Config .cfg file path containing reweights', required=True)
    args = parser.parse_args()

    cfg = configparser.ConfigParser()
    cfg.readfp(open(args.config, 'r'))

    # retrieve infos from config
    ntupleDir = cfg.get('ntuple', 'dir')
    ntupleDir = ntupleDir + '/' + cfg.get('subdir', 'proc')
    ops1d = cfg.get('operator', 'name').split(',')
    stateOut = cfg.get('tobemerged', 'out').strip()
    staticParts = cfg.get('ntuple', 'static').split(',')
    w = cfg.get('variables', 'nominalwgt').strip()
    ntupleSuffix = cfg.get('ntuple', 'suffix').strip()
    histoSuffix = cfg.get('histogram', 'suffix').strip()
    histoTitle = cfg.get('histogram', 'title').strip()

    # get rwgt lists
    if 'notused' in dict(cfg.items('reweights')).keys():
        notused = cfg.get ('reweights', 'notused').split(',')
    else:
        notused = []
    rwgt_keys, rwgt_used, rwgt_notused, rwgt_dict = rwgtObjects (
        cfg.get ('reweights', 'coupling').split(','),
        cfg.get ('reweights', 'name').split(','),
        notused
    )

    operators = list()
    for x in range(len(ops1d)):
        for y in range(x+1, len(ops1d)):
            operators.append('{0}_{1}'.format(ops1d[x].strip(),ops1d[y].strip()))

    files = [f for f in glob.glob(ntupleDir + '/ntuple*' + ntupleSuffix + '.root') if stateOut in f]
    
    for ntupleFileIn in files:

        if not any(op.strip() in os.path.basename(ntupleFileIn)
            for op in operators) : continue

        ntupleFileIn = ntupleFileIn.strip()
        ntupleNameIn = getTreeName (os.path.basename(ntupleFileIn), staticParts)
        histoNameIn = ntupleNameIn + histoSuffix

        print ('\n\tNtuple file-in   =  ' + ntupleFileIn)
        print ('\tTNtuple name-in  =  ' + ntupleNameIn)
        print ('\tTH1F name-in     =  ' + histoNameIn + '\n')

        f_in = ROOT.TFile (ntupleFileIn, 'READ')
        t = ROOT.gDirectory.Get (ntupleNameIn)
        h = ROOT.gDirectory.Get (histoNameIn)
        overallXS = h.GetBinContent(1)
        print ('[INFO] overall XS: ' + str(overallXS))
            
        leaves = t.GetListOfLeaves()
        vars_wrwgt = [leaves.At(i).GetName() for i in range(0, leaves.GetEntries())]
        # variables for final ntuple
        vars = [v for v in vars_wrwgt if v not in list(set(rwgt_used)|set(rwgt_notused))]
        vars.sort()

        events_dictionary = getEvents (t, vars, w, rwgt_dict,)

        eventsIN = events_dictionary['events_in']
        SumWgtOld = events_dictionary['sum_nominal_weight']
        SumWgtIN = events_dictionary['sum_rwgt_in']

        f_in.Close()
            
        XS = overallXS * SumWgtIN / SumWgtOld

        ntupleFileOut = ntupleFileIn.replace(ntupleSuffix, '_IN').strip()
        ntupleNameOut = ntupleNameIn.replace(ntupleSuffix, '_IN').strip()
        histoNameOut = ntupleNameOut + histoSuffix

        print ('\n\tNtuple file-out  =  ' + ntupleFileOut)
        print ('\tTNtuple name-out =  ' + ntupleNameOut)
        print ('\tTH1F name-out    =  ' + histoNameOut + '\n')
            
        t = getNtuple (ntupleNameOut, ntupleNameOut, vars, eventsIN)
        h = getHisto (histoNameOut, histoTitle, XS, SumWgtIN, SumWgtIN)

        f_out = ROOT.TFile (ntupleFileOut, 'RECREATE')

        print ('[INFO] writing ROOT file')
        t.Write()
        h.Write()
            
        f_out.Close()

    print ('\n[INFO] end process')
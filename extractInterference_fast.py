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
    rwgt13 = ntuple.GetLeaf(rwgt['1:3'])
    rwgt21 = ntuple.GetLeaf(rwgt['2:1'])
    rwgt02 = ntuple.GetLeaf(rwgt['0:2'])
    rwgt10 = ntuple.GetLeaf(rwgt['1:0'])

    print ('[INFO] reading SM + LI + QU + IN ntuple')
    
    for i in range(0, ntuple.GetEntries()):

        values_in = []

        ntuple.GetEntry(i)

        sum_nominal_weight += w.GetValue ()
        r13 = rwgt13.GetValue ()
        r21 = rwgt21.GetValue ()
        r02 = rwgt02.GetValue ()
        r10 = rwgt10.GetValue ()

        w_in = r13 - r21 - r02 + r10

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
    parser.add_argument('--root', dest='root', help='root file ntuple_$proc_SM_LI_QU_IN.root', required=True)
    args = parser.parse_args()

    file_path = args.root 
    tntuple_name  = args.root.split("/")[-1].split("ntuple_")[1].split(".root")[0]
    th_name = tntuple_name + "_nums"


    w  = "w" #peso  nominale
    rwgt_keys = ['1:3','2:1','0:2', '1:0']
    rwgt_used = ['rwgt_1', 'rwgt_2', 'rwgt_3', 'rwgt_4']
    rwgt_notused = []
    rwgt_dict = dict(zip(rwgt_keys, rwgt_used))

    print(rwgt_dict)

    ntupleFileIn = file_path
    ntupleNameIn = tntuple_name
    histoNameIn = th_name
    ntupleSuffix = "_SM_LI_QU_IN"
    histoTitle = "global numbers"

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
    histoNameOut = ntupleNameOut + "_nums"

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

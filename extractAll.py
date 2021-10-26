import ROOT
import argparse
import configparser
from itertools import combinations
from array import array
import sys
import glob
import os
import logging
from common.ntupleCommon import *

def getEventsSM (ntuple, variables, nominal_wgt, rwgt):

    outevents_sm = []

    sum_nominal_weight = 0.
    sum_rwgt_sm = 0.

    leaves = {k: ntuple.GetLeaf(k) for k in variables}
    w = ntuple.GetLeaf(nominal_wgt)
    rwgt0 = ntuple.GetLeaf(rwgt['SM']["wgtName"][0])

    print ('[INFO] reading SM ntuple')
    
    #for i in range(0, ntuple.GetEntries()):
    for i in range(0, 1000000):

        values_sm = []

        ntuple.GetEntry(i)

        sum_nominal_weight += w.GetValue ()
        w_sm = rwgt0.GetValue () 

        sum_rwgt_sm += w_sm

        for (key, val) in sorted(leaves.items(), key=lambda x: x[1]):
            if key == nominal_wgt:
                values_sm.append(w_sm)
            else:
                values_sm.append(float(val.GetValue ()))
        outevents_sm.append (array('f', values_sm))

    print ('[INFO] sum of nominal weights: ' + str(sum_nominal_weight))
    print ('[INFO] sum of new SM nominal weights: ' + str(sum_rwgt_sm))

    resultsDict = {
        'events_sm': outevents_sm,
        'sum_nominal_weight': sum_nominal_weight,
        'sum_rwgt_sm': sum_rwgt_sm
    }

    return resultsDict

def getEventsLinQuad (ntuple, variables, nominal_wgt, rwgt):

    outevents_li = []
    outevents_qu = []

    sum_nominal_weight = 0.
    sum_rwgt_li = 0.
    sum_rwgt_qu = 0.

    quad_null = 0
    quad_neg = 0

    leaves = {k: ntuple.GetLeaf(k) for k in variables}
    w = ntuple.GetLeaf(nominal_wgt)
    rwgt0 = ntuple.GetLeaf(rwgt['0']["wgtName"][0])
    rwgtp1 = ntuple.GetLeaf(rwgt["1"]["wgtName"][0])
    rwgtm1 = ntuple.GetLeaf(rwgt["-1"]["wgtName"][0])

    print ('[INFO] reading SM + LI + QU ntuple')
    
    #for i in range(0, ntuple.GetEntries()):
    for i in range(0, 1000000):

        values_li = []
        values_qu = []

        ntuple.GetEntry(i)

        sum_nominal_weight += w.GetValue ()
        a = rwgtp1.GetValue ()
        b = rwgtm1.GetValue ()
        c = rwgt0.GetValue () 

        #sspeecific case for 0,1,-1 reweighting
        w_li = 0.5 * (a - b)
        w_qu = 0.5 * (a + b - 2 * c)

        sum_rwgt_li += w_li
        sum_rwgt_qu += w_qu
        if w_qu == 0 : quad_null = 1 + quad_null
        if w_qu < 0:
            w_qu = 0
            quad_neg = 1 + quad_neg

        for (key, val) in sorted(leaves.items(), key=lambda x: x[1]):
            if key == nominal_wgt:
                values_li.append(w_li)
                values_qu.append(w_qu)
            else:
                values_li.append(float(val.GetValue ()))
                values_qu.append(float(val.GetValue ()))
        outevents_li.append (array('f', values_li))
        outevents_qu.append (array('f', values_qu))

    print ('[INFO] sum of SM + LI + QU nominal weights: ' + str(sum_nominal_weight))
    print ('[INFO] sum of new LI nominal weights: ' + str(sum_rwgt_li))
    print ('[INFO] sum of new QU nominal weights: ' + str(sum_rwgt_qu))

    resultsDict = {
        'events_li': outevents_li,
        'events_qu': outevents_qu,
        'sum_nominal_weight': sum_nominal_weight,
        'sum_rwgt_li': sum_rwgt_li,
        'sum_rwgt_qu': sum_rwgt_qu,
        'quad_null': quad_null,
        'quad_neg': quad_neg,
    }

    return resultsDict



def getEventsIn (ntuple, variables, nominal_wgt, rwgt):

    outevents_in = []

    sum_nominal_weight = 0.
    sum_rwgt_in = 0.

    leaves = {k: ntuple.GetLeaf(k) for k in variables}
    w = ntuple.GetLeaf(nominal_wgt)
    rwgt11 = ntuple.GetLeaf(rwgt['11']["wgtName"][0])
    rwgt00 = ntuple.GetLeaf(rwgt['00']["wgtName"][0])
    rwgt01 = ntuple.GetLeaf(rwgt['01']["wgtName"][0])
    rwgt10 = ntuple.GetLeaf(rwgt['10']["wgtName"][0])

    print ('[INFO] reading SM + LI + QU + IN ntuple')
    
    #for i in range(0, ntuple.GetEntries()):
    for i in range(0, 1000000):

        values_in = []

        ntuple.GetEntry(i)

        sum_nominal_weight += w.GetValue ()
        r11 = rwgt11.GetValue ()
        r00 = rwgt00.GetValue ()
        r01 = rwgt01.GetValue ()
        r10 = rwgt10.GetValue ()

        w_in = r11 + r00 - r01 - r10

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
  Extract All components
 ----------------------------------- """)

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('--root', dest='root', help='root file ntuple_$proc_SM_LI_QU_IN.root', required=True)
    parser.add_argument('--rwgt', dest='rwgtcard', help='Reweight card that contains the mapping of weights to operator couplings, used to create the gridpack', required=True)
    parser.add_argument('--wInt', dest='hasInt', help='if overall gridpack produced with more than one operator, default is false', required=False, default=False,  action='store_true')
    parser.add_argument('--ops', dest='ops', help='comma separated list of operstors to be extracted', required=False, default="*")
    parser.add_argument('--out', dest='out', help='outfolder path to save ntuples, default is current dir', required=False, default="")
    args = parser.parse_args()


    file_path = args.root 
    tntuple_name  = args.root.split("/")[-1].split("ntuple_")[1].split(".root")[0]
    th_name = tntuple_name + "_nums"

    process = tntuple_name.split("_")[0]
    suff = "SM_LI_QU"
    if args.hasInt:
        suff = "SM_LI_QU_IN"

    ops = tntuple_name.split(process + "_")[1].split("_" + suff)[0].split("_")

    # reading the reweight card and creating a dict
    # ('cW_1p0_cHq1_1p0', {'wgtName': ['rwgt_33'], 'values': [[1.0, 1.0]]})
    # ('cHDD_m1p0', {'wgtName': ['rwgt_6'], 'values': [[-1.0]]})
    # ('SM', {'wgtName': ['rwgt_1'], 'values': [[]]})

    op_names =  {
        '2': 'cW',
        '9': 'cHWB',
        '5': 'cHDD',
        '30': 'cll1',
        '21': 'cHl1',
        '22': 'cHl3',
        '24': 'cHq1',
        '25': 'cHq3',
        #to be continued 
    }

    if not args.ops or args.ops == "*": ops = [op_names[k] for k in op_names.keys()]
    else: ops = args.ops.split(",")

    op_comb = list(combinations(ops, 2))

    tot_number_of_files = 1 + 2*len(ops) + len(op_comb) #SM + NLin + Nquad + N(N-1)/2 IN
    count_filled = 0

    c = readReweightCard(args.rwgtcard, convert_names = op_names)
    
    #first extract SM

    w  = "w" #nominal weight

    print ('\n\tNtuple file-in   =  ' + file_path)
    print ('\tTNtuple name-in  =  ' + tntuple_name)
    print ('\tTH1F name-in     =  ' + th_name + '\n')

    f_in = ROOT.TFile (file_path, 'READ')
    t = ROOT.gDirectory.Get (tntuple_name)
    h = ROOT.gDirectory.Get (th_name)
    overallXS = h.GetBinContent(1)
    print ('[INFO] overall XS: ' + str(overallXS))

    print("""
    #-------------------------------------#
    #-----------     BEGIN    ------------#
    #-------------------------------------#
    """)
        
    leaves = t.GetListOfLeaves()
    vars_wrwgt = [leaves.At(i).GetName() for i in range(0, leaves.GetEntries())]
    # variables for final ntuple
    vars = [v for v in vars_wrwgt if "rwgt" not in v]
    vars.sort()

    events_dictionary = getEventsSM (t, vars, w, c)

    eventsIN = events_dictionary['events_sm']
    SumWgtOld = events_dictionary['sum_nominal_weight']
    SumWgtIN = events_dictionary['sum_rwgt_sm']

    f_in.Close()
        
    XS = overallXS * SumWgtIN / SumWgtOld

    ntupleFileOut = args.out + "ntuple_" + process + '_SM.root'
    ntupleNameOut = process + '_SM'
    histoNameOut = ntupleNameOut + "_nums"

    print ('\n\tNtuple file-out  =  ' + ntupleFileOut)
    print ('\tTNtuple name-out =  ' + ntupleNameOut)
    print ('\tTH1F name-out    =  ' + histoNameOut + '\n')

    t = getNtuple (ntupleNameOut, ntupleNameOut, vars, eventsIN)
    h = getHisto (histoNameOut, "global numbers", XS, SumWgtIN, SumWgtIN)

    f_out = ROOT.TFile (ntupleFileOut, 'RECREATE')

    print ('[INFO] writing ROOT file')
    t.Write()
    h.Write()
        
    f_out.Close()
    count_filled += 1

    print ('\n[INFO] end SM process')
    print("")
    print("# -----------  {}/{}   ----------- # ".format(count_filled, tot_number_of_files))
    print("")

    #then extract linear and quadratic
    for op in ops:

        f_in = ROOT.TFile (file_path, 'READ')
        t = ROOT.gDirectory.Get (tntuple_name)
        h = ROOT.gDirectory.Get (th_name)
        overallXS = h.GetBinContent(1)

        #searching weights name from the dict
        rwgt_dict = {}
        rwgt_dict["1"] = c[op + "_1p0"]
        rwgt_dict["0"] = c["SM"]
        rwgt_dict["-1"] = c[op + "_m1p0"]

        events_dictionary = getEventsLinQuad (t, vars, w, rwgt_dict)

        eventsLI = events_dictionary['events_li']
        eventsQU = events_dictionary['events_qu']
        SumWgtOld = events_dictionary['sum_nominal_weight']
        SumWgtLI = events_dictionary['sum_rwgt_li']
        SumWgtQU = events_dictionary['sum_rwgt_qu']
        q_null = events_dictionary['quad_null']
        q_neg = events_dictionary['quad_neg']

        f_in.Close()

        if q_null > 0:
            print ('[WARNING] {0}: {1} events give Quad nominal weight = 0'.format(op, q_null))
        if q_neg > 0:
            print ('[WARNING] {0}: {1} events give Quad nominal weight < 0. Setting them to 0'.format(op, q_neg))

        for component in ['LI', 'QU']:

            if component == 'LI':
                eventsExtr = eventsLI
                SumWgtExtr = SumWgtLI
            elif component == 'QU':
                eventsExtr = eventsQU
                SumWgtExtr = SumWgtQU
            
            XS = overallXS * SumWgtExtr / SumWgtOld

            ntupleFileOut = args.out + "ntuple_" + process + '_{}_{}.root'.format(op, component)
            ntupleNameOut = process + '_{}_{}'.format(op, component)
            histoNameOut = ntupleNameOut + "_nums"

            print ('\n\tNtuple file-out  =  ' + ntupleFileOut)
            print ('\tTNtuple name-out =  ' + ntupleNameOut)
            print ('\tTH1F name-out    =  ' + histoNameOut + '\n')
            
            t = getNtuple (ntupleNameOut, ntupleNameOut, vars, eventsExtr)
            h = getHisto (histoNameOut, "global numbers", XS, SumWgtExtr, SumWgtExtr)
            f_out = ROOT.TFile (ntupleFileOut, 'RECREATE')

            print ('[INFO] writing {} {} ROOT file'.format(op, component))
            t.Write()
            h.Write()
            
            f_out.Close()
            
            count_filled += 1
            print("")
            print("# -----------  {}/{}   ----------- # ".format(count_filled, tot_number_of_files))
            print("")


    #then extract imxed interferences
    for op_pair in op_comb:

        f_in = ROOT.TFile (file_path, 'READ')
        t = ROOT.gDirectory.Get (tntuple_name)
        h = ROOT.gDirectory.Get (th_name)
        overallXS = h.GetBinContent(1)

        #searching weights name from the dict
        rwgt_dict = {}
        #00
        rwgt_dict["00"] = c["SM"]

        #11
        if op_pair[0] + "_1p0_" + op_pair[1] + "_1p0" in c.keys():
            rwgt_dict["11"] = c[op_pair[0] + "_1p0_" + op_pair[1] + "_1p0"]
        elif op_pair[1] + "_1p0_" + op_pair[0] + "_1p0" in c.keys():
            rwgt_dict["11"] = c[op_pair[1] + "_1p0_" + op_pair[0] + "_1p0"]
        else: sys.error("c directory does not have {} component".format(op_pair[0] + "_1p0_" + op_pair[1] + "_1p0"))

        #10
        rwgt_dict["10"] = c[op_pair[0] + "_1p0"]
        #01
        rwgt_dict["01"] = c[op_pair[1] + "_1p0"]

        events_dictionary = getEventsIn (t, vars, w, rwgt_dict)

        eventsIN = events_dictionary['events_in']
        SumWgtOld = events_dictionary['sum_nominal_weight']
        SumWgtIN = events_dictionary['sum_rwgt_in']

        f_in.Close()
            
        XS = overallXS * SumWgtIN / SumWgtOld

        ntupleFileOut = args.out + "ntuple_" + process + '_{}_{}_IN.root'.format(op_pair[0], op_pair[1])
        ntupleNameOut = process + '_{}_{}_IN'.format(op_pair[0], op_pair[1])
        histoNameOut = ntupleNameOut + "_nums"

        print ('\n\tNtuple file-out  =  ' + ntupleFileOut)
        print ('\tTNtuple name-out =  ' + ntupleNameOut)
        print ('\tTH1F name-out    =  ' + histoNameOut + '\n')

        t = getNtuple (ntupleNameOut, ntupleNameOut, vars, eventsIN)
        h = getHisto (histoNameOut, "global numbers", XS, SumWgtIN, SumWgtIN)

        f_out = ROOT.TFile (ntupleFileOut, 'RECREATE')

        print ('[INFO] writing {} IN ROOT file'.format(op_pair))
        t.Write()
        h.Write()
            
        f_out.Close()

        count_filled += 1
        print("")
        print("# -----------  {}/{}   ----------- # ".format(count_filled, tot_number_of_files))
        print("")
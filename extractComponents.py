import ROOT
import argparse
import configparser
from array import array
import sys
import glob
import os
import logging
from datetime import datetime
from common.ntupleCommon import getTreeName, getNtuple, getHisto


def rwgtObjects (couplingList, nameList, notusedList):

    keys = [rwgt.strip() for rwgt in couplingList]
    used = [rwgt.strip() for rwgt in nameList]
    notused = [rwgt.strip() for rwgt in notusedList]

    if len(keys) == len(used):

        used_dict = dict(zip(keys, used))
        return keys, used, notused, used_dict

    else: raise IndexError ('In config file <name> and <coupling> have different sizes')


def getEvents (ntuple, variables, nominal_wgt, rwgt):

    outevents_li = []
    outevents_qu = []

    sum_nominal_weight = 0.
    sum_rwgt_li = 0.
    sum_rwgt_qu = 0.

    quad_null = 0
    quad_neg = 0

    leaves = {k: ntuple.GetLeaf(k) for k in variables}
    w = ntuple.GetLeaf(nominal_wgt)
    rwgt0 = ntuple.GetLeaf(rwgt['0.0'])
    rwgtp1 = ntuple.GetLeaf(rwgt['1.0'])
    rwgtm1 = ntuple.GetLeaf(rwgt['-1.0'])

    print ('[INFO] reading SM + LI + QU ntuple')
    
    for i in range(0, ntuple.GetEntries()):

        values_li = []
        values_qu = []

        ntuple.GetEntry(i)

        sum_nominal_weight += w.GetValue ()
        a = rwgtp1.GetValue ()
        b = rwgtm1.GetValue ()
        c = rwgt0.GetValue ()
        w_li = 0.5 * (a - b)
        w_qu = 0.5 * (a + b - 2 * c)
        sum_rwgt_li += w_li
        sum_rwgt_qu += w_qu
        if w_qu == 0 : quad_null = 1 + quad_null
        if w_qu < 0 : quad_neg = 1 + quad_neg

        for (key, val) in sorted(leaves.items(), key=lambda x: x[1]):
            if key == nominal_wgt:
                values_li.append(w_li)
                values_qu.append(w_qu)
            else:
                values_li.append(float(val.GetValue ()))
                values_qu.append(float(val.GetValue ()))
        outevents_li.append (array('f', values_li))
        outevents_qu.append (array('f', values_qu))

    logging.info('sum of SM + LI + QU nominal weights: ' + str(sum_nominal_weight))
    logging.info('sum of new LI nominal weights: ' + str(sum_rwgt_li))
    logging.info('sum of new QU nominal weights: ' + str(sum_rwgt_qu))

    print ('[INFO] sum of SM + LI + QU nominal weights: ' + str(sum_nominal_weight))
    print ('[INFO] sum of new LI nominal weights: ' + str(sum_rwgt_li))
    print ('[INFO] sum of new QU nominal weights: ' + str(sum_rwgt_qu))

    return outevents_li, outevents_qu, sum_nominal_weight, sum_rwgt_li, sum_rwgt_qu, quad_null, quad_neg


if __name__ == '__main__':

    print("""
 _____________________________________ 
  Extract LI and QU from SM + LI + QU 
 ------------------------------------- """)

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('--cfg', dest='config', help='Config .cfg file path containing reweights', required=True)
    parser.add_argument('--li', dest='li', help='Extract linear component', type=bool, default=True, required=False)
    parser.add_argument('--qu', dest='qu', help='Extract quadratic component', type=bool, default=True, required=False)
    args = parser.parse_args()

    if not args.li and not args.qu:
        sys.exit('Nothing to be extracted')

    cfg = configparser.ConfigParser()
    cfg.readfp(open(args.config, 'r'))

    # retrieve infos from config
    ntupleDir = cfg.get('ntuple', 'dir')
    ntupleDir = ntupleDir + '/' + cfg.get('subdir', 'proc')
    operators = cfg.get('operator', 'name').split(',')
    stateOut = cfg.get('tobemerged', 'out').strip()
    staticParts = cfg.get('ntuple', 'static').split(',')
    w = cfg.get('variables', 'nominalwgt').strip()
    ntupleSuffix = cfg.get('ntuple', 'suffix').strip()
    histoSuffix = cfg.get('histogram', 'suffix').strip()
    histoTitle = cfg.get('histogram', 'title').strip()
    logfile = ntupleDir + '/' + datetime.now().strftime('%Y%m%d-%H%M%S-extractComponents.log')
    logging.basicConfig(format='%(asctime)s :: %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                            filename=logfile, level=logging.INFO)
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

    files = [f for f in glob.glob(ntupleDir + '/ntuple*' + ntupleSuffix + '.root') if stateOut in f]
    
    for ntupleFileIn in files:

        if not any(op.strip() in os.path.basename(ntupleFileIn).split('_') for op in operators): continue

        ntupleFileIn = ntupleFileIn.strip()
        ntupleNameIn = getTreeName (os.path.basename(ntupleFileIn), staticParts)
        histoNameIn = ntupleNameIn + histoSuffix

        logging.info('working on ' + ntupleNameIn.replace(ntupleSuffix, ''))
        print ('\n\tNtuple file-in   =  ' + ntupleFileIn)
        print ('\tTNtuple name-in  =  ' + ntupleNameIn)
        print ('\tTH1F name-in     =  ' + histoNameIn + '\n')

        f_in = ROOT.TFile (ntupleFileIn, 'READ')
        t = ROOT.gDirectory.Get (ntupleNameIn)
        h = ROOT.gDirectory.Get (histoNameIn)
        overallXS = h.GetBinContent(1)
        logging.info('overall XS: ' + str(overallXS))
        print ('[INFO] overall XS: ' + str(overallXS))
            
        leaves = t.GetListOfLeaves()
        vars_wrwgt = [leaves.At(i).GetName() for i in range(0, leaves.GetEntries())]
        # variables for final ntuple
        vars = [v for v in vars_wrwgt if v not in list(set(rwgt_used)|set(rwgt_notused))]
        vars.sort()

        eventsLI, eventsQU, SumWgtOld, SumWgtLI, SumWgtQU, q_null, q_neg = getEvents (t, vars, w, rwgt_dict)
        f_in.Close()

        if q_null > 0:
            logging.warning(str(q_null) + 'events give BSM nominal weight = 0')
            print ('[WARNING] {0}: {1} events give BSM nominal weight = 0'.format(ntupleNameIn, q_null))
        if q_neg > 0:
            logging.warning(str(q_neg) + 'events give BSM nominal weight < 0')
            print ('[WARNING] {0}: {1} events give BSM nominal weight < 0'.format(ntupleNameIn, q_neg))

        for component in ['LI', 'QU']:

            if component == 'LI':
                if args.li:
                    eventsExtr = eventsLI
                    SumWgtExtr = SumWgtLI
                else: continue
            elif component == 'QU':
                if args.qu:
                    eventsExtr = eventsQU
                    SumWgtExtr = SumWgtQU
                else: continue
            
            XS = overallXS * SumWgtExtr / SumWgtOld
            logging.info('XSec({0}) =  {1}'.format(component, XS))

            ntupleFileOut = ntupleFileIn.replace(ntupleSuffix, '_' + component).strip()
            ntupleNameOut = ntupleNameIn.replace(ntupleSuffix, '_' + component).strip()
            histoNameOut = ntupleNameOut + histoSuffix

            print ('\n\tNtuple file-out  =  ' + ntupleFileOut)
            print ('\tTNtuple name-out =  ' + ntupleNameOut)
            print ('\tTH1F name-out    =  ' + histoNameOut + '\n')
            
            t = getNtuple (ntupleNameOut, ntupleNameOut, vars, eventsExtr)
            h = getHisto (histoNameOut, histoTitle, XS, SumWgtExtr, SumWgtExtr)

            f_out = ROOT.TFile (ntupleFileOut, 'RECREATE')

            print ('[INFO] writing ROOT file')
            t.Write()
            h.Write()
            
            f_out.Close()

    print ('\n[INFO] end process')
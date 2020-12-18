import ROOT
import argparse
import configparser
from array import array


def getTreeName (filepath, conventions):

    if '/' in filepath:
        treeName = filepath.split('/')[1]
    else:
        treeName = filepath
        
    for s in conventions:
        treeName = treeName.replace(s.strip(), '')

    return treeName


def rwgtObjects (couplingList, nameList, notusedList):

    keys = [rwgt.strip() for rwgt in couplingList]
    used = [rwgt.strip() for rwgt in nameList]
    notused = [rwgt.strip() for rwgt in notusedList]

    if len(keys) == len(used):

        used_dict = dict(zip(keys, used))
        return keys, used, notused, used_dict

    else: raise KeyError ('In config file <name> and <coupling> have different sizes')


def getEvents (ntuple, variables, nominal_wgt, rwgt):

    outevents = []

    sum_nominal_weight = 0.
    sum_rwgt = 0.

    leaves = {k: ntuple.GetLeaf(k) for k in variables}
    w = ntuple.GetLeaf(nominal_wgt)
    rwgt0 = ntuple.GetLeaf(rwgt['0.0'])
    rwgtp1 = ntuple.GetLeaf(rwgt['1.0'])
    rwgtm1 = ntuple.GetLeaf(rwgt['-1.0'])

    print ('[INFO] reading SM + LI + QU ntuple')
    
    for i in range(0, ntuple.GetEntries()):

        values = []

        ntuple.GetEntry(i)

        sum_nominal_weight += w.GetValue ()
        a = rwgtp1.GetValue ()
        b = rwgtm1.GetValue ()
        c = rwgt0.GetValue ()
        qu = 0.5 * (a + b - 2 * c)
        sum_rwgt += qu

        for (key, val) in sorted(leaves.items(), key=lambda x: x[1]):
            if key == nominal_wgt: values.append(qu)
            else: values.append(float(val.GetValue ()))
        outevents.append (array('f', values))

    print ('[INFO] sum of SM + LI + QU nominal weights: ' + str(sum_nominal_weight))
    print ('[INFO] sum of new QU nominal weights: ' + str(sum_rwgt))

    return outevents, sum_nominal_weight, sum_rwgt


def writeNtuple (name, title, variables, events):

    print ('[INFO] writing QU ntuple')

    ntuple = ROOT.TNtuple (name, title, ':'.join(variables))
    for e in events : ntuple.Fill(e)
    ntuple.Write()

def writeHisto (name, title, old_XS, old_sum_wgt, new_sum_wgt):

    print ('[INFO] writing QU global numbers histogram')

    histo = ROOT.TH1F (name, title, 3, 0, 3)
    histo.SetBinContent(1, old_XS * new_sum_wgt / old_sum_wgt)
    histo.SetBinContent(2, new_sum_wgt)
    histo.SetBinContent(3, new_sum_wgt) # to be improved
    histo.Write()


if __name__ == '__main__':

    print("""
 ______________________________ 
  Extract QU from SM + LI + QU 
 ------------------------------ """)

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('--cfg', dest='config', help='Config .cfg file path containing reweights', required = True)
    args = parser.parse_args()

    cfg = configparser.ConfigParser()
    cfg.readfp(open(args.config, 'r'))

    # retrieve infos from config
    files = cfg.get('ntuple', 'files').split(',')
    staticParts = cfg.get('ntuple', 'static').split(',')
    w = cfg.get('variables', 'nominalwgt').strip()
    suffix = cfg.get('histogram', 'suffix').strip()
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
    
    for ntupleFileIn in files:

        ntupleFileIn = ntupleFileIn.strip()
        ntupleFileOut = ntupleFileIn.replace('.root', '_QU.root')
        ntupleNameIn = getTreeName (ntupleFileIn, staticParts)
        ntupleNameOut = ntupleNameIn + '_QU'
        histoNameIn = ntupleNameIn + suffix
        histoNameOut = ntupleNameOut + suffix

        print ('\n\tNtuple file-in   =  ' + ntupleFileIn)
        print ('\tTNtuple name-in  =  ' + ntupleNameIn)
        print ('\tTH1F name-in     =  ' + histoNameIn + '\n')
        print ('\tNtuple file-out  =  ' + ntupleFileOut)
        print ('\tTNtuple name-out =  ' + ntupleNameOut)
        print ('\tTH1F name-out    =  ' + histoNameOut + '\n')
        
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

        eventsQU, oldSumWgt, newSumWgt = getEvents (t, vars, w, rwgt_dict)
        f_in.Close()

        f_out = ROOT.TFile (ntupleFileOut, 'RECREATE')
        writeNtuple (ntupleNameOut, ntupleNameOut, vars, eventsQU)
        writeHisto (histoNameOut, histoTitle, overallXS, oldSumWgt, newSumWgt)
        f_out.Close()

    print ('[INFO] end process')
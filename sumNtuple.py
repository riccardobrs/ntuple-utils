import ROOT
import argparse
import configparser
from array import array
import sys
import glob
import os
import pandas as pd
from common.ntupleCommon import getTreeName, getHisto, getNtuple


def getEvents (ntuple, variables, eventsList):

    leaves = {k: ntuple.GetLeaf(k) for k in variables}
    
    for i in range(0, ntuple.GetEntries()):

        values = []
        ntuple.GetEntry(i)

        for (key, val) in sorted(leaves.items(), key=lambda x: x[1]):
            values.append(float(val.GetValue ()))

        eventsList.append (array('f', values))

    return eventsList


def writeCsv (name, columnsList, rowList):

    df = pd.DataFrame(rowList)
    df.columns = columnsList
    df.to_csv(name, index=False)

    
if __name__ == '__main__':

    print("""
 _______________ 
  Ntuple merger 
 --------------- """)

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('--cfg', dest='config', help='Config .cfg file path containing ntuple infos',
                            required=True)
    parser.add_argument('--csv', dest='csv', help='Save .cfg output and ntuple in .csv format', 
                            default=False, action='store_true', required=False)
    parser.add_argument('--multi', dest='multi', help='Multi operator mode: op1_op2. Default is 1D', 
                            default=False, action='store_true', required=False)
    args = parser.parse_args()

    cfg = configparser.ConfigParser()
    cfg.readfp(open(args.config, 'r')) # this method will be deprecated

    # retrieve infos from config
    ntupleDir = cfg.get('ntuple', 'dir').strip()
    staticParts = cfg.get('ntuple', 'static').split(',')
    ntupleSuffix = cfg.get('ntuple', 'suffix').strip()
    histoSuffix = cfg.get('histogram', 'suffix').strip()
    histoTitle = cfg.get('histogram', 'title').strip()
    statesIn = cfg.get('tobemerged', 'in').split(',')
    stateOut = cfg.get('tobemerged', 'out').strip()
    ops1d = cfg.get('operator', 'name').split(',')
    csvSubdir = cfg.get('subdir', 'csv').strip()
    cfgSubdir = cfg.get('subdir', 'cfg').strip()
    procSubdir = cfg.get('subdir', 'proc').strip()

    if args.csv : subdirs = [cfgSubdir, csvSubdir, procSubdir]
    else : subdirs = [procSubdir]
    for sdir in subdirs:
        sdirpath = ntupleDir + '/' + sdir
        if not os.path.isdir(sdirpath):
            os.mkdir(sdirpath)
    
    if args.multi:
        operators = list()
        for x in range(len(ops1d)):
            for y in range(x+1, len(ops1d)):
                operators.append('{0}_{1}'.format(ops1d[x].strip(),ops1d[y].strip()))
    else:
        operators = ops1d

    for operator in operators:

        files = [f for f in glob.glob(ntupleDir + '/ntuple*' + ntupleSuffix + '.root') if (operator.strip()+'_') in f]
        if args.multi:
            files = [f for f in files if 'IN' in f]
        else:
            files = [f for f in files if 'IN' not in f]
        
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
        if args.csv:
            csvFileOut = ntupleDir + '/' + csvSubdir + '/' + os.path.basename(ntupleFileOut).replace('.root', '.csv')
            cfgFileOut = ntupleDir + '/' + cfgSubdir + '/' + os.path.basename(ntupleFileOut).replace('.root', '.cfg')
            print ('\n[INFO] csv file-out =  ' + csvFileOut)
            print ('[INFO] cfg file-out =  ' + cfgFileOut)
        ntupleFileOut = ntupleDir + '/' + procSubdir + '/' + os.path.basename(ntupleFileOut)
        ntupleNameOut = getTreeName (os.path.basename(ntupleFileOut), staticParts)
        histoNameOut = ntupleNameOut + histoSuffix

        if args.csv:

            ### converting events list to dataframe e saving as a csv
            print ('\n[INFO] writing events to csv')
            writeCsv (csvFileOut, vars, eventsList)

            print ('[INFO] writing cfg file\n')
            with open(cfgFileOut, 'w') as f:
                f.write('#################################################\n')
                f.write('# this file has been automatically generated by #\n')
                f.write('#                sumNtuple.py                   #\n')
                f.write('#           please do not modify it             #\n')
                f.write('#################################################\n')
                f.write('\n')
                f.write('[ntuple]\n')
                f.write('root = {0}\n'.format(ntupleFileOut))
                f.write('csv = {0}\n'.format(csvFileOut))
                f.write('\n')
                f.write('[tntuple]\n')
                f.write('name = {0}\n'.format(ntupleNameOut))
                f.write('title = {0}\n'.format(ntupleNameOut))
                f.write('\n')
                f.write('[th1f]\n')
                f.write('name = {0}\n'.format(histoNameOut))
                f.write('title = {0}\n'.format(histoTitle))
                f.write('XS = {0}\n'.format(XS))
                f.write('sw_overall = {0}\n'.format(sw_overall))
                f.write('sw_passed = {0}\n'.format(sw_passed))
        
        else:

            print ('\n[INFO] ROOT file-out  =  ' + ntupleFileOut)
            print ('[INFO] TNtuple name-out =  ' + ntupleNameOut)
            print ('[INFO] TH1F name-out    =  ' + histoNameOut + '\n')

            t = getNtuple (ntupleNameOut, ntupleNameOut, vars, eventsList)
            h = getHisto (histoNameOut, histoTitle, XS, sw_overall, sw_passed)

            f_out = ROOT.TFile (ntupleFileOut, 'RECREATE')

            print ('[INFO] writing ROOT file')
            t.Write()
            h.Write()

            f_out.Close()

    print ('\n[INFO] end process')
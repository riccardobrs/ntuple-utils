#!/usr/bin/env python

import ROOT
import configparser
from array import array
import sys
import glob
import os
import pandas as pd
from common.ntupleCommon import getNtuple, getHisto


if __name__ == '__main__':

    try:
        cfgDir = sys.argv[1]
    except:
        raise IndexError ('Missing mandatory argument: cfg directory path')

    print("""
 ____________________________ 
  Text 2 ROOT file converter 
 ---------------------------- """)

    files = [os.path.abspath(f) for f in glob.glob(cfgDir + '/*') if os.path.splitext(f)[1] == '.cfg']

    for f in files:

        cfg = configparser.ConfigParser()
        cfg.readfp(open(f, 'r')) # this method will be deprecated

        # retrieve infos from config
        csvIn = cfg.get('ntuple', 'csv').strip()
        rootOut = cfg.get('ntuple', 'root').strip()
        ntupleName = cfg.get('tntuple', 'name').strip()
        ntupleTitle = cfg.get('tntuple', 'title').strip()
        histoName = cfg.get('th1f', 'name').strip()
        histoTitle = cfg.get('th1f', 'title').strip()
        XS = float(cfg.get('th1f', 'XS').strip())
        sw_overall = float(cfg.get('th1f', 'sw_overall').strip())
        sw_passed = float(cfg.get('th1f', 'sw_passed').strip())

        print ('\n[INFO] working on ' + ntupleName)
        print ('\n[INFO] csv file-in  =  ' + csvIn)
        print ('[INFO] ROOT file-out  =  ' + rootOut)

        vars = []
        df = pd.read_csv(csvIn)
        for c in df.columns: vars.append(c)
        events = df.values.tolist()
        print ('[INFO] working on {0} events'.format(len(events))) 
        for i in range(len(events)):
            events[i] = array('f', events[i])
        
        t = getNtuple (ntupleName, ntupleTitle, vars, events)
        h = getHisto (histoName, histoTitle, XS, sw_overall, sw_passed)

        f_out = ROOT.TFile (rootOut, 'RECREATE')

        print ('[INFO] writing ROOT file')
        t.Write()
        h.Write() 

        f_out.Close()

import ROOT
from glob import glob
import argparse
import pandas as pd
import os

if __name__ == '__main__':

    print("""
 _____________ 
  mjj matcher 
 ------------- """)

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('--baseFolder', '-b', dest='baseFolder', help='Folder containing ntuple', required=True)
    parser.add_argument('--match', dest='match', help='Two comma separated variables to be matched', required=True)
    parser.add_argument('--cut', dest='cut', help='Super cut', default='1==1', required=False)
    parser.add_argument('--prefix', dest='prefix', help='.root files prefix', default='ntuple', required=False)
    args = parser.parse_args()

    baseFolder = os.path.abspath(args.baseFolder)
    ntuple = glob (baseFolder + '/' + args.prefix + '*.root')

    m1 = args.match.split(',')[0].strip()
    m2 = args.match.split(',')[1].strip()
    den = args.cut
    num = '{0}=={1} && {2}'.format(m1, m2, den)

    matches = list()

    for n in ntuple:

        f = ROOT.TFile (n)
        objs = [f.Get(key.GetName()).IsA().GetName() for key in f.GetListOfKeys()]
        names = [key.GetName() for key in f.GetListOfKeys()]
        name = dict(zip(objs, names))['TNtuple']
        t = f.Get(name)
        p = float(t.GetEntries(num)) / t.GetEntries(den)
        f.Close()

        matches.append([name, round(p,2)])
    
    df = pd.DataFrame(matches)
    df.columns = ['Name', 'Matching percentage']
    df.to_csv(baseFolder+'/matches.csv', index=False)
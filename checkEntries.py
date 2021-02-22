import ROOT
from glob import glob
import argparse
import os

if __name__ == '__main__':

    print("""
 _________________________ 
  check number of entries 
 ------------------------- """)

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('--baseFolder', '-b', dest='baseFolder', help='Folder containing ntuple', required=True)
    parser.add_argument('--prefix', dest='prefix', help='.root files prefix', default='ntuple', required=False)
    args = parser.parse_args()

    baseFolder = os.path.abspath(args.baseFolder)
    ntuple = glob (baseFolder + '/' + args.prefix + '*.root')

    for n in ntuple:

        f = ROOT.TFile (n)
        objs = [f.Get(key.GetName()).IsA().GetName() for key in f.GetListOfKeys()]
        names = [key.GetName() for key in f.GetListOfKeys()]
        name = dict(zip(objs, names))['TNtuple']
        t = f.Get(name)
        entries = t.GetEntries()
        print(name + ' ' + str(entries))
        f.Close()

import ROOT
import argparse
from glob import glob
import os


if __name__ == '__main__':

    print("""
 ______________ 
  Check Events 
 -------------- """)

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('-b', dest='base', help='Base directory where operator folders are contained',
                            required=True)
    parser.add_argument('--delete', dest='delete', help='Delete corrupt root files', 
                            default=False, action='store_true', required=False)
    args = parser.parse_args()

    b = os.path.abspath(args.base)
    files = glob(b + '/*/*.root')
    corrupt = list()

    for f in files:
        rf = ROOT.TFile(f, 'READ')
        t = rf.Get('Events')
        if t.GetEntries() == 0:
            corrupt.append(f)
        rf.Close()

    for c in corrupt:
        print('>>> Empty events tree for ' + c)
        if args.delete: os.system('rm ' + c)
    
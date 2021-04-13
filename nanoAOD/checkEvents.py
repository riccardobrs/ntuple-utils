import ROOT
import argparse
from glob import glob
import os


if __name__ == '__main__':

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
        n = t.GetEntries()
        if n == 0:
            print('>>> Empty events tree for ' + f)
            corrupt.append(f)
        else:
            print('>>> Number of events for {0} = {1}'.format(f,n))
        rf.Close()

    if args.delete:
        print('>>> Removing empty root files')
        for c in corrupt:
            os.system('rm ' + c)
    
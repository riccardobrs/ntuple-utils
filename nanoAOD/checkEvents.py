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
    parser.add_argument('--verbose', dest='verbose', help='Verbose mode', 
                            default=False, action='store_true', required=False)
    args = parser.parse_args()

    b = os.path.abspath(args.base)
    files = glob(b + '/*/*.root')
    corrupt = list()
    events = 0

    for f in files:
        rf = ROOT.TFile(f, 'READ')
        t = rf.Get('Events')
        n = t.GetEntries()
        if n == 0:
            print('>>> Empty events tree for ' + f)
            corrupt.append(f)
        else:
            events += n
            if args.verbose:
                print('>>> Number of events for {0} = {1}'.format(f,n))
        rf.Close()

    if args.delete:
        if len(corrupt) > 0:
            print('>>> Removing empty root files')
        for c in corrupt:
            os.system('rm ' + c)
    
    ratio = int(1000 * float(len(corrupt)) / len(files)) / 10.0
    average = float(events) / (len(files) - len(corrupt))
    
    print('\nSummary')
    print('--------------------------------')
    print('Scanned files: {0}'.format(len(files)))
    print('Corrupt files: {0}'.format(len(corrupt)))
    print('Corrupt files percentage: {0}%'.format(ratio))
    print('Average events per file: {0}'.format(average)) # corrupt files neglected
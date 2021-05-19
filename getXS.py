import configparser
from glob import glob
import argparse
import os
import re
import ROOT

global sample_str
sample_str = "samples['{0}'].extend( ['xsec={1}',      'kfact=1.00',           'ref=X'] )\n"

def getRegexMatch(regex, str_analyzed):

    match = re.search(regex, str_analyzed, re.IGNORECASE)
    if match is not None:
        return match.group()
    else:
        return None


def getSampleStr(cfgfile):

    with open(cfgfile, 'r') as cp:
        cfg = configparser.ConfigParser()
        cfg.readfp(cp)
        sample_name = [str(c) for c in cfg.sections() if str(c).startswith('Z')][0]
        sample_XS = str(cfg.get(sample_name, 'XS')) # pb

    return sample_str.format(sample_name,sample_XS)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('-b', dest='base', help='Results archives base folder', required=True)
    parser.add_argument('-o', dest='outfile', help='Output path', required=True)
    parser.add_argument('--ext', dest='ext', help='Archives extension', required=False, default='tar.gz')
    parser.add_argument('--root', dest='root', help='Get XS from .root file', required=False, default=False, action='store_true')
    args = parser.parse_args()

    xs_list = list()

    if os.path.isfile(args.outfile):
        with open(args.outfile, 'r') as o:
            for line in o.readlines():
                sample = getRegexMatch("(?<=samples\[').*?(?='\])", line)
                if (sample is not None) and (sample not in xs_list):
                    xs_list.append(sample)
    
    tars = glob(os.path.abspath(args.base) + '/*.' + args.ext)
    for tar in tars:

        if getRegexMatch(".*?(?=_results)", os.path.basename(tar)) in xs_list:
            print('[INFO] skipping ' + tar)
            continue

        rmdir = False
        cfgpath = os.path.basename(tar).split('.')[0] + '/read_03_input.cfg'
        cfgdir = os.path.dirname(os.path.abspath(cfgpath))
        if '_results' not in cfgdir:
            print('[INFO] skipping ' + tar)
            continue
        else:
            if os.path.isdir(cfgdir):
                if os.path.isfile(cfgpath):
                    print('[INFO] working on ' + cfgpath)
                else:
                    print('[INFO] skipping ' + tar)
                    continue
            else:
                print('[INFO] working on ' + tar)
                rmdir = True
                os.system('tar --extract --file={0} {1}'.format(tar, cfgpath))
                print('       read_03_input.cfg extracted')
        
        with open(args.outfile, 'a') as o:
            o.write(getSampleStr(cfgpath))

        if rmdir:    
            os.system('rm -rf ' + cfgdir)

    results = glob(os.path.abspath(args.base) + '/*_results')
    for result in results:

        if getRegexMatch(".*?(?=_results)", os.path.basename(result)) in xs_list:
            print('[INFO] skipping ' + result)
            continue

        cfgpath = os.path.basename(result) + '/read_03_input.cfg'
        cfgdir = os.path.dirname(os.path.abspath(cfgpath))
        if os.path.isdir(cfgdir):
            if os.path.isfile(cfgpath):
                print('[INFO] working on ' + cfgpath)
            else:
                print('[INFO] skipping ' + result)
                continue
        else:
            print('[INFO] skipping ' + result)
            continue

        with open(args.outfile, 'a') as o:
            o.write(getSampleStr(cfgpath))
    
    if args.root:
        roots = glob(os.path.abspath(args.base) + '/*.root')
        for root in roots:
            sample = getRegexMatch("(?<=ntuple_).*?(?=.root)", os.path.basename(root))
            if sample in xs_list:
                print('[INFO] skipping ' + root)
                continue
            print('[INFO] working on ' + root)
            f = ROOT.TFile(root, 'READ')
            h = f.Get(sample + '_nums')
            xs = h.GetBinContent(1)
            to_write = sample_str.format(sample,xs)
            with open(args.outfile, 'a') as o:
                o.write(to_write)
            f.Close()


    

import configparser
from glob import glob
import argparse
import os

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('-b', dest='base', help='Results archives base folder', required=True)
    parser.add_argument('-o', dest='outfile', help='Output path', required=True)
    parser.add_argument('--ext', dest='ext', help='Archives extension', required=False, default='tar.gz')
    args = parser.parse_args()
    
    tars = glob(os.path.abspath(args.base) + '/*.' + args.ext)
    for tar in tars:
        print('[INFO] working on ' + tar)
        cfgpath = os.path.splitext(os.path.basename(tar))[0] + '/read_03_input.cfg'
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
                os.system('tar --extract --file={0} {1}'.format(tar, cfgpath)
                print('       read_03_input.cfg extracted')
        with open(cfgpath, 'r') as cp:
            cfg = configparser.ConfigParser()
            cfg.readfp(cp)
            sample_name = [str(c) for c in cfg.sections() if str(c).startswith('Z')][0]
            sample_XS = str(cfg.get(sample_name, 'XS')) # pb
        with open(args.outfile, 'w+') as o:
            o.write(sample_name + '\t' + sample_XS + '\n')
        os.system('rm -rf ' + cfgdir)

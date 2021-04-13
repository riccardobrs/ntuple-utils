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

    rmdir = False
    
    tars = glob(os.path.abspath(args.base) + '/*.' + args.ext)
    for tar in tars:

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

        with open(cfgpath, 'r') as cp:
            cfg = configparser.ConfigParser()
            cfg.readfp(cp)
            sample_name = [str(c) for c in cfg.sections() if str(c).startswith('Z')][0]
            sample_XS = str(cfg.get(sample_name, 'XS')) # pb

        with open(args.outfile, 'a') as o:
            o.write("samples['{0}'].extend( ['xsec={1}',      'kfact=1.00',           'ref=X'] )\n".format(sample_name,sample_XS))

        if rmdir:    
            os.system('rm -rf ' + cfgdir)

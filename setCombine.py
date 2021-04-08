import argparse
import configparser
from glob import glob
import os

    
if __name__ == '__main__':

    print("""
 _____________ 
  Set combine  
 ------------- """)

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('--cfg', dest='config', help='Config .cfg file path containing infos',
                            required=True)
    args = parser.parse_args()

    cfg = configparser.ConfigParser()
    cfg.readfp(open(args.config, 'r')) # this method will be deprecated

    # retrieve infos from config
    baseDir = cfg.get('general', 'basedir').strip()
    models = cfg.get('general', 'model').split(',')
    prefix = cfg.get('general', 'prefix').strip()
    proc = cfg.get('general', 'process').strip()
    fitfile = cfg.get('fit', 'file').strip()
    fitpoints = cfg.get('fit', 'points').strip()

    combine1 = 'combine -M MultiDimFit model.root  --algo=grid --points ' + fitpoints
    combine1 = combine1 + '  -m 125   -t -1   --robustFit=1 --X-rtd FITTER_NEW_CROSSING_ALGO'
    combine1 = combine1 + ' --X-rtd FITTER_NEVER_GIVE_UP --X-rtd FITTER_BOUND --redefineSignalPOIs'

    workdirs = glob('{0}/{1}_{2}_*'.format(baseDir, prefix, proc))
    for wd in workdirs:
        ops = os.path.basename(wd).replace(prefix + '_' + proc + '_', '')
        op1 = ops.split('_')[1].strip()
        op2 = ops.split('_')[0].strip()
        combine2 = combine1 + ' k_{0},k_{1}'.format(op1,op2)
        combine2 = combine2 + '     --freezeParameters r      --setParameters r=1    --setParameterRanges'
        for model in models:
            fitsh = wd + '/' + model.strip() + '/' + fitfile
            print ('Writing ' + fitsh)
            with open(fitsh, 'w') as f:
                f.write('#-----------------------------------\n')
                f.write('#     Automatically generated       #\n')
                f.write('#        by setCombine.py           #\n')
                f.write('#-----------------------------------\n\n\n\n')
                for var in dict(cfg.items(op1+':'+op2)).keys():
                    ranges = cfg.get(op1+':'+op2, var).split(',')
                    r1 = ranges[0].replace(':',',').strip()
                    r2 = ranges[1].replace(':',',').strip()
                    combine3 = combine2 + ' k_{0}={1}:k_{2}={3}  --verbose -1'.format(op2,r2,op1,r1)
                    f.write('#-----------------------------------\n')
                    f.write('cd datacards/{0}_{1}/{2}\n'.format(proc,ops,var))
                    f.write(combine3 + '\n')
                    f.write('cd ../../..\n\n\n')

    print ('\n. . . End process . . .')
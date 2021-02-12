import ROOT
import argparse
import configparser
from array import array
import sys
import glob
import os
import logging
import pandas as pd
from datetime import datetime
from common.ntupleCommon import getTreeName, getNtuple, getHisto


def rwgtObjects (couplingList, nameList, notusedList):

    keys = [rwgt.strip() for rwgt in couplingList]
    used = [rwgt.strip() for rwgt in nameList]
    notused = [rwgt.strip() for rwgt in notusedList]

    if len(keys) == len(used):

        used_dict = dict(zip(keys, used))
        return keys, used, notused, used_dict

    else: raise IndexError ('In config file <name> and <coupling> have different sizes')


def getEvents (ntuple, variables, nominal_wgt, rwgt, fit, imagesN, imagesDir):

    outevents_sm = []
    outevents_li = []
    outevents_qu = []

    sum_nominal_weight = 0.
    sum_rwgt_sm = 0.
    sum_rwgt_li = 0.
    sum_rwgt_qu = 0.

    quad_null = 0
    quad_neg = 0

    leaves = {k: ntuple.GetLeaf(k) for k in variables}
    w = ntuple.GetLeaf(nominal_wgt)
    rwgt0 = ntuple.GetLeaf(rwgt['0.0'])
    rwgtp1 = ntuple.GetLeaf(rwgt['1.0'])
    rwgtm1 = ntuple.GetLeaf(rwgt['-1.0'])
    xvec = [1.0, -1.0, 0.0]
    if fit:
        ROOT.gStyle.SetOptFit(1112)
        fit_results = []
        neg_bsm_results = []
        try:
            rwgtp2 = ntuple.GetLeaf(rwgt['2.0'])
            rwgtm2 = ntuple.GetLeaf(rwgt['-2.0'])
            xvec.append (2.0)
            xvec.append (-2.0)
            p5 = True
        except:
            print ('[WARNING] rwgt(2) and rwgt(-2) are not defined')
            p5 = False

    print ('[INFO] reading SM + LI + QU ntuple')
    
    for i in range(0, ntuple.GetEntries()):

        values_sm = []
        values_li = []
        values_qu = []

        ntuple.GetEntry(i)

        sum_nominal_weight += w.GetValue ()
        a = rwgtp1.GetValue ()
        b = rwgtm1.GetValue ()
        c = rwgt0.GetValue ()

        if fit:

            yvec = []
            yvec.append (a / w.GetValue())
            yvec.append (b / w.GetValue())
            yvec.append (c / w.GetValue())
            if p5:
                yvec.append (rwgtp2.GetValue() / w.GetValue())
                yvec.append (rwgtm2.GetValue() / w.GetValue())
            analit_qu = 0.5 * (a + b - 2 * c) / w.GetValue()
            analit_li = 0.5 * (a - b) / w.GetValue()
            analit_sm = c / w.GetValue()
            graph = ROOT.TGraph (len(xvec), array('d', xvec), array('d', yvec))
            graph.SetTitle('')
            graph.SetMarkerStyle(20)
            graph.GetXaxis().SetTitle('coupling')
            graph.GetYaxis().SetTitle('rwgt / nominal wgt')
            fit_f = ROOT.TF1 ('fit_f', '[0]*x*x + [1]*x + [2]', min(xvec), max(xvec))
            fit_f.SetParName (0, 'QU')
            fit_f.SetParName (1, 'LI')
            fit_f.SetParName (2, 'SM')
            fit_f.SetParameter(0, analit_qu)
            fit_f.SetParameter(1, analit_li)
            fit_f.SetParameter(2, analit_sm)
            if i < imagesN :
                parab = ROOT.TF1 ('parab', '{0}*x*x + {1}*x + {2}'.format(
                    analit_qu, analit_li, analit_sm), min(xvec), max(xvec))
                parab.SetLineColor(ROOT.kBlue)
                fit_f.SetLineColor(ROOT.kRed)
                canva = ROOT.TCanvas()
                canva.cd()
                graph.Draw('AP')
                parab.Draw('SAME')
                leg = ROOT.TLegend()
                leg.AddEntry(fit_f, 'Fit', 'L')
                leg.AddEntry(parab, 'Analytical', 'L')
                leg.Draw()
            graph.Fit('fit_f')
            w_sm = fit_f.GetParameter(2) * w.GetValue ()
            w_li = fit_f.GetParameter(1) * w.GetValue ()
            w_qu = fit_f.GetParameter(0) * w.GetValue ()
            fit_res = [fit_f.GetParameter(0), fit_f.GetParError(0), fit_f.GetParameter(1),
                        fit_f.GetParError(1), fit_f.GetChisquare(), fit_f.GetNDF(), fit_f.GetProb()]
            fit_results.append(array('d', fit_res))
            if w_qu < 0:
                if fit_f.GetParameter(0) + fit_f.GetParError(0) < 0:
                    neg_bsm_res = [fit_f.GetParameter(0), fit_f.GetParError(0)]
                    neg_bsm_results.append(array('d', neg_bsm_res))
            if i < imagesN :
                canva.SaveAs('{0}/event_{1}.png'.format(imagesDir, i))
                canva.SaveAs('{0}/event_{1}.root'.format(imagesDir, i))
            
        else:
            
            w_sm = c
            w_li = 0.5 * (a - b)
            w_qu = 0.5 * (a + b - 2 * c)

        sum_rwgt_sm += w_sm
        sum_rwgt_li += w_li
        sum_rwgt_qu += w_qu
        if w_qu == 0 : quad_null = 1 + quad_null
        if w_qu < 0:
            w_qu = 0
            quad_neg = 1 + quad_neg

        for (key, val) in sorted(leaves.items(), key=lambda x: x[1]):
            if key == nominal_wgt:
                values_sm.append(w_sm)
                values_li.append(w_li)
                values_qu.append(w_qu)
            else:
                values_sm.append(float(val.GetValue ()))
                values_li.append(float(val.GetValue ()))
                values_qu.append(float(val.GetValue ()))

        outevents_sm.append (array('f', values_sm))     
        outevents_li.append (array('f', values_li))
        outevents_qu.append (array('f', values_qu))
    
    if fit:
        df = pd.DataFrame(fit_results)
        if not df.empty:
            fit_columns = ['QU', 'QUerr', 'LI', 'LIerr', 'chi2', 'NDF', 'prob']
            df.columns = fit_columns
        df_neg = pd.DataFrame(neg_bsm_results)
        if not df_neg.empty:
            neg_columns = ['QU', 'QUerr']
            df_neg.columns = neg_columns
    else:
        df = pd.DataFrame()
        df_neg = pd.DataFrame()

    logging.info('sum of SM + LI + QU nominal weights: ' + str(sum_nominal_weight))
    logging.info('sum of new LI nominal weights: ' + str(sum_rwgt_li))
    logging.info('sum of new QU nominal weights: ' + str(sum_rwgt_qu))

    print ('[INFO] sum of SM + LI + QU nominal weights: ' + str(sum_nominal_weight))
    print ('[INFO] sum of new LI nominal weights: ' + str(sum_rwgt_li))
    print ('[INFO] sum of new QU nominal weights: ' + str(sum_rwgt_qu))

    resultsDict = {
        'events_sm': outevents_sm,
        'events_li': outevents_li,
        'events_qu': outevents_qu,
        'sum_nominal_weight': sum_nominal_weight,
        'sum_rwgt_sm': sum_rwgt_sm,
        'sum_rwgt_li': sum_rwgt_li,
        'sum_rwgt_qu': sum_rwgt_qu,
        'quad_null': quad_null,
        'quad_neg': quad_neg,
        'fit_df': df,
        'neg_df': df_neg
    }

    return resultsDict

def remember (x):

    global found_op
    found_op = x

    return True


if __name__ == '__main__':

    print("""
 _____________________________________ 
  Extract LI and QU from SM + LI + QU 
 ------------------------------------- """)

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('--cfg', dest='config', help='Config .cfg file path containing reweights', required=True)
    parser.add_argument('--sm', dest='sm', help='Extract SM component', type=bool, default=False, required=False)
    parser.add_argument('--li', dest='li', help='Extract linear component', type=bool, default=True, required=False)
    parser.add_argument('--qu', dest='qu', help='Extract quadratic component', type=bool, default=True, required=False)
    parser.add_argument('--fit', dest='fit', help='Using a parabolic fit', default=False, action='store_true', required=False)
    parser.add_argument('--png', dest='png', help='How many fit to be saved', type=int, default=0, required=False)
    args = parser.parse_args()

    if not args.li and not args.qu:
        sys.exit('Nothing to be extracted')

    cfg = configparser.ConfigParser()
    cfg.readfp(open(args.config, 'r'))

    # retrieve infos from config
    ntupleDir = cfg.get('ntuple', 'dir')
    ntupleDir = ntupleDir + '/' + cfg.get('subdir', 'proc')
    operators = cfg.get('operator', 'name').split(',')
    stateOut = cfg.get('tobemerged', 'out').strip()
    staticParts = cfg.get('ntuple', 'static').split(',')
    w = cfg.get('variables', 'nominalwgt').strip()
    ntupleSuffix = cfg.get('ntuple', 'suffix').strip()
    histoSuffix = cfg.get('histogram', 'suffix').strip()
    histoTitle = cfg.get('histogram', 'title').strip()
    logfile = ntupleDir + '/' + datetime.now().strftime('%Y%m%d-%H%M%S-extractComponents.log')
    logging.basicConfig(format='%(asctime)s :: %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                            filename=logfile, level=logging.INFO)
    # get rwgt lists
    if 'notused' in dict(cfg.items('reweights')).keys():
        notused = cfg.get ('reweights', 'notused').split(',')
    else:
        notused = []
    rwgt_keys, rwgt_used, rwgt_notused, rwgt_dict = rwgtObjects (
        cfg.get ('reweights', 'coupling').split(','),
        cfg.get ('reweights', 'name').split(','),
        notused
    )

    files = [f for f in glob.glob(ntupleDir + '/ntuple*' + ntupleSuffix + '.root') if stateOut in f]
    
    for ntupleFileIn in files:

        if not any(op.strip() in os.path.basename(ntupleFileIn).split('_') and
            remember (op.strip()) for op in operators) : continue
        
        imagesDir = ntupleDir + '/' + found_op
        if args.png > 0 and not os.path.isdir (imagesDir) : os.mkdir (imagesDir)

        ntupleFileIn = ntupleFileIn.strip()
        ntupleNameIn = getTreeName (os.path.basename(ntupleFileIn), staticParts)
        histoNameIn = ntupleNameIn + histoSuffix

        logging.info('working on ' + ntupleNameIn.replace(ntupleSuffix, ''))
        print ('\n\tNtuple file-in   =  ' + ntupleFileIn)
        print ('\tTNtuple name-in  =  ' + ntupleNameIn)
        print ('\tTH1F name-in     =  ' + histoNameIn + '\n')

        f_in = ROOT.TFile (ntupleFileIn, 'READ')
        t = ROOT.gDirectory.Get (ntupleNameIn)
        h = ROOT.gDirectory.Get (histoNameIn)
        overallXS = h.GetBinContent(1)
        logging.info('overall XS: ' + str(overallXS))
        print ('[INFO] overall XS: ' + str(overallXS))
            
        leaves = t.GetListOfLeaves()
        vars_wrwgt = [leaves.At(i).GetName() for i in range(0, leaves.GetEntries())]
        # variables for final ntuple
        vars = [v for v in vars_wrwgt if v not in list(set(rwgt_used)|set(rwgt_notused))]
        vars.sort()

        events_dictionary = getEvents (t, vars, w, rwgt_dict, args.fit, args.png, imagesDir)

        eventsSM = events_dictionary['events_sm']
        eventsLI = events_dictionary['events_li']
        eventsQU = events_dictionary['events_qu']
        SumWgtOld = events_dictionary['sum_nominal_weight']
        SumWgtSM = events_dictionary['sum_rwgt_sm']
        SumWgtLI = events_dictionary['sum_rwgt_li']
        SumWgtQU = events_dictionary['sum_rwgt_qu']
        q_null = events_dictionary['quad_null']
        q_neg = events_dictionary['quad_neg']
        fit_dataframe = events_dictionary['fit_df']
        negBsm_dataframe = events_dictionary['neg_df']

        f_in.Close()

        if q_null > 0:
            logging.warning(str(q_null) + ' events give BSM nominal weight = 0')
            print ('[WARNING] {0}: {1} events give BSM nominal weight = 0'.format(ntupleNameIn, q_null))
        if q_neg > 0:
            logging.warning(str(q_neg) + ' events give BSM nominal weight < 0. Setting them to 0')
            print ('[WARNING] {0}: {1} events give BSM nominal weight < 0. Setting them to 0'.format(ntupleNameIn, q_neg))

        if not fit_dataframe.empty:
            csvfitFile = ntupleFileIn.replace(ntupleSuffix, '').replace('.root', '.csv').replace('ntuple_', '').strip()
            print ('[INFO] writing fit results to ' + os.path.basename(csvfitFile))
            fit_dataframe.to_csv(csvfitFile, index=False)
            if not negBsm_dataframe.empty:
                csvNegBSM = csvfitFile.replace('.csv', '_QU_neg.csv')
                print ('[WARNING] writing negative BSM fit results to ' + os.path.basename(csvNegBSM))
                negBsm_dataframe.to_csv(csvNegBSM, index=False)

        for component in ['SM', 'LI', 'QU']:

            if component == 'SM':
                if args.sm:
                    eventsExtr = eventsSM
                    SumWgtExtr = SumWgtSM
                else: continue
            elif component == 'LI':
                if args.li:
                    eventsExtr = eventsLI
                    SumWgtExtr = SumWgtLI
                else: continue
            elif component == 'QU':
                if args.qu:
                    eventsExtr = eventsQU
                    SumWgtExtr = SumWgtQU
                else: continue
            
            XS = overallXS * SumWgtExtr / SumWgtOld
            logging.info('XSec({0}) =  {1}'.format(component, XS))

            if component == 'SM':
                ntupleFileOut = 'ntuple_ZV_SM.root'
                ntupleNameOut = 'ZV_SM'
                histoNameOut =  'ZV_SM_nums'
            else:
                ntupleFileOut = ntupleFileIn.replace(ntupleSuffix, '_' + component).strip()
                ntupleNameOut = ntupleNameIn.replace(ntupleSuffix, '_' + component).strip()
                histoNameOut = ntupleNameOut + histoSuffix

            print ('\n\tNtuple file-out  =  ' + ntupleFileOut)
            print ('\tTNtuple name-out =  ' + ntupleNameOut)
            print ('\tTH1F name-out    =  ' + histoNameOut + '\n')
            
            t = getNtuple (ntupleNameOut, ntupleNameOut, vars, eventsExtr)
            h = getHisto (histoNameOut, histoTitle, XS, SumWgtExtr, SumWgtExtr)

            f_out = ROOT.TFile (ntupleFileOut, 'RECREATE')

            print ('[INFO] writing ROOT file')
            t.Write()
            h.Write()
            
            f_out.Close()

    print ('\n[INFO] end process')
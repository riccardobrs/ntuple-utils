from glob import glob
import ROOT
import ctypes
from math import *
import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('--basesm', dest='basesm', help='Base folder that contains root files', required=True)
    parser.add_argument('--basebsm', dest='basebsm', help='Base folder that contains root files', required=True)
    parser.add_argument('-o', dest='out', help='Output folder', required=True)
    parser.add_argument('--sm', dest='sm', help='SM name convention', default='ZZ_SM', required=False)
    parser.add_argument('--bsm', dest='bsm', help='BSM name convention', default='ZZ_cqq31_SM_LI_QU', required=False)
    args = parser.parse_args()

    vars = [('Jet_pt[0]','1', 800), ('Jet_pt[1]','2', 700), ('Jet_pt[2]','3', 400), ('Jet_pt[3]','4', 400)]

    xmin = 0.

    ROOT.gStyle.SetOptStat(0)

    sm_files = glob('{0}/*{1}*.root'.format(args.basesm, args.sm))
    bsm_files = glob('{0}/*{1}*.root'.format(args.basebsm, args.bsm))

    sm_chain = ROOT.TChain('Events')
    bsm_chain = ROOT.TChain('Events')

    sm = (sm_chain, sm_files)
    bsm = (bsm_chain, bsm_files)

    for model in [sm, bsm]:
        for f in model[1]:
            model[0].Add(f)

    for var in vars:

        n = var[1]
        xmax = var[2]

        canva = ROOT.TCanvas('canva{0}'.format(n), 'canva{0}'.format(n))

        sm_h = ROOT.TH1F('jet-pt-{0}'.format(n), 'Jet pt {0} (GeV)'.format(n), int(xmax/10), xmin, xmax)
        bsm_h = ROOT.TH1F('reweighted-{0}'.format(n), 'reweighted-{0}'.format(n), int(xmax/10), xmin, xmax)

        sm_h.Sumw2()
        bsm_h.Sumw2()

        sm_h.GetXaxis().SetTitle ('Jet p_{T}^{'+n+'} (GeV)')
        sm_h.GetYaxis().SetTitle ('Events')
        bsm_h.SetLineColor(ROOT.kRed)

        ROOT.gROOT.cd()

        pad1 = ROOT.TPad('pad1-{0}'.format(n), 'pad1-{0}'.format(n), 0, 0.28, 1, 1)
        pad1.SetBottomMargin(0)
        pad1.SetRightMargin(0.04)
        pad1.SetLeftMargin(0.13)
        pad1.SetTickx(1)
        pad1.SetTicky(1)
        pad1.Draw()
        
        canva.cd()
        
        pad2 = ROOT.TPad('pad2-{0}'.format(n), 'pad2-{0}'.format(n), 0, 0.0, 1, 0.28)
        pad2.SetTopMargin(0) # joins upper and lower plot
        pad2.SetRightMargin(0.04)
        pad2.SetLeftMargin(0.13)
        pad2.SetBottomMargin(0.13)
        pad2.SetGridx()
        pad2.SetGridy()
        pad2.SetTickx(1)
        pad2.SetTicky(1)
        pad2.Draw()
        
        canva.Modified()
        canva.Update()
        
        pad1.cd()
        sm_chain.Draw('{0}>>jet-pt-{1}'.format(var[0], n), 'XSWeight', 'HIST')
        #bsm_chain.Draw('{0}>>reweighted-{1}'.format(var[0], n), 'XSWeight*LHEReweightingWeight[0]', 'SAME')
        bsm_chain.Draw('{0}>>reweighted-{1}'.format(var[0], n), 'XSWeight', 'SAME')
        #sm_h.SetTitle('SM')
        sm_h.SetTitle('Official')
        #bsm_h.SetTitle('Reweighted')
        bsm_h.SetTitle('Private')
        pad1.BuildLegend()
        sm_h.SetTitle('Jet^{'+n+'} p_{T} (GeV)')

        pad2.cd()
        h_ratio_vs = bsm_h.Clone('ratio_vs')
        #h_ratio_vs.GetYaxis().SetTitle('Reweighted/SM')
        h_ratio_vs.GetYaxis().SetTitle('Private/Official')
        h_ratio_vs.SetStats(0)
        h_ratio_vs.Divide (sm_h)
        h_ratio_vs.SetTitle('')
        h_ratio_vs.GetXaxis().SetLabelSize (0.09)
        h_ratio_vs.GetYaxis().SetLabelSize (0.09)
        h_ratio_vs.GetXaxis().SetTitleSize (0.09)
        h_ratio_vs.GetYaxis().SetTitleSize (0.09)
        h_ratio_vs.GetYaxis().SetTitleOffset (0.4)

        h_ratio_same = sm_h.Clone('ratio_same')
        #h_ratio_same.GetYaxis().SetTitle('Reweighted/SM')
        h_ratio_same.GetYaxis().SetTitle('Private/Official')
        h_ratio_same.SetStats(0)
        h_ratio_same.Divide (sm_h)
        h_ratio_same.SetTitle ('')
        h_ratio_same.GetXaxis().SetLabelSize (0.09)
        h_ratio_same.GetYaxis().SetLabelSize (0.09)
        h_ratio_same.GetXaxis().SetTitleSize (0.09)
        h_ratio_same.GetYaxis().SetTitleSize (0.09)
        h_ratio_same.GetYaxis().SetTitleOffset (0.4)

        h_ratio_same.SetFillStyle(3013)
        h_ratio_same.SetFillColor(13)
        h_ratio_same.SetMarkerStyle(1)
        h_ratio_vs.Draw()
        h_ratio_same.Draw('E2 SAME')
        
        canva.Modified()
        canva.Update()
        canva.SaveAs('{0}/compare_ptj{1}.pdf'.format(args.out, n))
        canva.SaveAs('{0}/compare_ptj{1}.root'.format(args.out, n))

        sm_e = ctypes.c_double()
        sm_i = sm_h.IntegralAndError(int(xmin), int(xmax), sm_e, '')
        bsm_e = ctypes.c_double()
        bsm_i = bsm_h.IntegralAndError(int(xmin), int(xmax), bsm_e, '')

        sm_e = sm_e.value
        bsm_e = bsm_e.value

        #print('Integral (SM): {0} +- {1}'.format(sm_i, sm_e))
        #print('Integral (reweighted): {0} +- {1}'.format(bsm_i, bsm_e))
        print('Integral (Official): {0} +- {1}'.format(sm_i, sm_e))
        print('Integral (Private): {0} +- {1}'.format(bsm_i, bsm_e))
        print('Sigma: {0}'.format(abs(bsm_i-sm_i)/sqrt(sm_e**2 + bsm_e**2)))
import ROOT
from glob import glob
import argparse
from itertools import combinations


def get_mmjj(chain, nmax):

    result = dict()
    mmjj_wgt_list = list()
    sum_wgt = 0.

    if nmax is None:
        nmax = chain.GetEntries()
    elif nmax <= 0:
        nmax = chain.GetEntries()

    s = nmax / 100

    for n,event in enumerate(chain):
        
        if n >= nmax: break
        if (n%s == 0) and (n/s <= 100): print('>>> reading events: {0}%'.format(n/s))

        # incoming particles have status -1, outgoing particles status 1
        out_indices = [i for i,status in enumerate(list(event.LHEPart_status)) if status==1] # outgoing
        out_partons_indices = [i for i in out_indices if abs(event.LHEPart_pdgId[i])>=1 and abs(event.LHEPart_pdgId[i])<=6] # partons
        
        mjj_list = list()

        # all possible combinations
        for indices in combinations(out_partons_indices, 2):

            pt_j1 = event.LHEPart_pt[indices[0]]
            eta_j1 = event.LHEPart_eta[indices[0]]
            phi_j1 = event.LHEPart_phi[indices[0]]
            m_j1 = event.LHEPart_mass[indices[0]]

            pt_j2 = event.LHEPart_pt[indices[1]]
            eta_j2 = event.LHEPart_eta[indices[1]]
            phi_j2 = event.LHEPart_phi[indices[1]]
            m_j2 = event.LHEPart_mass[indices[1]]

            qvec_j1 = ROOT.TLorentzVector()
            qvec_j2 = ROOT.TLorentzVector()

            qvec_j1.SetPtEtaPhiM(pt_j1, eta_j1, phi_j1, m_j1)
            qvec_j2.SetPtEtaPhiM(pt_j2, eta_j2, phi_j2, m_j2)

            mjj = (qvec_j1 + qvec_j2).M() # dijet invariant mass
            mjj_list.append(mjj)
        
        xsec = event.Xsec
        mmjj = min(mjj_list) # minimum dijet invariant mass
        xwgtup = event.LHEWeight_originalXWGTUP
        mmjj_wgt_list.append((mmjj, xwgtup))
        sum_wgt += xwgtup
    
    result['events'] = mmjj_wgt_list
    result['sum_wgt'] = sum_wgt
    result['xsec'] = xsec
        
    return result


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('--official', dest='official', help='Official nanoAODv7 base folder', required=True)
    parser.add_argument('--private', dest='private', help='Private nanoAODv7 base folder', required=True)
    parser.add_argument('--prefixoff', dest='prefixoff', help='Official production prefix (comma separated list)', required=False, default='WmTo2J_ZTo2L,WpTo2J_ZTo2L,ZTo2L_ZTo2J')
    parser.add_argument('--prefixpriv', dest='prefixpriv', help='Private production prefix (comma separated list)', required=False, default='ZWm_SM,ZWp_SM,ZZ_SM')
    parser.add_argument('-N', dest='N', help='Max number of events to be considered', required=False, type=int)
    parser.add_argument('--LWidth', dest='LWidth', help='Line width', required=False, type=int, default=1)
    parser.add_argument('--hist', dest='hist', help='Draw with HIST option', required=False, action='store_true', default=False)
    parser.add_argument('--err', dest='err', help='Draw with E option', required=False, action='store_true', default=False)
    parser.add_argument('--lumi', dest='lumi', help='Integrated luminosity [1/fb]', required=False, type=float, default=100.)
    parser.add_argument('-o', dest='outdir', help='Output folder', required=True)
    args = parser.parse_args()

    official_chain = ROOT.TChain('Events')
    private_chain = ROOT.TChain('Events')

    official_files = list()
    private_files = list()

    lumi = args.lumi*1000. # 1/fb to 1/pb conversion

    for p in args.prefixoff.split(','):
        official_files = official_files + glob(args.official + '/nanoLatino*{0}*.root'.format(p.strip()))

    for p in args.prefixpriv.split(','):
        private_files = private_files + glob(args.private + '/nanoLatino*{0}*.root'.format(p.strip()))
    
    for f in official_files:
        official_chain.Add(f)
    
    for f in private_files:
        private_chain.Add(f)
    
    results_official = get_mmjj(official_chain, args.N)
    results_private = get_mmjj(private_chain, args.N)

    events_official = results_official['events']
    events_private = results_private['events']

    sum_wgt_official = results_official['sum_wgt']
    sum_wgt_private = results_private['sum_wgt']

    xsec_official = results_official['xsec']
    xsec_private = results_private['xsec']
    print('Official xsec = {0}'.format(xsec_official))
    print('Private xsec = {0}'.format(xsec_private))

    xmax = max([x[0] for x in (events_official + events_private)])

    mmjj_canva = ROOT.TCanvas()
    mmjj_histo_official = ROOT.TH1D('mmjj', '', 20, 0., xmax)
    mmjj_histo_private = ROOT.TH1D('mmjj_private', '', 20, 0., xmax)
    
    for x in events_official:
        wgt = x[1]*xsec_official*lumi/sum_wgt_official
        mmjj_histo_official.Fill(x[0], wgt)

    for x in events_private:
        wgt = x[1]*xsec_private*lumi/sum_wgt_private
        mmjj_histo_private.Fill(x[0], wgt)
    
    draw_opt = ''
    if args.hist:
        draw_opt += 'HIST'
        if args.err:
            draw_opt += ' E'

    mmjj_canva.cd()
    mmjj_histo_official.GetXaxis().SetTitle('min m_{jj} [GeV]')
    mmjj_histo_official.GetYaxis().SetTitle('Events')
    mmjj_histo_official.SetLineColor(ROOT.kBlue)
    mmjj_histo_official.SetLineWidth(args.LWidth)
    mmjj_histo_official.Draw(draw_opt)
    mmjj_histo_private.GetXaxis().SetTitle('min m_{jj} [GeV])
    mmjj_histo_private.GetYaxis().SetTitle('Events')
    mmjj_histo_private.SetLineColor(ROOT.kRed)
    mmjj_histo_private.SetLineWidth(args.LWidth)
    mmjj_histo_private.Draw((draw_opt+' SAME').strip())
    mmjj_canva.SaveAs(args.outdir + '/LHE_mmjj.root')
    mmjj_canva.SaveAs(args.outdir + '/LHE_mmjj.pdf')

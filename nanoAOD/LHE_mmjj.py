import ROOT
from glob import glob
import argparse
from itertools import combinations


global mV
mV = 80.379 # GeV


def mjjCombinations(event, indices_to_be_combined):

    mjj_list = list()
    detajj_list = list()

    # all possible combinations
    for indices in combinations(indices_to_be_combined, 2):

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
        detajj_list.append(abs(eta_j1 - eta_j2))
    
    return zip(mjj_list, detajj_list)


def get_mmjj(chain, nmax):

    result = dict()
    mmjj_wgt_list = list()
    mmjjToV_wgt_list = list()
    mmjjqqbar_wgt_list = list()
    mjjmax_wgt_list = list()

    sum_wgt = 0.
    ele = 0
    mu = 0
    tau = 0
    ele_weighted = 0.
    mu_weighted = 0.
    tau_weighted = 0.

    if nmax is None:
        nmax = chain.GetEntries()
    elif nmax <= 0:
        nmax = chain.GetEntries()

    s = nmax / 100

    print('\n>>> start reading events')

    for n,event in enumerate(chain):
        
        if n >= nmax: break
        if (n%s == 0) and (n/s <= 100): print('    events read: {0}%'.format(n/s))

        # incoming particles have status -1, outgoing particles status 1
        out_indices = [i for i,status in enumerate(list(event.LHEPart_status)) if status==1] # outgoing
        out_partons_indices = [i for i in out_indices if abs(event.LHEPart_pdgId[i])>=1 and abs(event.LHEPart_pdgId[i])<=6] # partons
        out_ele_indices = [i for i in out_indices if abs(event.LHEPart_pdgId[i])==11]
        out_mu_indices = [i for i in out_indices if abs(event.LHEPart_pdgId[i])==13]
        out_tau_indices = [i for i in out_indices if abs(event.LHEPart_pdgId[i])==15]

        if any(event.LHEPart_pdgId[x[0]] == -event.LHEPart_pdgId[x[1]] for x in combinations(out_partons_indices, 2)):
            out_partons_qqbar_indices = out_partons_indices
        else:
            out_partons_qqbar_indices = list()

        if len(out_partons_indices) != 4:
            print('[WARNING] found {0} partons in event number {1}'.format(len(out_partons_indices),n))

        mjj_detajj_list = mjjCombinations(event, out_partons_indices)
        
        xsec = event.Xsec # pb
        xwgtup = event.LHEWeight_originalXWGTUP # LHE nominal weight
        sum_wgt += xwgtup

        if len(out_ele_indices)==2:
            ele += 1
            ele_weighted += xwgtup
        if len(out_mu_indices)==2:
            mu += 1
            mu_weighted += xwgtup
        if len(out_tau_indices)==2:
            tau += 1
            tau_weighted += xwgtup

        mmjj = min(mjj_detajj_list)[0] # minimum dijet invariant mass
        mmjj_toV = min(mjj_detajj_list, key=lambda x: abs(x[0]-mV))[0] # dijet invariant mass closest to V
        mjjmax = max(mjj_detajj_list)[0] # max dijet invariant mass
        mdetajj = min(mjj_detajj_list)[1] # minimum dijet invariant mass
        mdetajj_toV = min(mjj_detajj_list, key=lambda x: abs(x[0]-mV))[1] # dijet invariant mass closest to V
        detajjmax = max(mjj_detajj_list)[1] # max dijet invariant mass
        
        mmjj_wgt_list.append((mmjj, xwgtup, xsec, mdetajj))
        mmjjToV_wgt_list.append((mmjj_toV, xwgtup, xsec, mdetajj_toV))
        mjjmax_wgt_list.append((mjjmax, xwgtup, xsec, detajjmax))

        if len(out_partons_qqbar_indices) > 0:
            
            mjj_detajj_qqbar_list = mjjCombinations(event, out_partons_qqbar_indices)
            mmjj_qqbar = min(mjj_detajj_qqbar_list)[0]
            mdetajj_qqbar = min(mjj_detajj_qqbar_list)[1]
            mmjjqqbar_wgt_list.append((mmjj_qqbar, xwgtup, xsec, mdetajj_qqbar))
    
    result['events_min'] = mmjj_wgt_list
    result['events_closestToV'] = mmjjToV_wgt_list
    result['events_min_qqbar'] = mmjjqqbar_wgt_list
    result['events_max'] = mjjmax_wgt_list
    result['sum_wgt'] = sum_wgt
    result['ele'] = (ele, ele_weighted)
    result['mu'] = (mu, mu_weighted)
    result['tau'] = (tau, tau_weighted)
        
    return result


def save_plots(h_official, h_private, xtitle, LWidth, draw_opt, outpath):

    ROOT.gStyle.SetOptStat(111111)

    canva = ROOT.TCanvas()
    canva.cd()
    h_official.GetXaxis().SetTitle(xtitle)
    h_official.GetYaxis().SetTitle('Events')
    h_official.SetLineColor(ROOT.kBlue)
    h_official.SetLineWidth(LWidth)
    h_official.Draw(draw_opt)
    h_private.GetXaxis().SetTitle(xtitle)
    h_private.GetYaxis().SetTitle('Events')
    h_private.SetLineColor(ROOT.kRed)
    h_private.SetLineWidth(LWidth)
    h_private.Draw((draw_opt+' SAME').strip())
    leg = ROOT.TLegend()
    leg.SetBorderSize(0)
    leg.SetNColumns(1)
    leg.SetTextSize(0.04)
    leg.AddEntry(h_official, 'VBS-Official', 'F')
    leg.AddEntry(h_private, 'VBS-Private', 'F')
    leg.Draw()
    for ext in ['.root', '.pdf']:
        canva.SaveAs(outpath + ext)

def save_plots2D(h, xtitle, ytitle, draw_opt, outpath):

    ROOT.gStyle.SetOptStat(111111)

    canva = ROOT.TCanvas()
    canva.cd()
    h.GetXaxis().SetTitle(xtitle)
    h.GetYaxis().SetTitle(ytitle)
    h.GetZaxis().SetTitle('Events')
    h.Draw(draw_opt)
    for ext in ['.root', '.pdf']:
        canva.SaveAs(outpath + ext)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('--official', dest='official', help='Official nanoAODv7 base folder', required=True)
    parser.add_argument('--private', dest='private', help='Private nanoAODv7 base folder', required=True)
    parser.add_argument('--prefixoff', dest='prefixoff', help='Official production prefix (comma separated list)', required=False, default='WmTo2J_ZTo2L,WpTo2J_ZTo2L,ZTo2L_ZTo2J')
    parser.add_argument('--prefixpriv', dest='prefixpriv', help='Private production prefix (comma separated list)', required=False, default='ZWm_SM,ZWp_SM,ZZ_SM')
    parser.add_argument('-N', dest='N', help='Max number of events to be considered', required=False, type=int)
    parser.add_argument('--LWidth', dest='LWidth', help='Line width', required=False, type=int, default=1)
    parser.add_argument('--hist', dest='hist', help='Draw 1D with HIST option', required=False, action='store_true', default=False)
    parser.add_argument('--err', dest='err', help='Draw 1D with E option', required=False, action='store_true', default=False)
    parser.add_argument('--th2draw', dest='th2draw', help='Draw 2D option', required=False, default='CONTZ')
    parser.add_argument('--lumi', dest='lumi', help='Integrated luminosity [1/fb]', required=False, type=float, default=59.7)
    parser.add_argument('-o', dest='outdir', help='Output folder', required=True)
    args = parser.parse_args()

    official_chain = ROOT.TChain('Events')
    private_chain = ROOT.TChain('Events')

    official_files = list()
    private_files = list()

    lumi = args.lumi * 1000. # 1/fb to 1/pb conversion

    for p in args.prefixoff.split(','):
        official_files = official_files + glob(args.official + '/nanoLatino_{0}__part*.root'.format(p.strip()))

    for p in args.prefixpriv.split(','):
        private_files = private_files + glob(args.private + '/nanoLatino_{0}__part*.root'.format(p.strip()))
    
    for f in official_files:
        official_chain.Add(f)
    
    for f in private_files:
        private_chain.Add(f)
    
    results_official = get_mmjj(official_chain, args.N)
    results_private = get_mmjj(private_chain, args.N)

    print('\n### Official production ###')
    print(' N events (unweighted) with e+ e-: {0}'.format(results_official['ele'][0]))
    print(' N events (unweighted) with mu+ mu-: {0}'.format(results_official['mu'][0]))
    print(' N events (unweighted) with tau+ tau-: {0}'.format(results_official['tau'][0]))
    print(' Yield events with e+ e-: {0}'.format(results_official['ele'][1]))
    print(' Yield events with mu+ mu-: {0}'.format(results_official['mu'][1]))
    print(' Yield events with tau+ tau-: {0}'.format(results_official['tau'][1]))
    print('\n### Private production ###')
    print(' N events (unweighted) with e+ e-: {0}'.format(results_private['ele'][0]))
    print(' N events (unweighted) with mu+ mu-: {0}'.format(results_private['mu'][0]))
    print(' N events (unweighted) with tau+ tau-: {0}'.format(results_private['tau'][0]))
    print(' Yield events with e+ e-: {0}'.format(results_private['ele'][1]))
    print(' Yield events with mu+ mu-: {0}'.format(results_private['mu'][1]))
    print(' Yield events with tau+ tau-: {0}'.format(results_private['tau'][1]))

    events_min_official = results_official['events_min']
    events_min_private = results_private['events_min']
    events_toV_official = results_official['events_closestToV']
    events_toV_private = results_private['events_closestToV']
    events_min_qqbar_official = results_official['events_min_qqbar']
    events_min_qqbar_private = results_private['events_min_qqbar']
    events_max_official = results_official['events_max']
    events_max_private = results_private['events_max']

    sum_wgt_official = results_official['sum_wgt']
    sum_wgt_private = results_private['sum_wgt']

    ymax_mdetajj = max([x[3] for x in (events_min_official + events_min_private)])
    xmax_mmjj = max([x[0] for x in (events_min_official + events_min_private)])
    xmax_mmjj_toV = max([x[0] for x in (events_toV_official + events_toV_private)])
    xmax_mmjj_qqbar = max([x[0] for x in (events_min_qqbar_official + events_min_qqbar_private)])

    mmjj_histo_official = ROOT.TH1F('min mjj', '', 40, 0., xmax_mmjj)
    mmjj_histo_private = ROOT.TH1F('min mjj private', '', 40, 0., xmax_mmjj)
    mmjj_toV_histo_official = ROOT.TH1F('mjj closest to V', '', 40, 0., xmax_mmjj_toV)
    mmjj_toV_histo_private = ROOT.TH1F('mjj closest to V private', '', 40, 0., xmax_mmjj_toV)
    mmjj_qqbar_histo_official = ROOT.TH1F('min mjj (qqbar)', '', 40, 0., xmax_mmjj_qqbar)
    mmjj_qqbar_histo_private = ROOT.TH1F('min mjj (qqbar) private', '', 40, 0., xmax_mmjj_qqbar)
    mjjmax_histo_official = ROOT.TH1F('max mjj', '', 50, 0., 150.)
    mjjmax_histo_private = ROOT.TH1F('max mjj private', '', 50, 0., 150.)
    mmjj_detajj_histo_official = ROOT.TH2F('min mjj vs detajj', '', 40, 0., xmax_mmjj, 20, 0., ymax_mdetajj)
    mmjj_detajj_histo_private = ROOT.TH2F('min mjj vs detajj private', '', 40, 0., xmax_mmjj, 20, 0., ymax_mdetajj)

    events_sumwgt_histos = [(events_min_official, sum_wgt_official, mmjj_histo_official, 'min'),
                            (events_min_private, sum_wgt_private, mmjj_histo_private, 'min'),
                            (events_toV_official, sum_wgt_official, mmjj_toV_histo_official, 'closest to V'),
                            (events_toV_private, sum_wgt_private, mmjj_toV_histo_private, 'closest to V'),
                            (events_min_qqbar_official, sum_wgt_official, mmjj_qqbar_histo_official, 'min (qqbar)'),
                            (events_min_qqbar_private, sum_wgt_private, mmjj_qqbar_histo_private, 'min (qqbar)'),
                            (events_max_official, sum_wgt_official, mjjmax_histo_official, 'max'),
                            (events_max_private, sum_wgt_private, mjjmax_histo_private, 'max')]
    
    #events_sumwgt_histos2D = [(events_min_official, sum_wgt_official, mmjj_detajj_histo_official, 'official'),
    #                        (events_min_private, sum_wgt_private, mmjj_detajj_histo_private, 'private')]
    
    draw_opt = ''
    if args.hist:
        draw_opt += 'HIST'
        if args.err:
            draw_opt += ' E'

    # 1D histograms
    for obj in events_sumwgt_histos:
        for x in obj[0]:
            wgt = x[1]*x[2]*lumi/obj[1]
            obj[2].Fill(x[0], wgt)
    
    # 2D histograms
    #for obj in events_sumwgt_histos2D:
    #
    #    for x in obj[0]:
    #        wgt = x[1]*x[2]*lumi/obj[1]
    #        obj[2].Fill(x[0], x[3], wgt)
    #
    #    save_plots2D(   obj[2], 'min m_{jj} [GeV]', '#Delta#eta_{jj}',
    #                    args.th2draw, args.outdir + '/LHE_mjj_detajj_' + obj[3])
    
    for obj_official,obj_private in zip(events_sumwgt_histos[0::2], events_sumwgt_histos[1::2]):

        save_plots ( obj_official[2], obj_private[2],
                    obj_official[3] + ' m_{jj} [GeV]',
                    args.LWidth, draw_opt,
                    args.outdir + '/LHE_mjj_' + obj_official[3].replace('(','').replace(')','').replace(' ','_') )

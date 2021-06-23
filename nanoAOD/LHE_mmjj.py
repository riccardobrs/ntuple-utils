import ROOT
from glob import glob
import argparse
from itertools import combinations


def get_mmjj(chain):

    mmjj_list = list()

    for event in chain:
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
        
        mmjj = min(mjj_list) # minimum dijet invariant mass
        mmjj_list.append(mmjj)
        
    return mmjj_list


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Command line parser')
    parser.add_argument('--official', dest='official', help='Official nanoAODv7 base folder', required=True)
    parser.add_argument('--private', dest='private', help='Private nanoAODv7 base folder', required=True)
    parser.add_argument('--prefixoff', dest='prefixoff', help='Official production prefix (comma separated list)', required=False, default='WmTo2J_ZTo2L,WpTo2J_ZTo2L,ZTo2L_ZTo2J')
    parser.add_argument('--prefixpriv', dest='prefixpriv', help='Private production prefix (comma separated list)', required=False, default='ZWm_SM,ZWp_SM,ZZ_SM')
    parser.add_argument('-o', dest='outdir', help='Output folder', required=True)
    args = parser.parse_args()

    official_chain = ROOT.TChain('Events')
    private_chain = ROOT.TChain('Events')

    official_files = list()
    private_files = list()

    for p in args.prefixoff.split(','):
        official_files = official_files + glob(args.official + '/nanoLatino*{0}*.root'.format(p.strip()))

    for p in args.prefixpriv.split(','):
        private_files = private_files + glob(args.private + '/nanoLatino*{0}*.root'.format(p.strip()))
    
    for f in official_files:
        official_chain.Add(f)
    
    for f in private_files:
        private_chain.Add(f)
    
    mmjjs_official = get_mmjj(official_chain)
    mmjjs_private = get_mmjj(private_chain)

    xmax = max((max(mmjjs_official), max(mmjjs_private)))

    mmjj_canva = ROOT.TCanvas()
    mmjj_histo_official = ROOT.TH1D('mmjj', '', 20, 0., xmax)
    mmjj_histo_private = ROOT.TH1D('mmjj_private', '', 20, 0., xmax)
    
    for x in mmjjs_official:
        mmjj_histo_official.Fill(x)

    for x in mmjjs_private:
        mmjj_histo_private.Fill(x)

    mmjj_canva.cd()
    mmjj_histo_official.SetLineColor(ROOT.kBlue)
    mmjj_histo_official.SetLineWidth(2)
    mmjj_histo_official.Draw()
    mmjj_histo_private.SetLineColor(ROOT.kRed)
    mmjj_histo_private.SetLineWidth(2)
    mmjj_histo_private.Draw('SAME')
    mmjj_canva.SaveAs(args.outdir + '/LHE_mmjj.root')
    mmjj_canva.SaveAs(args.outdir + '/LHE_mmjj.pdf')

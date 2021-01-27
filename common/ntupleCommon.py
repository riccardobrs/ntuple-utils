import ROOT


def getTreeName (filepath, conventions):

    if '/' in filepath:
        treeName = filepath.split('/')[1]
    else:
        treeName = filepath
        
    for s in conventions:
        treeName = treeName.replace(s.strip(), '')

    return treeName


def getNtuple (name, title, variables, events):

    ntuple = ROOT.TNtuple (name, title, ':'.join(variables))
    for e in events : ntuple.Fill(e)
    
    return ntuple


def getHisto (name, title, XS, sum_wgt_overall, sum_wgt_passed):

    histo = ROOT.TH1F (name, title, 3, 0, 3)
    histo.SetBinContent(1, XS)
    histo.SetBinContent(2, sum_wgt_overall)
    histo.SetBinContent(3, sum_wgt_passed)
    
    return histo

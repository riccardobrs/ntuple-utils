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
    

def rwgtObjects (couplingList, nameList, notusedList):

    keys = [rwgt.strip() for rwgt in couplingList]
    used = [rwgt.strip() for rwgt in nameList]
    notused = [rwgt.strip() for rwgt in notusedList]

    if len(keys) == len(used):

        used_dict = dict(zip(keys, used))
        return keys, used, notused, used_dict

    else: raise IndexError ('In config file <name2d> and <coupling2d> have different sizes')

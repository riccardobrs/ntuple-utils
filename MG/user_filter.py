def remove_diag(diag,model=None):
    """remove all diagrams with more than 1 vertex which are not QCD==2"""
    
    if len(diag['vertices']) > 1:
        if diag.get('orders')['QCD'] != 2:
            return True

    return False

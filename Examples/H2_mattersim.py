# Example script to get potential of H2 molecule from with MatterSim using ASE
# This should be run inside the MatterSim container.
from Matbench_Models import initialise_error, initialise_model

# check we have ASE installed properly
try:
    from ase import Atoms

except:
    initialise_error('ASE module cannot be found, please install ASE.')

from ase.optimize import BFGS
from ase.calculators.nwchem import NWChem
from ase.io import write

if __name__=='__main__':
    # path to the compiled model, inside the MatterSim container
    Compiled_Model_Path = 'MatterSim-v1.0.0-5M.pth'

    # Setup the system with ASE, in this case a simple H2 molecule
    h2 = Atoms('H2', positions=[[0, 0, 0],[0, 0, 0.7]])

    # Tell ASE to use MatterSim as a Calculator
    h2.calc = initialise_model('MatterSim',Compiled_Model_Path)

    # Do the calculations 
    opt = BFGS(h2)
    opt.run(fmax=0.02)
    write('H2.xyz', h2)
    h2.get_potential_energy()
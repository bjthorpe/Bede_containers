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
import numpy as np


if __name__=='__main__':
    d = 0.9575
    t = np.pi / 180 * 104.51
    # Setup the system with ASE, in this case a simple H2O molecule
    h2 = Atoms('H2O',positions=[(d, 0, 0),(d * np.cos(t), d * np.sin(t), 0),(0, 0, 0)],)

    # Tell ASE to use MatterSim as a Calculator
    h2.calc = initialise_model("esen-30m-oam")

    # Do the calculations 
    opt = BFGS(h2, trajectory='H2O.traj')
    opt.run(fmax=0.01)
    write('H2O.xyz', h2)
    energy = h2.get_potential_energy()
    print(f"potential = {energy} eV")

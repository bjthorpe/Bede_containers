# test script to get potential of H2 molecule from with MatterSim through ASE
# This should be run inside the MatterSim container.

from Matbench_Models import Get_ASE_Calculator
from ase import Atoms
from ase.optimize import BFGS
from ase.calculators.nwchem import NWChem
from ase.io import write
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("model", help="which model to use")
parser.add_argument("-t","--task", help="task to preform, if needed",default=None)
args = parser.parse_args()
# Setup the system with ASE, in this case a simple H2 molecule
h2 = Atoms('H2', positions=[[0, 0, 0],[0, 0, 0.7]])

# Tell ASE to use MatterSim as a Calculator

h2.calc = Get_ASE_Calculator(args.model,task=args.task,device='cpu')

# Do the calculations
opt = BFGS(h2)
opt.run(fmax=0.02)
print(h2.get_potential_energy())

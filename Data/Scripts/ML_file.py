#!/usr/bin/env python3

# General required modules
import sys
import os

# Use castep units module to convert to and from atomic units
from utility import castep_units
from Matbench_Models import Get_ASE_Calculator
from ase.io import read

def initialise_model(ML_model_option,ML_task=None,device='cpu'):
    '''
    Initialise the ML model, only need to do this once
    '''

    def initialise_error(message):
        print(f'ERROR: {message}')
        sys.exit(23)

    # Lists of valid model names
    Meta_OMat24 = [
        "esen-30m-oam",
        "esen-30m-mp",
        "eqv2_m",
        "eqv2-l-dens",
        "eqv2-m-dens",
        "eqv2-s-dens",
        "eqv2-s",
        "eqv2-s-oam",
        "eqv2-m-oam",
        "esen-30m-omat",
        "eqv2-s-omat",
        "eqv2-m-omat",
        "eqv2-l-omat",
    ]

    Meta_UMA = [
        "uma-s-1p1",
        "uma-s-1",
        "uma-m-1p1",
    ]

    MatterSim = ["mattersim"]

    Mace = ["mace"]

    NequIP = [
        'nequip-oam-xl',
        'allegro-oam-l',
        'nequip-oam-l',
        'allegro-mp-l',
        'nequip-mp-l',
    ]

    ML_model_option_lower=ML_model_option.lower()


    if ML_model_option_lower in MatterSim:

        try:
            from mattersim.forcefield import MatterSimCalculator
        except:
            initialise_error('MatterSim module cannot be found, please install.')

        try:
            from ase import Atoms
        except:
            initialise_error('ASE module cannot be found, please install.')

        ML_model = Get_ASE_Calculator(ML_model_option_lower,device=device)


    elif ML_model_option_lower in Mace:

        try:
            from mace.calculators import MACECalculator
        except:
            initialise_error('MACE module cannot be found, please install.')

        try:
            from ase import Atoms
        except:
            initialise_error('ASE module cannot be found, please install.')

        MACE_model_path = 'mace-omat-0-medium.model'

        if not os.path.exists(MACE_model_path):
            initialise_error(f'MACE model {MACE_model_path} not found.')

        ML_model = Get_ASE_Calculator(ML_model_option_lower,model_paths=MACE_model_path,
                                    default_dtype='float64',
                                    device=device)
    # Meta(facebook) OMAT24
    elif ML_model_option_lower in Meta_OMat24:

        try:
            from fairchem.core import OCPCalculator    
        except:
            initialise_error('fairchem (V1.10) module cannot be found, please install.')

        try:
            from ase import Atoms
        except:
            initialise_error('ASE module cannot be found, please install.')

        ML_model = Get_ASE_Calculator(ML_model_option_lower)

     # Meta(facebook) UMA
    elif ML_model_option_lower in Meta_UMA:

        try:
            from fairchem.core import pretrained_mlip, FAIRChemCalculator  
        except:
            initialise_error('fairchem (V2.13) module cannot be found, please install.')
        try:
            from ase import Atoms
        except:
            initialise_error('ASE module cannot be found, please install.')
        
        
        if not ML_task:
            initialise_error(f'Task must be specified for METa UMA model.\n\
                             This must be one of: oc20, omat, omol ,odac, or, omc".')
        

        ML_model = Get_ASE_Calculator(ML_model_option_lower,device=device,task=ML_task)

     # Nequip/Allegro
    elif ML_model_option_lower in NequIP:

        try:
            from nequip.integrations.ase import NequIPCalculator  
        except:
            initialise_error('NequIP module cannot be found, please install.')
        try:
            from ase import Atoms
        except:
            initialise_error('ASE module cannot be found, please install.')
        
        ML_model = Get_ASE_Calculator(ML_model_option_lower,device=device)
# will need to rethink this if needed!!
    # elif ML_model_option_lower == 'chgnet':

    #     try:
    #         from chgnet.model import CHGNet
    #     except:
    #         initialise_error('CHGNet module cannot be found, please install.')

    #     try:
    #         from pymatgen.core import Structure
    #     except:
    #         initialise_error('Pymatgen module cannot be found, please install.')

    #     ML_model = CHGNet.load(use_device='cpu')

    else:
        initialise_error(f'Unrecognised ML_model_option {ML_model_option}')
        ML_model=None

    return ML_model

class predict_from_cell:

    def __init__(self,seed,model_name,device):

        # Sort out inputs
        self.seed = seed
        self.model_name = model_name
        self.device       = device
        # Variables used on cell reading
        self.cell          = None
        self.num_ions      = None
        self.species_label = None

        # Empty variables for energy, stress and forces
        self.total_energy = None
        self.stress       = None
        self.forces       = None

    def check_cell_file_exists(self):
        '''
        Check that the cell file <seed>.cell exists, exit with error if not.
        '''

        if not os.path.isfile(f'{self.seed}.cell'):
            print(f'ERROR: Cell file {self.seed}.cell not found')
            sys.exit(3)

    def read_cell_file(self):
        '''
        Read the cell file and assign an ASE atoms object to the class variable cell.
        Also assign number of ions to num_ions.
        Finally, assign an array of strings with each element in the string being the speices label of the respective ion.

        N.B. This uses the ASE cell file reader. This is not the most performative method available...
        '''

        self.check_cell_file_exists()

        self.cell = read(f'{self.seed}.cell')
        self.num_ions = len(self.cell.get_atomic_numbers())
        self.species_label = self.cell.get_chemical_symbols()

    def predict_energy_stress_forces(self):
        '''
        Predict the energy, stress and forces using model.
        This involves initilaising an ASE predictor and calling the ASE calcualtors for
        energy, stress and forces (converting from the default output units to atomic units).
        '''

        # Initialise the model based ont he `medium' pre trained MACE model running on CPU to 64 bit precision
        self.model = initialise_model(self.model_name,self.device)

        # Use MACE model to predict the energies, forces and stresses on the final structure
        self.cell.calc=self.model

        # Energy/Stress/Forces converted to atomic units
        # N.B. We convert to atomic units here to keep all internal things in appropriate units
        self.total_energy = castep_units.si_to_atomic('ev',self.cell.get_total_energy())
        self.stress = castep_units.si_to_atomic('GPa',self.cell.get_stress(voigt=False))
        self.forces = castep_units.si_to_atomic('ev/a',self.cell.get_forces())

    def write_energy_stress_forces_to_geom(self):
        '''
        Write the values stored in the enthalpy, stress and forces variables to an output geom file.
        N.B. at this point these values should be stored in total_energy, stress and forces in atomic units.
        '''

        with open(f'{self.seed}.EFS', 'w') as f:
            f.write(f"                      "
                    f"{self.total_energy}   {self.total_energy}   <-- E\n")
            for i in range(3):
                f.write(f"                      {' '.join(map(str,self.stress[i]))}   <-- S\n")
            for i in range(C.num_ions):
                f.write(f" {C.species_label[i]}              "
                        f"{(i%C.species_label.count(self.species_label[i]))+1}    "
                        f"{' '.join(map(str,self.forces[i]))}   <-- F\n")



if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser(
        description='Create an ML prediction server for use with CASTEP file PP method')

    parser.add_argument('model_name',help='Name of Model to use.')
    parser.add_argument('seed',help='seed to use for filenames, this is auto generated as the last positional argument by CASTEP')
    parser.add_argument('-d','--device',default='cpu',help='The device to use for inference currently cpu or cuda')

    args = parser.parse_args()

    devices=['cpu','cuda']
    if args.device not in devices:
        parser.error('device must be cpu or cuda')
    
    model_name = args.model_name
    device = args.device
    cell_seed = args.seed

    # Initialise the prediction class, this reads the cell file on initialisation
    C = predict_from_cell(cell_seed,model_name,device)

    # Read in the cell file
    C.read_cell_file()

    # Run the prediction
    C.predict_energy_stress_forces()

    # Write the output, in geom format, to <seed>.EFS
    C.write_energy_stress_forces_to_geom()

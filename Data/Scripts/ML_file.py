#!/usr/bin/env python3

# General required modules
import sys
import os

# Use castep units module to convert to and from atomic units
from utility import castep_units
from Matbench_Models import Get_ASE_Calculator
from ase.io import read

def initialise_model(ML_model_option,ML_task=None,device='cuda'):
    '''
    Initialise the ML model, only need to do this once
    '''

    ML_model_option_lower=ML_model_option.lower()

    if ML_model_option_lower in UPET:
        import torch
        # fix/bodge specifically for UPET to disable just in time compiling as it
        # seemed to be causing issues. This may result in slightly lower performance but
        # given it's that or not working at all I think we'll take the hit.
        original_script = torch.jit.script

        def skip_jit(obj, *args, **kwargs):
            ''' 
            function to skip torch.jit.script  
            and just use eager mode in the event 
            of an error as jit script is optional.
            '''
            try:
                return original_script(obj, *args, **kwargs)
            except Exception as e:
                print("Warning: The following error occurred with pytorch jit compilation: {e}")
                print("So we are skipping jit and reverting to eager mode. This is not a major problem")
                print("as the result will be the same. However, performance will not be optimal.")
                return obj

        torch.jit.script = skip_jit
        try:
            ML_model = Get_ASE_Calculator(ML_model_option,device=device)
        finally:
            # turn torch.jit.script back on
            torch.jit.script = original_script

    elif ML_model_option_lower == 'chgnet':
        # will need to rethink this if needed!!
        raise NotImplementedError('unfortunately, CHGNet currently only has a server implementation')
        # try:
        #     from chgnet.model import CHGNet
        # except:
        #     initialise_error('CHGNet module cannot be found, please install.')

        # try:
        #     from pymatgen.core import Structure
        # except:
        #     initialise_error('Pymatgen module cannot be found, please install.')

        # ML_model = CHGNet.load(use_device='cpu')
    else:
        ML_model = Get_ASE_Calculator(ML_model_option,device=device,task=ML_task)
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
        self.model = initialise_model(self.model_name,device=self.device)

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

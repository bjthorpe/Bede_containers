import os
import sys
import logging
import utility.io as io
from twisted.internet import reactor
from server.twisted_server import ML_Factory
from Matbench_Models import Get_ASE_Calculator

def initialise_model(self,ML_model_option,ML_port,ML_task=None):
    '''
    Initialise the ML model, only need to do this once
    '''

    def initialise_error(message,port):
        print(f'ERROR: {message}')
        io.write_log('critical',message,port)
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
            initialise_error('MatterSim module cannot be found, please install.',ML_port)

        try:
            from ase import Atoms
        except:
            initialise_error('ASE module cannot be found, please install.',ML_port)

        self.Atoms = Atoms
        self.toolkit = 'ASE'
        self.model = Get_ASE_Calculator(ML_model_option_lower,device='cpu')


    elif ML_model_option_lower in Mace:

        try:
            from mace.calculators import MACECalculator
        except:
            initialise_error('MACE module cannot be found, please install.',ML_port)

        try:
            from ase import Atoms
        except:
            initialise_error('ASE module cannot be found, please install.',ML_port)

        MACE_model_path = 'mace-omat-0-medium.model'

        if not os.path.exists(MACE_model_path):
            initialise_error(f'MACE model {MACE_model_path} not found.',ML_port)

        self.Atoms = Atoms
        self.toolkit = 'ASE'
        self.model = Get_ASE_Calculator(ML_model_option_lower,model_paths=MACE_model_path,
                                    default_dtype='float64',
                                    device='cpu')
    # Meta(facebook) OMAT24
    elif ML_model_option_lower in Meta_OMat24:

        try:
            from fairchem.core import OCPCalculator    
        except:
            initialise_error('fairchem (V1.10) module cannot be found, please install.',ML_port)

        try:
            from ase import Atoms
        except:
            initialise_error('ASE module cannot be found, please install.',ML_port)

        self.Atoms = Atoms
        self.toolkit = 'ASE'
        self.model = Get_ASE_Calculator(ML_model_option_lower)

     # Meta(facebook) UMA
    elif ML_model_option_lower in Meta_UMA:

        try:
            from fairchem.core import pretrained_mlip, FAIRChemCalculator  
        except:
            initialise_error('fairchem (V2.13) module cannot be found, please install.',ML_port)
        try:
            from ase import Atoms
        except:
            initialise_error('ASE module cannot be found, please install.',ML_port)
        
        
        if not ML_task:
            initialise_error(f'Task must be specified for METa UMA model.\n\
                             This must be one of: oc20, omat, omol ,odac, or, omc".',ML_port)
        
        self.Atoms = Atoms
        self.toolkit = 'ASE'
        self.model = Get_ASE_Calculator(ML_model_option_lower,device='cpu',task=ML_task)

    elif ML_model_option_lower == 'chgnet':

        try:
            from chgnet.model import CHGNet
        except:
            initialise_error('CHGNet module cannot be found, please install.',ML_port)

        try:
            from pymatgen.core import Structure
        except:
            initialise_error('Pymatgen module cannot be found, please install.',ML_port)

        self.Structure = Structure
        self.toolkit = 'PyMatGen'
        self.model = CHGNet.load(use_device='cpu')

    else:
        initialise_error(f'Unrecognised ML_model_option {ML_model_option}',ML_port)


if __name__ == '__main__':
    
    args = io.parse_arguments()

    # Set default logging
    logging.getLogger(__name__)
    logging.basicConfig(
        filename='logs/python_server.log',encoding='utf-8',filemode='a',
        level=getattr(logging,args.logging_level.upper(),None),
        format='%(asctime)s | %(levelname)8s : %(message)s',
    )

    io.write_log('info','Server started',args.port)
    reactor.listenTCP(args.port,ML_Factory(
        port=args.port,
        task=args.task,
        timeout_cutoff=args.timeout_cutoff,
        logging_level=args.logging_level,
        ML_model_option=args.ML_model_option,
        initialise_model_function=initialise_model))
    reactor.run()

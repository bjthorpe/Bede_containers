import sys
from pathlib import Path
import subprocess
import os
from utility.io import write_log

def get_toolkit_home():
    toolkit_home = os.environ.get('ML_TOOLKIT_HOME', "")

    if toolkit_home=='':
        print(f'Could not find ML_Toolkit_home please ensure you have run install_ml-toolkit')
        sys.exit(1)
    
    return toolkit_home

def compile_nequip_model(compiled_model,checkpoint_file,device):
    ''' 
    Run command to compile nequip model if needed
    This should only need to be done the first time 
    the model runs.
    '''
    compile_command = f"nequip-compile {checkpoint_file} {compiled_model} --device {device} --mode aotinductor --target ase"
    proc = subprocess.run(compile_command, shell=True)

    try:
        proc.check_returncode()
    except subprocess.CalledProcessError as e:
        print(
            f"An error occurred {e.stderr}:"
        )
        sys.exit(1)

def Get_ASE_Calculator(ML_model_option: str, **kwargs):
    """
    Return an ASE caculator for the specified the ML model
    Params:
        ML_model_option:str - Name of ML toolkit to use
        kwargs:dict - options that are specific to the chosen model.
                      See the docs or comments on specific models for
                      what params are used.
    """
    if "models_dir" not in kwargs:
        # set default for models directory if not supplied
        models_dir="/Models"
    else:
        models_dir = kwargs['models_dir']

    # lots of different models use device keyword so set default here:
    if "device" not in kwargs:
        # set default as cpu
        kwargs['device']='cpu'

    # dicts of valid model names and corresponding checkpoint files
    Meta_OMat24 = {
        "esen-30m-oam": f"{models_dir}/esen_30m_oam.pt",
        "esen-30m-mp": f"{models_dir}/esen_30m_mptrj.pt",
        "eqv2_m": f"{models_dir}/eqV2_86M_omat_mp_salex.pt",
        "eqv2-l-dens": f"{models_dir}/eqV2_dens_153M_mp.pt",
        "eqv2-m-dens": f"{models_dir}/eqV2_dens_86M_mp.pt",
        "eqv2-s-dens": f"{models_dir}/eqV2_dens_31M_mp.pt",
        "eqv2-s": f"{models_dir}/eqV2_31M_mp.pt",
        "eqv2-s-oam": f"{models_dir}/eqV2_31M_omat_mp_salex.pt",
        "eqv2-m-oam": f"{models_dir}/eqV2_86M_omat_mp_salex.pt",
        "esen-30m-omat": f"{models_dir}/esen_30m_omat.pt",
        "eqv2-s-omat": f"{models_dir}/eqV2_31M_omat.pt",
        "eqv2-m-omat": f"{models_dir}/eqV2_86M_omat.pt",
        "eqv2-l-omat": f"{models_dir}/eqV2_153M_omat_mp_salex.pt",
    }

    Meta_UMA = {
        "uma-s-1p1": f"{models_dir}/uma-s-1p1.pt",
        "uma-s-1": f"{models_dir}/uma-s-1.pt",
        "uma-m-1p1": f"{models_dir}/uma-m-1p1.pt",
    }

    MatterSim = {"mattersim_v1_5m": f"MatterSim-v1.0.0-5M.pth"}

    NequIP = {
        'nequip-oam-xl':f'{models_dir}/Nequip/NequIP-OAM-XL-0.1.nequip.zip',
        'allegro-oam-l':f'{models_dir}/Nequip/Allegro-OAM-L-0.1.nequip.zip',
        'nequip-oam-l':f'{models_dir}/Nequip/NequIP-OAM-L-0.1.nequip.zip',
        'allegro-mp-l':f'{models_dir}/Nequip/Allegro-MP-L-0.1.nequip.zip',
        'nequip-mp-l':f'{models_dir}/Nequip/NequIP-MP-L-0.1.nequip.zip',
    }

    UPET = {
        'pet-oam-xl':f'{models_dir}/UPET/pet-oam-xl-v1.0.0.ckpt',
        'pet-oam-l':f'{models_dir}/UPET/pet-oam-l-v0.1.0.ckpt',
        'pet-omat-l':f'{models_dir}/UPET/pet-oam-l-v1.0.0.ckpt',
        'pet-omat-xl':f'{models_dir}/UPET/pet-oam-xl-v1.0.0.ckpt',
        'pet-omat-s':f'{models_dir}/UPET/pet-oam-s-v1.0.0.ckpt',
        'pet-omat-xs':f'{models_dir}/UPET/pet-oam-xs-v1.0.0.ckpt',
        'pet-mad-1.5-s':f'{models_dir}/UPET/pet-mad-s-v1.5.0.ckpt',
        'pet-mad-1.5-xs':f'{models_dir}/UPET/pet-mad-xs-v1.5.0.ckpt',
        'pet-spice-l':f'{models_dir}/UPET/pet-spice-l-v0.2.0.ckpt',
        'pet-spice-s': f'{models_dir}/UPET/pet-spice-s-v0.2.0.ckpt'
    }
    MACE = {'mace':f'mace-omat-0-medium.model'}

    # multi dataset models from 7net that require task
    SEVENNET_multi = {
        'sevennet-omni':'7net-omni',
        'sevennet-omni-i8':'7net-omni-i8',
        'sevennet-omni-i12':'7net-omni-i12',
        'sevennet-mf-ompa':'7net-mf-ompa',
    }
    # single dataset models so no task required
    SEVENNET_single = {
        'sevennet-omat':'7net-omat',
        'sevennet-0': '7net-0',
        'sevennet-l3i5': '7net-l3i5',
    }

    GRACE = {
        'grace-1l-oam':f'{models_dir}/GRACE-1L-OAM',
        'grace-2l-mptrj':f'{models_dir}/MP_GRACE_2L_r6_11Nov2024',
        'grace-2l-oam':f'{models_dir}GRACE-2L-OAM',
        'grace-2l-oam-l':f'{models_dir}/GRACE-2L-OMAT-large-ft-AM'
    }

    TACE = {
        'tace-omat24-l':f'{models_dir}/TACE-OMat24-L.pt',
        'tace-oam-l':f'{models_dir}/TACE-OAM-L.pt'
    }
    Matris = {
        'matris_10m_oam':'matris_10m_oam',
        'matris_10m_mp':'matris_10m_mp'
    }

    ORBV = {
        # orb-v3 models
        "orb-v3":f'{models_dir}/ORB-v3.chkpt',
        "orb-v3-conservative-omol": f'{models_dir}/ORB-v3_conservative_omol.chkpt',
        "orb-v3-direct-omol": f'{models_dir}/ORB-v3_direct_omol.chkpt',
        "orb-v3-conservative-20-omat": f'{models_dir}/ORB-v3_direct_omol.chkpt',
        "orb-v3-conservative-inf-omat": f'{models_dir}/ORB-v3_conservative_inf_omat.chkpt',
        "orb-v3-direct-20-omat": f'{models_dir}/ORB-v3_direct_20_omat.chkpt',
        "orb-v3-direct-inf-omat": f'{models_dir}/ORB-v3_direct_inf_omat.chkpt',
        "orb-v3-conservative-20-mpa": f'{models_dir}/ORB-v3_conservative_20_mpa.chkpt',
        "orb-v3-conservative-inf-mpa": f'{models_dir}/ORB-v3_conservative_inf_mpa.chkpt',
        "orb-v3-direct-20-mpa": f'{models_dir}/ORB-v3_direct_20_mpa.chkpt',
        "orb-v3-direct-inf-mpa": f'{models_dir}/ORB_v3_direct_inf_mpa.chkpt',
        # orb-v2 models
        "orb-v2": f'{models_dir}/ORB_v2.chkpt',
        "orb-mptraj-only-v2": f'{models_dir}/ORB_mptraj_only_v2.chkpt',
    }
    
    Equiformer={
        "equiformerv3_dens_oam":f'{models_dir}/omat24-mptrj-salex_gradient.pt',
        "equiformerv3_dens_mp":f'{models_dir}/mptrj_gradient.pt',
        "equiformerv3_omat":f'{models_dir}/omat24_gradient.pt',
    }

    DEEPMD={
        'dpa-3.1-3m-ft':f'{models_dir}/dpa-3.1-3m-ft.pth',
        'dpa-3.1-mprtj':f'{models_dir}/dpa-3.1-mprtj.pth'
    }

    ML_model_option_lower = ML_model_option.lower()
    ASE_Calculator = None

    ###############################################################################
    #         MatterSim (Microsoft)
    #
    #         Params:
    #           "device" - what device to target.can be either 'cpu' or 'cuda'.
    #           "load_path" - Path inside the container to compiled model. 
    #                          Default is to look inside /models.
    ###############################################################################
    if ML_model_option_lower in MatterSim:

        try:
            from mattersim.forcefield import MatterSimCalculator
        except:
            raise ModuleNotFoundError("MatterSim cannot be found, please install MatterSim.")


        if 'load_path' not in kwargs:
            #if path to model not provided use default models directory
            kwargs['load_path'] = MatterSim[ML_model_option_lower]

        ASE_Calculator = MatterSimCalculator(load_path=kwargs['load_path'],device=kwargs['device'])

    ###############################################################################
    #   MACE - Fast and accurate machine learning interatomic potentials with 
    #           higher order equivariant message passing.
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
    #   https://github.com/ACEsuit/mace 
    #   
    #   Params:
    #           "device" - what device to target.can be either 'cpu' or 'cuda'.
    #           "model_path" - Path inside the container to compiled model. 
    #                          Default is to look inside /models.
    #           "default_dtype" - default data type
    ###############################################################################
    elif ML_model_option_lower == 'mace':
        try:
            from mace.calculators import MACECalculator
        except:
            raise ModuleNotFoundError('MACE cannot be found, please install.')
        
        if 'model_paths' not in kwargs:
            kwargs['model_paths']= MACE[ML_model_option_lower]

        ASE_Calculator = MACECalculator(model_paths=kwargs['model_paths'],device=kwargs['device'])
    ###############################################################################

    #          Meta Ai (Facebook)
    ###############################################################################

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #   Meta Open Materials 2024 (OMat24) Models:
    #
    #   Note: these use fairchem 1.10 and are incompatible with the latest version
    #   (currently 2.13).
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif ML_model_option_lower in Meta_OMat24:

        try:
            from fairchem.core import OCPCalculator
        except:
            raise ModuleNotFoundError('fairchem (V1.1) cannot be found, please install.')
                                
        if 'checkpoint_path' not in kwargs:
            kwargs['checkpoint_path']=Meta_OMat24[ML_model_option_lower]
        
        if kwargs['device']=='cpu':
            use_cpu=True
        else:
            use_cpu=False
        ASE_Calculator = OCPCalculator(checkpoint_path=kwargs['checkpoint_path'],cpu=use_cpu)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # UMA: A Family of Universal Models for Atoms
    #
    # Meta's latest models (as of Jan 2026)
    # These use Fairchem 2.13 and have a completely redesigned syntax
    #
    #       Params:
    #           "device" - what device to target. Can be either 'cpu' or 'cuda'.
    #           "task" - Set the task for your application.
    #                    This must be one of:
    #                       oc20: for catalysis
    #                       omat: for inorganic materials
    #                       omol: for molecules
    #                       odac: for MOFs
    #                       omc:  for molecular crystals
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif ML_model_option_lower in Meta_UMA:
        try:
            from fairchem.core.units.mlip_unit import load_predict_unit
            from fairchem.core import FAIRChemCalculator
        except:
            raise ModuleNotFoundError('fairchem (V2.13) cannot be found, please install.')
        
        available_tasks = ["oc20", "omat", "omol" ,"odac", "omc"]
        # check kwargs are correct
        if kwargs['task']==None:
            print('Meta UMA model requires the input argument "task".')
            print(f'This must be one of: {available_tasks}.')
            sys.exit(11)
        elif kwargs['task'] not in available_tasks:
            task = kwargs['task']
            print(f'unknown task {task}.')
            print(f'This must be one of: {available_tasks}.')
            sys.exit(11)

        # predictor = pretrained_mlip.get_predict_unit(
        #     Meta_UMA[ML_model_option_lower], device=kwargs["device"],
        #     cache_dir='/Models/hub'
        # )
        predictor = load_predict_unit(
            Meta_UMA[ML_model_option_lower], device=kwargs["device"],
        )
        ASE_Calculator = FAIRChemCalculator(predictor, task_name=kwargs["task"])
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # NequIP and Allegro
    #
    # NequIP is an open-source code for machine learning on atomic systems.
    # Allegro is an extension package for NequIP
    #
    # https://nequip.readthedocs.io/en/latest/integrations/ase.html
    #
    #       Params:
    #           "device" - what device to target. Can be either 'cpu' or 'cuda'.
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #           Note about "checkpoint_file":
    #
    #           Packaged model files (in .nequip.zip format ) for each supported 
    #           model can be found in the ML_Toolkit/Models/NequIP directory. 
    #           This directory is automatically copied into the container at 
    #           build time as /models/NequIP. 
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif ML_model_option_lower in NequIP:
        try:
            from nequip.integrations.ase import NequIPCalculator
        except:
            raise ModuleNotFoundError('Nequip cannot be found, please install.')
        
        checkpoint_file = NequIP[ML_model_option_lower]
        toolkit_home=get_toolkit_home()
        compile_path=f"{toolkit_home}/Models/Nequip/{kwargs['device']}/{ML_model_option}.nequip.pt2"

    # Call bash script to Compile the model if needed
        if not Path(compile_path).exists():
            print(f"***************************************************")
            print(f"{compile_path}")
            print(f"First time run so compiling model {ML_model_option}")
            print(f"This will take a lot longer than usual")
            print(f"***************************************************")
            Path(f"{toolkit_home}/Models/Nequip/{kwargs['device']}").mkdir(parents=True,exist_ok=True)
            compile_nequip_model(compile_path,checkpoint_file,kwargs["device"])
        
        ASE_Calculator = NequIPCalculator.from_compiled_model(
            compile_path=compile_path,
            device=kwargs['device'])
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # UPET: universal atomistic models
    #
    # universal interatomic potentials for advanced materials modeling across 
    # the periodic table. These models are based on the Point Edge Transformer 
    # (PET) architecture trained on various popular atomistic datasets, and 
    # they are capable of predicting energies and forces in complex atomistic 
    # workflows.
    #
    # https://github.com/lab-cosmo/upet/tree/main
    #
    #       Params:
    #           "device" - what device to target. Can be either 'cpu' or 'cuda'.
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif ML_model_option_lower in UPET:
        try:
            from upet.calculator import UPETCalculator
        except:
            raise ModuleNotFoundError('UPET cannot be found, please install.')
        checkpoint_file = UPET[ML_model_option]
        toolkit_home=get_toolkit_home()
        ASE_Calculator = UPETCalculator(checkpoint_path=checkpoint_file, device=kwargs['device'],model=ML_model_option_lower)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # SevenNet pretrained models (Multi)
    #
    # These are multi-fidelity architecture models, thus Multiple inference tasks are available
    # through the task keyword.
    #
    # Each task is designed to produce results that are consistent with the DFT settings used 
    # in the corresponding training datasets. For example, mpa is trained on the combined 
    # MPtrj and sAlex datasets and is used for evaluating Matbench Discovery, while omat24 
    # is trained on the OMat24 dataset. see 
    # https://sevennet.readthedocs.io/en/latest/user_guide/pretrained.html for details of 
    # each model and avalible tasks.
    #
    #      Params:
    #           "device" - what device to target. Can be either 'cpu' or 'cuda'.
    #           "task" - Set the task for your application.
    #                    This must be one of:
    #                        'mpa',
    #                        'omat24',
    #                        'matpes_pbe',
    #                        'oc20',
    #                        'oc22',
    #                        'odac23',
    #                        'omol25_low',
    #                        'omol25_high',
    #                        'spice','qcml',
    #                        'pet_mad',
    #                        'mp r2scan',
    #                        'matpes_r2scan'
    #
    # Note: Thease are set with the task cmd argument
    # 
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif ML_model_option_lower in SEVENNET_multi:
        try:
            from sevenn.calculator import SevenNetCalculator
        except:
            raise ModuleNotFoundError('SevenNet cannot be found, please install.')
        
        # set avalble tasks based on model
        if ML_model_option_lower == 'sevennet-mf-ompa':
            avalible_tasks = ['mpa','omat24']
        else:
            avalible_tasks = ['mpa','omat24','matpes_pbe','oc20','oc22','odac23',
                              'omol25_low','omol25_high','spice','qcml','pet_mad',
                              'mp r2scan','matpes_r2scan']
        # check task is both provided and correct.
        if kwargs["task"]==None:
            print(f'Svennet Model: {ML_model_option} requires the input argument "task".')
            print(f'This must be one of: {avalible_tasks}.')
            sys.exit(11)
        elif kwargs['task'] not in avalible_tasks:
            task = kwargs['task']
            print(f'unknown task {task}.')
            print(f'This must be one of: {avalible_tasks}.')
            sys.exit(11)

        ASE_Calculator = SevenNetCalculator(model=SEVENNET_multi[ML_model_option_lower], modal=kwargs['task'],device=kwargs['device'])
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # SevenNet pretrained models (single)
    # 
    # Sinlge task models from SevenNet, no task argumant required
    #
    #      Params:
    #           "device" - what device to target. Can be either 'cpu' or 'cuda'.
    # 
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif ML_model_option_lower in SEVENNET_single:
        try:
            from sevenn.calculator import SevenNetCalculator
        except:
            raise ModuleNotFoundError('SevenNet cannot be found, please install.')
    
        ASE_Calculator = SevenNetCalculator(model=SEVENNET_single[ML_model_option_lower],device=kwargs['device'])
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Grace pretrained models
    # 
    #      Params:
    #           "device" - what device to target. Can be either 'cpu' or 'cuda'.
    # 
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif ML_model_option_lower in GRACE:
        try:
            #from tensorpotential.calculator import grace_fm
            from tensorpotential.calculator.asecalculator import TPCalculator
        except:
            raise ModuleNotFoundError('Grace cannot be found, please install.')
    
        #ASE_Calculator = grace_fm(GRACE[ML_model_option])
        ASE_Calculator = TPCalculator(model=GRACE[ML_model_option_lower])
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # TACE pretrained models
    #
    #      Params:
    #           "device" - what device to target. Can be either 'cpu' or 'cuda'.
    # 
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif ML_model_option_lower in TACE:
        try:
            from tace.interface.ase import TACEAseCalc
        except:
            raise ModuleNotFoundError('TACE cannot be found, please install.')
    
        ASE_Calculator = TACEAseCalc(TACE[ML_model_option_lower],device=kwargs['device'],dtype='float32')
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # DeepMD pre-trained models
    #
    #      Params:
    #           "device" - what device to target. Can be either 'cpu' or 'cuda'.
    # 
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif ML_model_option_lower in DEEPMD:
        try:
            from deepmd.calculator import DP
        except:
            raise ModuleNotFoundError('DeepMD cannot be found, please install.')
    
        ASE_Calculator = DP(model=DEEPMD[ML_model_option_lower])
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ORBV pretrained models
    #
    #      Params:
    #           "device" - what device to target. Can be either 'cpu' or 'cuda'.
    # 
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif ML_model_option_lower in ORBV:
        try:
            from orb_models.forcefield import pretrained
            from orb_models.forcefield.pretrained import ORB_PRETRAINED_MODELS
            from orb_models.forcefield.inference.calculator import ORBCalculator
        except:
            raise ModuleNotFoundError('ORB_V cannot be found, please install.')
        
        # This loks a bit wierd but is here because orb-v3 has two names 
        # want to keep using orb-v3 in our dict as thats the name used by matbench discover.
        # However, ob-matrials lists the model as orb-v3-conservative-inf-omat

        ModelName = ML_model_option_lower
        if ML_model_option_lower == 'orb-v3': 
            ML_model_option_lower = 'orb-v3-conservative-inf-omat'

        method = ORB_PRETRAINED_MODELS[ML_model_option_lower]

        orbff, atoms_adapter = method(
            weights_path=ORBV[ModelName],
            device=kwargs['device'],
            precision="float32-high", # or precision="float32-highest"
        )
        ASE_Calculator = ORBCalculator(orbff, atoms_adapter=atoms_adapter, device=kwargs['device'])
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # TACE pretrained models
    #
    #      Params:
    #           "device" - what device to target. Can be either 'cpu' or 'cuda'.
    # 
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif ML_model_option_lower in Equiformer:
        try:
            from fairchem.core.common.relaxation.ase_utils import OCPCalculator
            from fairchem.core.models.model_registry import model_name_to_local_file
        except:
            raise ModuleNotFoundError('Equiformer cannot be found, please install.')
        
        if kwargs['device'] =='cuda':
            cpu_flag=False
        else:
            cpu_flag=True
        #checkpoint_path = model_name_to_local_file(Equiformer[ML_model_option_lower], local_cache='/Models')
        ASE_Calculator = OCPCalculator(checkpoint_path=Equiformer[ML_model_option_lower],cpu=cpu_flag,seed=0)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # END
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    else:
        print(f"Unknown module {ML_model_option}")
        sys.exit(1)
    return ASE_Calculator

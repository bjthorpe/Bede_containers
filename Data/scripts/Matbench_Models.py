import sys
from pathlib import Path

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
        "uma-s-1p1": "uma-s-1p1",
        "uma-s-1": "uma-s-1",
        "uma-m-1p1": "uma-m-1p1",
    }

    MatterSim = {"mattersim": f"MatterSim-v1.0.0-5M.pth"}

    NequIP = {
        'nequip-oam-xl':'NequIP-OAM-XL-0.1.nequip.zip',
        'allegro-oam-l':'Allegro-OAM-L-0.1.nequip.zip',
        'nequip-oam-l':'NequIP-OAM-L-0.1.nequip.zip',
        'allegro-mp-l':'Allegro-MP-L-0.1.nequip.zip',
        'nequip-mp-l':'NequIP-MP-L-0.1.nequip.zip',
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

        ASE_Calculator = MatterSimCalculator(**kwargs)

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
            kwargs['model_paths'] = 'mace-omat-0-medium.model'

        ASE_Calculator = MACECalculator(**kwargs)
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
    #           "workers" - Number of Gpus to use for inferencing
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
            from fairchem.core import pretrained_mlip, FAIRChemCalculator
        except:
            raise ModuleNotFoundError('fairchem (V2.13) cannot be found, please install.')
        
        # check kwargs are correct
        if "task" not in kwargs:
            raise ValueError('Meta UMA model requires the input argument "task".')

        predictor = pretrained_mlip.get_predict_unit(
            Meta_UMA[ML_model_option_lower], device=kwargs["device"]
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
    #           "checkpoint_file" - Path to either a checkpoint file (.ckpt) 
    #                               from training or a packaged model file 
    #                               (.nequip.zip).
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #           Note about "checkpoint_file":
    #
    #           Packaged model files (in .nequip.zip format ) for each supported 
    #           model can be found in the models/NequIP directory. This directory
    #           is automatically copied into the container at build time as 
    #           /models/NequIP. 
    # 
    #           These will be used by default if the checkpoint_file argument 
    #           is not supplied. To use a custom path you need to ensure that 
    #           it is accessible to the container. This can be achieved by 
    #           either copying the files at build time using the container 
    #           definition file or setting shared_directories in the .yaml 
    #           file for the model parameters (see the docs for more details).
    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif ML_model_option_lower in NequIP:
        from nequip.ase import NequIPCalculator

        if "checkpoint_file" not in kwargs:
            checkpoint_file = NequIP[ML_model_option_lower]
        else:
            checkpoint_file = f"{models_dir}/NequIP/{kwargs['checkpoint_file']}"

        compile_path=f"{models_dir}/NequIP/{ML_model_option_lower}.nequip.pt2"
# Call bash script to Compile the model if needed
        if not Path(checkpoint_file).exists():
            compile_nequip_model()
        
        ASE_Calculator = NequIPCalculator.from_compiled_model(
            compile_path=compile_path,
            device=kwargs['device'])
    else:
        initialise_error(f"Unknown module {ML_model_option}")
    return ASE_Calculator

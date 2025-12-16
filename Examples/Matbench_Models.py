import sys

def initialise_error(message:str):
    print(f'ERROR: {message}')
    sys.exit(23)

def initialise_model(ML_model_option:str,path='/models'):
    '''
    Initialise the ML model, only need to do this once
    Params:
        ML_model_option:str - Name of ML toolkit to use
        model_loc:str - Path to compiled ML model
    '''

    ML_model_option_lower=ML_model_option.lower()
    ASE_Calculator=None
# # Dict of models and locations of corresponding checkpoint files.
# # Note: if not using containers you will need to update these locations
    models_directory='/models'
    checkpoint_path = {'esen-30m-oam': f"{models_directory}/FairChem/esen_30m_oam.pt",
                  'esen-30m-mp': f"{models_directory}/FairChem/esen_30m_mptrj.pt",
                  'eqv2_m': f"{models_directory}/FairChem/eqV2_86M_omat_mp_salex.pt",
                  'mattersim':f"{models_directory}/MatterSim-v1.0.0-5M.pth"
                   }
#Models using mattersim
    if ML_model_option_lower == 'mattersim':

        try:
            from mattersim.forcefield import MatterSimCalculator
        except:
            initialise_error('MatterSim module cannot be found, please install MatterSim.')
        # path to the compiled model, Note: this should be already is inside 
        # the MatterSim container
        Compiled_Model_Path = checkpoint_path[ML_model_option_lower]
        ASE_Calculator = MatterSimCalculator(load_path=Compiled_Model_Path,device='cpu')

# Models from Meta Ai (Facebook) all use fairchem
    elif (ML_model_option_lower == 'esen-30m-oam' or ML_model_option_lower == 'eqv2_m' \
           or ML_model_option_lower == 'esen-30m-mp'):
        
        # from fairchem.core import pretrained_mlip, FAIRChemCalculator
        # predictor = pretrained_mlip.get_predict_unit("esen_30m_oam", device="cuda")
        # ASE_Calculator = FAIRChemCalculator(predictor, task_name="omol")
        from fairchem.core import OCPCalculator
        ASE_Calculator = OCPCalculator(checkpoint_path="/root/.cache/huggingface/hub/models--facebook--OMAT24/snapshots/8a5a78c7ba7b250a17e85fe85943c4608499d895/esen_30m_oam.pt")

    else:
        initialise_error(f'Unknown module {ML_model_option}')
    return ASE_Calculator
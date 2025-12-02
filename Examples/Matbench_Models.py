import sys

def initialise_error(message:str):
    print(f'ERROR: {message}')
    sys.exit(23)

def initialise_model(ML_model_option:str):
    '''
    Initialise the ML model, only need to do this once
    Params:
        ML_model_option:str - Name of ML toolkit to use
        model_loc:str - Path to compiled ML model
    '''

    ML_model_option_lower=ML_model_option.lower()
    ASE_Calculator=None

    if ML_model_option_lower == 'mattersim':

        try:
            from mattersim.forcefield import MatterSimCalculator
        except:
            initialise_error('MatterSim module cannot be found, please install MatterSim.')
        # path to the compiled model, Note: this should be already is inside 
        # the MatterSim container
        Compiled_Model_Path = 'MatterSim-v1.0.0-5M.pth'
        ASE_Calculator = MatterSimCalculator(load_path=Compiled_Model_Path,device='cpu')
    else:
        initialise_error(f'Unknown module {ML_model_option}')
    return ASE_Calculator
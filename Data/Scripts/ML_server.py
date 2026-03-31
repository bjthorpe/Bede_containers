import os
import sys
import logging
import utility.io as io
from twisted.internet import reactor
from server.twisted_server import ML_Factory
from Matbench_Models import Get_ASE_Calculator
from pathlib import Path

def get_toolkit_home():
    toolkit_home = os.environ.get('ML_TOOLKIT_HOME', "")

    if toolkit_home=='':
        cmd_output(f'Could not find ML_Toolkit_home please ensure you have run install_ml-toolkit')
        sys.exit(1)
    
    return toolkit_home

def initialise_model(self,ML_model_option,ML_port,ML_task=None,device='cuda'):
    '''
    Initialise the ML model, only need to do this once
    '''

    def initialise_error(message,port):
        print(f'ERROR: {message}')
        io.write_log('critical',message,port)
        sys.exit(23)

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
                io.write_log('warn',f"The following error occurred with pytorch jit compilation: {e}",ML_port)
                io.write_log('warn',f"Skipping jit and reverting to eager mode.",ML_port)
                io.write_log('warn',f"The result will be the same however, performance will not be optimal.",ML_port)
                return obj

        torch.jit.script = skip_jit
        try:
            self.model = Get_ASE_Calculator(ML_model_option,device=device)
        finally:
            # turn torch.jit.script back on
            torch.jit.script = original_script
        self.Atoms = Atoms
        self.toolkit = 'ASE'
    
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
        self.model = CHGNet.load(use_device=device)

    else:
        self.Atoms = Atoms
        self.toolkit = 'ASE'
        self.model = Get_ASE_Calculator(ML_model_option_lower,device=device,task=ML_task)

if __name__ == '__main__':
    
    args = io.parse_arguments()
    toolkit_home = get_toolkit_home()
    # Set default logging
    logging.getLogger(__name__)
    logging.basicConfig(
        filename=f'{toolkit_home}/logs/python_server.log',encoding='utf-8',filemode='a',
        level=getattr(logging,args.logging_level.upper(),None),
        format='%(asctime)s | %(levelname)8s : %(message)s',
    )

    io.write_log('info','Server started',args.port)
    reactor.listenTCP(args.port,ML_Factory(
        port=args.port,
        task=args.task,
        device=args.device,
        timeout_cutoff=args.timeout_cutoff,
        logging_level=args.logging_level,
        ML_model_option=args.ML_model_option,
        initialise_model_function=initialise_model))
    reactor.run()

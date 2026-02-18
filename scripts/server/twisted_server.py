import os
import sys
import logging
import argparse
import subprocess
import numpy as np

from twisted.internet.protocol import Factory, Protocol
from twisted.protocols.basic import Int32StringReceiver
from twisted.internet.threads import deferToThread
from twisted.internet import reactor
from dataclasses import dataclass, field
from utility import castep_units
from utility.io import write_log
from Matbench_Models import Get_ASE_Calculator


class ML_Factory(Factory):

    def __init__(self,port,timeout_cutoff,logging_level,ML_model_option,initialise_model_function):

        self.timeout_cutoff = timeout_cutoff
        self.port = port
        self.logging_level = logging_level
        self.ML_model_option = ML_model_option
        self.tmp_ctr = 0

        write_log('info',f'Starting: Loading ML model {ML_model_option} into factory',self.port)

        # Bind the input initialisation function to the factory class
        self.initialise_model = initialise_model_function.__get__(self,ML_Factory)
        self.initialise_model(self.ML_model_option,self.port)

        write_log('info',f'Complete: Loading ML model {ML_model_option} into factory',self.port)


    def buildProtocol(self,addr):

        write_log('debug','Creating protocol',self.port)
        protocol = Protocol(self.toolkit)
        protocol.factory = self
        return protocol



class Protocol(Int32StringReceiver):


    # Use little-endian unsigned int (4 bytes)
    structFormat = "<I"


    def __init__(self,toolkit):

        if toolkit.lower() == 'ase':
            self.predict_from_model = self.predict_from_model_ASE
        elif toolkit.lower() == 'pymatgen':
            self.predict_from_model = self.predict_from_model_pymatgen
        else:
            self.exit_with_error(f'Unrecognised toolkit "{toolkit}", must be ASE or Pymatgen')


    def connectionMade(self):
        '''
        What do do when the connection is opened.
        Only things to do with the connection, data/message processing is done in dataReceivedieved
        '''
        self.peer = self.transport.getPeer()
        self.factory.tmp_ctr += 1
        write_log('debug',f'Accepted connection {self.factory.tmp_ctr}'
                  f' from {self.peer.host}:{self.peer.port}',self.factory.port)


    def stringReceived(self, data: bytes):

        self.message = data.decode('utf-8')
        write_log('debug',f'Full message : {self.message}',self.factory.port)

        # We have recieved some new data, so any old data should be nullified
        self.file_magic     = None
        self.num_ions       = None
        self.real_lattice   = None
        self.species_labels = None
        self.frac_coords    = None

        self.predicted_total_energy = None
        self.predicted_stress       = None
        self.predicted_forces       = None
        self.predicted_magmom       = None

        if self.message == '':
            self.exit_with_error(f'Message sent from {self.peer.host}:{self.peer.port} is an empty string')
        else:
            self.processResponse()


    def respond_to_health_check(self):
        '''
        Repond to a health check communication with ALIVE
        '''
        self.response = 'ALIVE'
        self.send_response()
        self.close_connection()


    def kill_self(self):
        '''
        Kill the current process by sending a kill signal
        '''
        write_log('critical','Killing process',self.factory.port)
        subprocess.run(f'kill -9 {os.getpid()}',shell=True)


    def reincarnate(self,callbackopt=None):
        '''
        Kill the current process by sending a kill signal
        then restart an identical process
        '''
        write_log('critical','Reincarnating process',self.factory.port)
        main_path = os.path.abspath(getattr(sys.modules['__main__'],'__file__',''))
        subprocess.run(f'kill -9 {os.getpid()} && python {main_path} -P {self.factory.port} -L {self.factory.logging_level} -T {self.factory.timeout_cutoff} -M {self.factory.ML_model_option} &',shell=True)


    def send_response(self):
        '''
        Send whatever string is currently in self.response
        '''
        write_log('debug',f'Sending "{self.response.strip()}" to {self.peer.host}:{self.peer.port}',self.factory.port)
        self.sendString(self.response.encode())


    def close_connection(self):
        '''
        Close the currently active connection
        '''
        write_log('debug',f'Closing connection to {self.peer.host}:{self.peer.port}',self.factory.port)
        self.transport.loseConnection()


    def exit_with_error(self,error_msg):
        '''
        Close the currently active connection
        '''
        write_log('error',error_msg,self.factory.port)
        self.reincarnate()


    def processResponse(self):
        '''
        Process the response based on the given message.
        If none of the special messages [ CHECK, kill_self, reincarnate ]
        are given then run the default process.
        '''
        if self.message == 'CHECK':
            self.respond_to_health_check()

        elif self.message == 'kill_self':
            self.kill_self()

        elif self.message == 'reincarnate':
            self.reincarnate()

        else:

            self.response = ''

            # First parse the message we have recieved to a structure
            self.parse_message_to_structure()

            # Define a background timeout process, just to make sure the ML does not hang
            self.timeout_call = reactor.callLater(self.factory.timeout_cutoff,self.exit_with_error,
                                                  f'timeout after {self.factory.timeout_cutoff} seconds')

            # Defer the heavy lifting to a thread so it can't block the timeout call
            d = deferToThread(self.predict_from_model)
            # Varous things to do on success (send data back over socket) or failure (reincarnate)
            d.addCallback(self.reply_with_prediction)


    def parse_message_to_structure(self):
        '''
        Convert into various arrays that we need, specifically:
            - The real lattice (in Ang from atomic)
            - Species labels
            - Fractional coordinates
        '''

        structure_array = self.message.split()

        try:
            self.file_magic = str(structure_array[0])
        except Exception as e:
            self.exit_with_error(f'Error reading file magic, given as "{structure_array[0]}" to string: {e}')

        if self.file_magic in ['A','D','E']:
            # A for sending lattice/basis and returning energy/force/stress
            # D for sending lattice/basis and returning energy/force/stress/collinear-spin
            # E for sending lattice/basis and returning energy/force/stress/non-collinear-spin
            try:
                self.num_ions = int(structure_array[1])
            except Exception as e:
                self.exit_with_error(f'Error reading number of ions, given as "{structure_array[1]}" to integer: {e}')

            try:
                self.real_lattice = castep_units.atomic_to_si('ang',np.array(structure_array[2:11]).astype(float).reshape(3,3))
            except Exception as e:
                self.exit_with_error(f'Cannot read lattice vectors to numpy float array: {e}')

            try:
                self.species_labels = structure_array[11:11+self.num_ions]
            except Exception as e:
                self.exit_with_error(f'Cannot read species labels to string array: {e}')

            try:
                self.frac_coords = np.array(structure_array[11+self.num_ions:]).astype(float).reshape(self.num_ions,3)
            except Exception as e:
                self.exit_with_error(f'Cannot read fractional coords to numpy float array: {e}')

        else:
            self.exit_with_error(f'MatterSim server currently only sends lattice + basis'
                                 f' (file magics A, D, E), given {self.file_magic}')


    def reply_with_prediction(self,_):
        '''
        Once the process is completed parse the final bits of data, send them over and tidy up
        '''

        def check_none(**check_none):
            missing = [name for name, value in check_none.items() if value is None]
            if missing:
                self.exit_with_error(f"Values requred for response are None: {', '.join(f'{name}' for name in missing)}")

        # We have the prediction, so cancel the timeout
        self.cancel_timeout()

        # Construct return string based on file magic
        if self.file_magic == 'A':
            # A for recieving lattice/basis and returning just energy/force/stress

            check_none(energy=self.predicted_total_energy,
                       stress=self.predicted_stress,
                       forces=self.predicted_forces.flatten)

            # Parse the response to be, in atomic units, to a space seperated list
            # Enthalpy (total cell) stress forces
            self.response = \
                f"{self.predicted_total_energy:.21e} "+ \
                f"{' '.join([ f'{s:.21e}' for s in self.predicted_stress ])} "+ \
                f"{' '.join([ f'{f:.21e}' for f in self.predicted_forces.flatten() ])}"

        elif self.file_magic == 'D':
            # D for recieving lattice/basis and returning just energy/force/stress/collinear spin

            check_none(energy=self.predicted_total_energy,
                       stress=self.predicted_stress,
                       forces=self.predicted_forces.flatten,
                       magmom=self.predicted_magmom)

            # Parse the response to be, in atomic units, to a space seperated list
            # Enthalpy (total cell) stress forces
            self.response = \
                f"{self.predicted_total_energy:.21e} "+ \
                f"{' '.join([ f'{s:.21e}' for s in self.predicted_stress ])} "+ \
                f"{' '.join([ f'{f:.21e}' for f in self.predicted_forces.flatten() ])} "+ \
                f"{' '.join([ f'{m:.21e}' for m in self.predicted_magmom.flatten() ])}"

        else:
            self.exit_with_error(f'Server currently only runs by recieving lattice + basis'
                                 f' and returning EFS (file magic A) or EFS+CS (file magic D),'
                                 f' given {self.file_magic}')


        # Then send our response
        self.send_response()


    def cancel_timeout(self):
        '''
        Cancel the background timeout process, which if timeout is reached will kill this process
        '''
        if self.timeout_call and self.timeout_call.active():
            self.timeout_call.cancel()


    ################################
    # Library dependant predictors #
    ################################


    def matrix_to_voigt(self,matrix):
        voigt = np.zeros(6)
        voigt[0] = matrix[0][0]
        voigt[1] = matrix[1][1]
        voigt[2] = matrix[2][2]
        voigt[3] = matrix[1][2]
        voigt[4] = matrix[0][2]
        voigt[5] = matrix[0][1]
        return voigt


    def predict_from_model_ASE(self):
        """
        Perform the prediction form the model for a cell containing N ions from class vars:
        - Real lattice (in Angstrom) as 3x3 matrix
        - Array of species labels as strings with one for each ion (e.g. Li, Li, Al)
        - 3xN array of fractional coordinates, one for each ion

        This then returns (by placing on the queue)
        - The TOTAL cell enthalpy (in eV).
        - Array of length 6 giving the stress in Voigt ordering (in GPa).
        - 3xN array of forces on each ion (in eV/Ang).
        """

        # Convert to a pymatgen object
        cell = self.factory.Atoms(symbols=self.species_labels,
                                  scaled_positions=self.frac_coords,
                                  cell=self.real_lattice,
                                  pbc=[True,True,True])

        # Set the ASE calcualtor to be the one defined in the factory
        cell.calc = self.factory.model

        # Set the predicted energy (full cell energy), stress, forces, store them all in atomic units
        try:
            self.predicted_total_energy = castep_units.si_to_atomic('ev',cell.get_potential_energy())
        except Exception as e:
            self.exit_with_error(f'Error in parsing predicted energy: {e}')

        try:
            self.predicted_stress_non_voigt = castep_units.si_to_atomic('ev/a**3',cell.get_stress(voigt=False))
            self.predicted_stress = self.matrix_to_voigt(self.predicted_stress_non_voigt)
        except Exception as e:
            self.exit_with_error(f'Error in parsing predicted stress: {e}')

        try:
            self.predicted_forces = castep_units.si_to_atomic('ev/a',cell.get_forces())
        except Exception as e:
            self.exit_with_error(f'Error in parsing predicted forces: {e}')


    def predict_from_model_pymatgen(self):
        """
        Perform the prediction form the model for a cell containing N ions from class vars:
          - Real lattice (in Angstrom) as 3x3 matrix
          - Array of species labels as strings with one for each ion (e.g. Li, Li, Al)
          - 3xN array of fractional coordinates, one for each ion

        This then returns (by placing on the queue)
          - The TOTAL cell enthalpy (in eV).
          - Array of length 6 giving the stress in Voigt ordering (in GPa).
          - 3xN array of forces on each ion (in eV/Ang).
        """

        # Convert to a pymatgen object
        cell_pymatgen = self.factory.Structure(self.real_lattice,self.species_labels,self.frac_coords)

        # Then predict the energy/force/stress using the ML model
        model_prediction = self.factory.model.predict_structure(cell_pymatgen)

        # Set the predicted energy (full cell energy), stress, forces, store them all in atomic units
        try:
            self.predicted_total_energy = castep_units.si_to_atomic('ev',model_prediction['e'[0]]*self.num_ions)
        except Exception as e:
            self.exit_with_error(f'Error in parsing predicted energy: {e}')

        try:
            predicted_stress_non_voigt = castep_units.si_to_atomic('GPa',model_prediction['s'[0]])
            self.predicted_stress = self.matrix_to_voigt(predicted_stress_non_voigt)
        except Exception as e:
            self.exit_with_error(f'Error in parsing predicted stress: {e}')

        try:
            self.predicted_forces = castep_units.si_to_atomic('ev/a',np.array(model_prediction['f'[0]],dtype=float))
        except Exception as e:
            self.exit_with_error(f'Error in parsing predicted forces: {e}')

        if self.file_magic == 'D':
            try:
                self.predicted_magmom = np.array(model_prediction['m'[0]],dtype=float)
            except Exception as e:
                self.exit_with_error(f'Error in parsing predicted magmom: {e}')

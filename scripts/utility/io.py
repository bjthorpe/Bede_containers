import logging
import argparse


def write_log(level,message,port):
    logging_with_level = getattr(logging,level.lower(),None)
    if not callable(logging_with_level):
        logging.error(f'logging.{level.lower()} is not callable')
    else:
        logging_with_level(f'port {port} : {message}')


def parse_arguments():

    parser = argparse.ArgumentParser(
        description='Create an ML prediction server for use with CASTEP sockets PP methods')

    parser.add_argument('-P','--port',type=int,default=50000,
                        help='The port to open on the prediction server.')
    parser.add_argument('-L','--logging_level',type=str,default='info',
                        help='The logging level to be used by python logging. Should be one of '
                        ' [ debug, info, warning, error, critical ]. Default info')
    parser.add_argument('-T','--timeout_cutoff',type=int,default=30,
                        help='The timeout for the server, exit if prediction takes this long (in seconds).')
    parser.add_argument('-M','--ML_model_option',type=str,default='None',
                        help='The ML method to use, e.g. CHGNet, MatterSim etc.'
                        ' Dependancies must be installed. Check main file for implemented methods')

    args = parser.parse_args()

    if args.logging_level not in [ 'debug', 'info', 'warning', 'error', 'critical' ]:
        parser.error('logging_level (-L) must be one of [ debug, info, warning, error, critical ]')
    if args.port <= 1024 or args.port >65535:
        parser.error('Port must be in range [1025,65535]')
    if args.timeout_cutoff<1:
        parser.error('Timeout cutoff must be > 0')

    return args

from pathlib import Path
import yaml
from urllib.request import urlretrieve
import textwrap
import sys
import os

def cmd_output(message:str,length=80,sentinel='*',sep=" "):
    '''
    useful function for formatting logging/cmd output
    Params:

    message - string to output
    length - number of characters to output
    sentinel - character used to fill majority of line
    sep - character used to create space either side of the message
    length - max length of the outputted message
    log - flag to set if output goes to just the log or both log and stdout
    '''
    message = sep + message + sep
    messages=textwrap.wrap(message,length)
    for msg in messages:
        result = f"{msg:{sentinel}^{length}}"
        print(result)

def download_Nequip(url_yaml_file,model_name,output_dir):
    ''' 
    script to download Nequip model checkpoints
    from yaml file containing models names and urls
    '''

    with open(f"{url_yaml_file}") as path:
        urls = yaml.safe_load(path)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    cmd_output(f"Downloading Model checkpoint files for NequIP",sentinel=' ')
    if model_name=='all':
        for model in urls:
            print(f"Downloading: {model}")
            urlretrieve(urls[model],f"{output_dir}/{model}-0.1.nequip.zip")
        cmd_output("*",sep="")
    elif model_name in urls:
        print(f"Downloading: {model_name}")
        urlretrieve(urls[model_name],f"{output_dir}/{model_name}-0.1.nequip.zip")
        cmd_output("*",sep="")
    else:
        print(f'unrecognised model {model_name}')
        print(f'must be one of: {urls.keys()}')
        sys.exit(22)   
    return

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(prog='download_nequip_models', description='Script to download models for Nequipo and Allegro')
    parser.add_argument('-m','--model_name',nargs='?',default='all',help='model to download checkpoint file for')
    parser.add_argument('-o','--output_path',nargs='?',default='/Models/Nequip',help='path to store model checkpoint files')
    args = parser.parse_args()
    download_Nequip('Nequip_urls.yaml',args.model_name,args.output_path)
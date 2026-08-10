import argparse
from pathlib import Path
import requests
Model_names=['MatRIS_10M_OAM', 'MatRIS_10M_MP']
urls={
    'MatRIS_10M_OAM':'https://api.figshare.com/v2/file/download/59142728',
    'MatRIS_10M_MP':'https://api.figshare.com/v2/file/download/59143058'
    }
parser = argparse.ArgumentParser(
        description="A script to download checkpoint file for a named MatRIS model."
    )
parser.add_argument("ModelName",help="Name of Model",choices=Model_names,type=str)
args = parser.parse_args()

Model = args.ModelName
# create a directory ~/.cache/matris to download files to"
dl_dir = Path(f'{Path.home()}/.cache/matris')
dl_dir.mkdir(parents=True,exist_ok=True)
response = requests.get(urls[Model])
with open(f'{dl_dir}/{Model}.pth.tar', 'wb') as f:
    f.write(response.content)
#!/bin/bash
# go through arguments and set variables as appropriate
    while getopts "hu:m:" opt; do
        case ${opt} in
        h)
            echo "Usage: $0 [OPTIONS]"
            echo "  -h        Show this help message"
            echo "  -u URL    url to download model from"
            echo "  -m MODEL_NAME    Specify which Nequip model to download"
            exit 0
            ;;
        u)
            regex='^(https?)://([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(:[0-9]{1,5})?(/.*)?$'

            if [[ "${OPTARG}" =~ $regex ]]; then
                echo "Valid URL"
                URL=${OPTARG}
            else
                echo -e "\n\nERROR: Invalid URL ${OPTARG}"
                exit 11
            fi   
        ;;
        m)
            if [[ ${OPTARG} =~ ^[A-Za-z0-9_-]+$ ]]; then
                echo "Valid"
            else
                echo -e "\n\nERROR: Invalid Model name ${OPTARG}"
                echo -e "Must only contain letters, numbers, - , or _"
                exit 11
            fi
                MODEL=${OPTARG}
        ;;
        ?)
        echo "Invalid option: -${OPTARG}." >&2
        echo "Usage: $0 [OPTIONS]" >&2
        echo "  -h        Show this help message" >&2
        echo "  -u URL    url to download model from" >&2
        echo "  -m MODEL_NAME    Specify which Nequip model to download" >&2
        exit 1
        ;;
        esac
    done

 
# create place to store checkpoints in ML_toolkit_home
mkdir -p ${ML_TOOLKIT_HOME}/Models/Nequip

# download the pre-trained models
echo Downloading model ${MODEL} from ${URL}
curl $URL -o ${ML_TOOLKIT_HOME}/Models/Nequip/${MODEL_NAME}-0.1.nequip.zip
echo "Model checkpoint saved as ${ML_TOOLKIT_HOME}/Models/Nequip/${MODEL_NAME}-0.1.nequip.zip"
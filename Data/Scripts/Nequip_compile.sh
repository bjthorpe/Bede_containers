#!/bin/bash
# go through arguments and set variables as appropriate
    while getopts "hd:M:" opt; do
        case ${opt} in
        h)
            echo "Usage: $0 [OPTIONS]"
            echo "  -h        Show this help message"
            echo "  -d DEVICE    Device to compile for must be either cuda or cpu"
            echo "  -M MODEL_NAME   Name of Nequip/Allegro model to compile"
            exit 0
            ;;
        d)
            if [ "${OPTARG}"=='cpu' ]; then
                DEVICE=${OPTARG}

            elif [ "${OPTARG}"=='cuda' ]; then
                DEVICE=${OPTARG}

            else
                echo -e "\n\nERROR: Input variable <device> (given ${OPTARG}) not valid must be either cpu or cuda.\n\n" >&2
                exit 11
            fi
            
        ;;
        
        M)
                MODEL_NAME=${OPTARG}
        ;;
        ?)
        echo "Invalid option: -${OPTARG}." >&2
        exit 1
        ;;
        esac
    done

mkdir -p ${ML_TOOLKIT_HOME}/Models/Nequip/${DEVICE}

nequip-compile ${ML_TOOLKIT_HOME}/Models/Nequip/${MODEL_NAME}-0.1.nequip.zip \
 ${ML_TOOLKIT_HOME}/Models/Nequip/${DEVICE}/${MODEL_NAME}.nequip.pt2  --device $DEVICE --mode aotinductor --target ase

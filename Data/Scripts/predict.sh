#!/bin/bash
DEVICE='cuda'
# go through arguments and set variables as appropriate
while getopts "hM:D:T:" opt; do
    case ${opt} in
    h)
        echo "Usage: $0 [OPTIONS]"
        echo "  -h        Show this help message"
        echo "  -M Model_Name  ML model to use. "
        echo "  -D Device Device to use, must be one of cpu or cuda (default is cuda)"
        echo "  -T TASK used with Meta UMA and some SevenNet models, ignored by all others."
        exit 0
        ;;
    M)
        ML_MODEL=${OPTARG}
        
    ;;
    D)
        if [ "${OPTARG}" == 'cuda' ]; then
            DEVICE=${OPTARG}
        elif [ "${OPTARG}" == 'cpu' ]; then
            DEVICE=${OPTARG}       
        else
            echo -e "\n\nERROR: Input variable <device> (given ${OPTARG}) not valid must be cpu or cuda\n\n" >&2
            exit 11
        fi
    ;;
    T)
        TASK="--task ${OPTARG}"
    ;;
    ?)
    echo "Invalid option: -${OPTARG}." >&2
    exit 1
    ;;
    esac
done

if [ "$#" -gt 0 ]; then
  echo "${!#}"
else
  echo "No positional arguments provided at least the seed number and model name are required"
  exit 1
fi

if [ -z "$ML_MODEL" ]; then
    echo "Error: Model_name is required" >&2
    exit 1
fi

if [ -z "$ML_TOOLKIT_HOME" ]; then
    echo "Error: ML_TOOLKIT_HOME not found." 
    echo " please ensure you have installed ML-toolkit though pip and run the 'install-ml-toolkit' command." >&2
    exit 1
fi
ml-toolkit run ${ML_MODEL}  python ${ML_TOOLKIT_HOME}/Scripts/ML_file.py --device=${DEVICE} ${TASK} ${ML_MODEL} "${!#}"

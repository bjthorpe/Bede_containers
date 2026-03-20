#!/bin/bash
ml-toolkit run $1 python ${ML_TOOLKIT_HOME}/Scripts/ML_file.py --device=cuda $1 $2

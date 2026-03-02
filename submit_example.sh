#!/bin/bash
# Example SLURM script for testing Ollama on Bede
# with the ML_Toolkit
##########################################
#SBATCH --account CHANGE_ME              # charge job to specified account
#SBATCH --cpus-per-task 1                # number of cpus required per task
#SBATCH --chdir /path/to/ML_Toolkit      # change working directory
#SBATCH --job-name ollama_test           # name of job
#SBATCH --ntasks 1                       # number of processes required
#SBATCH -o ollama_test.out               # File to redirect program output
#SBATCH -e ollama_test.err               # File to redirect any errors
#SBATCH --time 10                        # time limit (in mins)
#SBATCH --partition ghtest               # Choose either gh or ghtest
#SBATCH --gres gpu:1                     # Number of GPUs required for the job
##########################################
# source the python virtual environment
source ML_Toolkit/bin/activate
#  start the Ollama server.
./ML_Toolkit start Ollama_Test_Container
# inference the model via python script
./ML_Toolkit run Ollama_Test_Container python ollama_test_chat.py
# stop the sever
./ML_Toolkit stop Ollama_Test_Container
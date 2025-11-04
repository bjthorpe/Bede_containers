import subprocess, sys
command = sys.argv[1:]
subprocess.run(f"apptainer exec docker://alpine {" ".join(command)}",shell=True)


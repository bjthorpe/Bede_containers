# tests for Apptainer installation
import pytest
import subprocess

def test_Apptainer():
    """
    Test to check Apptainer installation is working correctly by downloading and
    launching a simple cowsay container.
    """
    print("*********************************************************************")
    print(f"**************** Running Cowsay test container: *********************")
    print("*********************************************************************")

    apptainer_command = (
        f"apptainer run docker://quay.io/vwbusguy/cowsay 'All looks good to me'"
    )
    proc = subprocess.run(apptainer_command, shell=True)
    assert proc.returncode == 0


# Only run if using pytest without --no_GPU flag
@pytest.mark.GPU
def test_GPU():
    """
    Test to check Apptainer installation is working correctly with a GPU by
    downloading and launching a simple ubuntu container and testing for
    the presence of either nvidia-smi or rocm-smi.
    """
    import shutil

    # check for either Nvidia or AMD gpu on host system and that it can be found
    # inside the container
    if shutil.which("nvidia-smi"):
        apptainer_command = f"apptainer run --nv docker://ubuntu:latest nvidia-smi"
        proc = subprocess.run(apptainer_command, shell=True)
        found_GPU = True
        return_code = proc.returncode
    elif shutil.which("rocm-smi"):
        apptainer_command = f"apptainer run --rocm docker://ubuntu:latest rocm-smi"
        proc = subprocess.run(apptainer_command, shell=True)
        found_GPU = True
        return_code = proc.returncode
    else:
        found_GPU = False
        return_code = -1

    assert found_GPU and return_code == 0

#!/usr/bin/env python3

import os
import subprocess
import platform
import shutil
import sys
import argparse
from pathlib import Path

def run(cmd, cwd=None):
    print(f"\n[RUN] {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {cmd}")
        sys.exit(1)

def detect_distro():
    distro = "unknown"
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("ID="):
                    distro = line.strip().split("=")[1].replace('"', '')
    print(f"[INFO] Detected distro: {distro}")
    return distro

def check_command(cmd):
    return shutil.which(cmd)

def detect_platform():
    arch = platform.machine()
    if arch in ("x86_64", "amd64"):
        print("Architecture: AMD64 / x86_64")
        arch="amd64"
    elif arch in ("aarch64", "arm64"):
        print("Architecture: ARM64")
        arch="arm64"
    else:
        print(f"Error: Unknown architecture: {arch}")
        print(f"This installer only supports X86 and ARM64 builds")
        sys.exit(1)
    return arch

def install_go_local(go_version,arch):
    if check_command("go"):
        print("[INFO] Go already installed.")
        return

    print("[INFO] Installing Go locally...")

    home = os.path.expanduser("~")
    go_tar = f"go{go_version}.linux-{arch}.tar.gz"

    run(f"wget https://go.dev/dl/{go_tar}")
    run(f"tar -C {home} -xzf {go_tar}")

    bashrc = os.path.join(home, ".bashrc")
    with open(bashrc, "a") as f:
        f.write("\n# Go environment\n")
        f.write("export PATH=$HOME/go/bin:$HOME/go/bin:$PATH\n")

    os.environ["PATH"] = f"{home}/go/bin:" + os.environ["PATH"]

def download_apptainer(apptainer_version):
    tar_file = f"apptainer-{apptainer_version}.tar.gz"

    if not os.path.exists(tar_file):
        run(
            f"wget https://github.com/apptainer/apptainer/releases/download/v{apptainer_version}/{tar_file}"
        )

    run(f"tar -xzf {tar_file}")

def build_apptainer(apptainer_version,prefix):
    src_dir = f"apptainer-{apptainer_version}"

    run(f"./mconfig --prefix={prefix}", cwd=src_dir)
    run("make -C builddir", cwd=src_dir)
    run("make -C builddir install", cwd=src_dir)

def setup_environment(prefix):
    bin_path = f"{prefix}/bin"
    bashrc = os.path.expanduser("~/.bashrc")

    with open(bashrc, "a") as f:
        f.write("\n# Apptainer\n")
        f.write(f"export PATH={bin_path}:$PATH\n")

    print(f"[INFO] Added {bin_path} to PATH")

def verify_install(prefix):
    apptainer_bin = f"{prefix}/bin/apptainer"

    if os.path.exists(apptainer_bin):
        run(f"{apptainer_bin} --version")
        print("\n[SUCCESS] Apptainer installed successfully.")
    else:
        print("[ERROR] Installation failed.")
        sys.exit(1)

def install_apptainer():

    print("==== Apptainer HPC Installer ====")
    default_apptainer_version="1.4.3"
    default_go_version="1.21.6"

    parser = argparse.ArgumentParser(prog='Install-Apptainer',
                                     description='Script to automate install of apptainer')
    help_msg = f'Installation directory for Apptainer, if not provided this defaults to {Path.home()}/.local/apptainer'
    parser.add_argument('-p','--install_prefix',nargs='?',
                        default=f'{Path.home()}/.local/apptainer',help=help_msg)
    parser.add_argument('-a', '--apptainer_version', nargs='?',
                        default=f'{default_apptainer_version}',
                        help=f'version of apptainer to download. Default is latest at time of writing V{default_apptainer_version}')
    parser.add_argument('-g', '--go_version', nargs='?',
                        default=f'{default_go_version}',
                        help=f'version of go to download. Default is latest at time of writing V{default_go_version}.')
    args = parser.parse_args()

    detect_distro()
    arch = detect_platform()
    apptainer_path = check_command("apptainer")

    apptainer_version = args.apptainer_version
    go_version = args.go_version
    install_prefix = args.install_prefix

    if apptainer_path:
        print(f"Apptainer is already installed at: {apptainer_path}")
        run(f"{apptainer_path} --version")
        return
    
    print(f"installing Apptainer version: {apptainer_version} to {install_prefix}")

    if not check_command("wget"):
        print("[ERROR] wget is required.")
        sys.exit(1)

    if not check_command("gcc"):
        print("[ERROR] gcc not found. Load compiler module (e.g., module load gcc).")
        sys.exit(1)

    install_go_local(go_version,arch)
    download_apptainer(apptainer_version)
    build_apptainer(apptainer_version=apptainer_version,prefix=install_prefix)
    setup_environment(prefix=install_prefix)
    verify_install(prefix=install_prefix)
if __name__ == "__main__":
    install_apptainer()
#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse

def setup_env():
    """Sets up the PYTHONPATH so local modules can be found."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    oot_python_path = os.path.join(current_dir, "gr-techniquemaker", "python")
    
    # Add to current process
    if oot_python_path not in sys.path:
        sys.path.insert(0, oot_python_path)
    
    # Set for subprocesses
    env = os.environ.copy()
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{oot_python_path}{os.pathsep}{existing_pp}" if existing_pp else oot_python_path
    return env

def main():
    parser = argparse.ArgumentParser(
        description="TechniqueMaker Unified Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./TechniqueMaker.py gui          # Launch the standalone GUI
  ./TechniqueMaker.py predator     # Launch the Predator Jammer Console
  ./TechniqueMaker.py calibrate    # Launch the RF System Calibrator
  ./TechniqueMaker.py batch        # Run the AI Dataset Generator
  ./TechniqueMaker.py install      # Run the OOT installation script
        """
    )
    parser.add_argument("mode", choices=["gui", "predator", "calibrate", "batch", "install"], help="What to launch")
    parser.add_argument("--args", nargs=argparse.REMAINDER, help="Additional arguments for the sub-command")

    args = parser.parse_args()
    env = setup_env()
    current_dir = os.path.dirname(os.path.abspath(__file__))

    if args.mode == "gui":
        print("--- Launching TechniqueMaker GUI ---")
        subprocess.run([sys.executable, "BaseGui.py"], env=env, cwd=current_dir)
    
    elif args.mode == "predator":
        print("--- Launching Predator Jammer Console ---")
        subprocess.run([sys.executable, "PredatorJammer.py"], env=env, cwd=current_dir)

    elif args.mode == "calibrate":
        print("--- Launching RF System Calibrator ---")
        subprocess.run([sys.executable, "SystemCalibrator.py"], env=env, cwd=current_dir)
    
    elif args.mode == "batch":
        print("--- Launching AI Batch Generator ---")
        cmd = [sys.executable, "BatchGenerator.py"]
        if args.args: cmd.extend(args.args)
        subprocess.run(cmd, env=env, cwd=current_dir)
    
    elif args.mode == "install":
        print("--- Running OOT Installation ---")
        subprocess.run(["/bin/bash", "./install.sh"], cwd=current_dir)

if __name__ == "__main__":
    main()

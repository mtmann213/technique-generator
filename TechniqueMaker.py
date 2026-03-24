#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse

def setup_env():
    """Sets up the PYTHONPATH so local modules can be found, prioritizing system installations."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    oot_python_path = os.path.join(current_dir, "gr-techniquemaker", "python")
    
    # Add to current process at the END, so system-installed compiled OOT modules take priority
    if oot_python_path not in sys.path:
        sys.path.append(oot_python_path)
    
    # Set for subprocesses
    env = os.environ.copy()
    existing_pp = env.get("PYTHONPATH", "")
    # Append local path so system paths take precedence
    env["PYTHONPATH"] = f"{existing_pp}{os.pathsep}{oot_python_path}" if existing_pp else oot_python_path
    
    # Also ensure the standard gnuradio install path is explicitly in the environment
    system_path = "/usr/local/lib/python3/dist-packages:/usr/local/lib/python3.12/site-packages:/usr/local/lib/python3.12/dist-packages"
    env["PYTHONPATH"] = f"{system_path}:{env['PYTHONPATH']}"
    
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
        subprocess.run([sys.executable, "apps/BaseGui.py"], env=env, cwd=current_dir)
    
    elif args.mode == "predator":
        print("--- Launching Predator Jammer Console ---")
        subprocess.run([sys.executable, "apps/PredatorJammer.py"], env=env, cwd=current_dir)

    elif args.mode == "calibrate":
        print("--- Launching RF System Calibrator ---")
        subprocess.run([sys.executable, "apps/SystemCalibrator.py"], env=env, cwd=current_dir)
    
    elif args.mode == "batch":
        print("--- Launching AI Batch Generator ---")
        cmd = [sys.executable, "apps/BatchGenerator.py"]
        if args.args: cmd.extend(args.args)
        subprocess.run(cmd, env=env, cwd=current_dir)
    
    elif args.mode == "install":
        print("--- Running OOT Installation ---")
        subprocess.run(["/bin/bash", "./install.sh"], cwd=current_dir)

if __name__ == "__main__":
    main()

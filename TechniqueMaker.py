#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse

def setup_env():
    """Sets up the environment so local modules can be found, prioritizing system installations."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    oot_python_path = os.path.join(current_dir, "gr-techniquemaker", "python")
    oot_build_path = os.path.join(current_dir, "gr-techniquemaker", "build", "python")
    apps_path = os.path.join(current_dir, "apps")
    
    # 1. Update sys.path for the current process
    for p in [oot_build_path, oot_python_path, apps_path]:
        if p not in sys.path:
            sys.path.insert(0, p)
            
    # 2. Return env dict for subprocesses
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    new_paths = [oot_build_path, oot_python_path, apps_path, current_dir]
    env["PYTHONPATH"] = os.pathsep.join(new_paths + ([existing_pythonpath] if existing_pythonpath else []))
    
    return env
    # 3. Setup subprocess environment
    env = os.environ.copy()
    existing_pp = env.get("PYTHONPATH", "")
    
    # Build new PYTHONPATH: System Paths -> Existing -> Local Path
    sys_pp_str = os.pathsep.join(system_paths)
    if existing_pp:
        env["PYTHONPATH"] = f"{sys_pp_str}{os.pathsep}{existing_pp}{os.pathsep}{oot_python_path}"
    else:
        env["PYTHONPATH"] = f"{sys_pp_str}{os.pathsep}{oot_python_path}"
    
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

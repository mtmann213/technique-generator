#!/usr/bin/env python3
import os
import json
import time
import random
import numpy as np
from BaseWaveforms import waveform_definitions

def generate_dataset(output_dir="dataset", samples_per_tech=100, fs=2e6, duration=0.1):
    """
    Generates a randomized SigMF dataset for all 14 techniques.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"--- Starting Dataset Generation ---")
    print(f"Output Directory: {output_dir}")
    print(f"Techniques: {len(waveform_definitions)}")
    print(f"Samples per Tech: {samples_per_tech}")
    print(f"Total Files: {len(waveform_definitions) * samples_per_tech}")

    for tech_name, tech_info in waveform_definitions.items():
        tech_dir = os.path.join(output_dir, tech_name.replace(" ", "_"))
        if not os.path.exists(tech_dir):
            os.makedirs(tech_dir)
        
        print(f"Generating: {tech_name}...")

        for i in range(samples_per_tech):
            params = {}
            for p in tech_info['params']:
                name = p['name']
                
                if name == 'sample_rate_hz': params[name] = fs; continue
                if name == 'technique_length_seconds': params[name] = duration; continue
                
                if p['type'] == 'entry':
                    # Special Case: Frequencies String
                    if 'frequencies_str' in name or 'hop_frequencies_str' in name:
                        # Create 3 random frequencies
                        f_list = [str(random.uniform(-fs/4, fs/4)) for _ in range(3)]
                        params[name] = " ".join(f_list)
                    elif 'bandwidth' in name or 'width' in name or 'sweep' in name or 'freq' in name:
                        params[name] = random.uniform(10e3, fs/2)
                    elif 'tones' in name or 'chunks' in name:
                        params[name] = random.randint(2, 10)
                    elif 'rolloff' in name:
                        params[name] = random.uniform(0.2, 0.7)
                    elif 'fft_size' in name:
                        params[name] = random.choice([512, 1024, 2048])
                    elif 'num_subcarriers' in name:
                        params[name] = random.randint(100, 400)
                    elif 'cp_length' in name:
                        params[name] = random.randint(16, 128)
                    elif 'target_value' in name:
                        params[name] = 1.0
                    else:
                        params[name] = 1.0
                elif p['type'] == 'options':
                    params[name] = random.choice(p['choices'])

            try:
                samples = tech_info['func'](**params)
                # Ensure complex
                if not np.iscomplexobj(samples):
                    samples = samples.astype(np.complex64)
                else:
                    samples = samples.astype(np.complex64)
                
                base_name = f"{tech_name.replace(' ', '_')}_{i:04d}"
                data_path = os.path.join(tech_dir, f"{base_name}.sigmf-data")
                meta_path = os.path.join(tech_dir, f"{base_name}.sigmf-meta")

                samples.tofile(data_path)

                meta = {
                    "global": {
                        "core:datatype": "cf32_le",
                        "core:sample_rate": fs,
                        "core:version": "1.0.0",
                        "core:description": f"TechniqueMaker AI Training Sample: {tech_name}",
                        "technique:name": tech_name,
                        "technique:parameters": {str(k): str(v) for k, v in params.items()}
                    },
                    "captures": [{"core:sample_start": 0, "core:frequency": 0}],
                    "annotations": []
                }
                with open(meta_path, 'w') as f:
                    json.dump(meta, f, indent=4)

            except Exception as e:
                print(f"Error generating {tech_name} sample {i}: {e}")

    print(f"--- Generation Complete! ---")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TechniqueMaker AI Factory")
    parser.add_argument("--count", type=int, default=10, help="Samples per technique")
    parser.add_argument("--fs", type=float, default=1000000, help="Sample rate")
    parser.add_argument("--duration", type=float, default=0.02, help="Duration per sample (seconds)")
    args = parser.parse_args()

    generate_dataset(samples_per_tech=args.count, fs=args.fs, duration=args.duration)

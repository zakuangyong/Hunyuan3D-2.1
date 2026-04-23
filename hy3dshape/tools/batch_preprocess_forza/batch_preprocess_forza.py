import os
import glob
import subprocess
import sys
import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.dirname(os.path.dirname(TOOLS_DIR))

DEFAULT_BLENDER_PATH = r"D:\Software\blender-5.1.0\blender.exe"
DEFAULT_INPUT_DIR = os.path.join(PROJECT_ROOT, 'datasets', '3d_model_by_forza')
DEFAULT_OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'datasets', 'forza_preprocessed')

def parse_args():
    parser = argparse.ArgumentParser(description='Batch process GLB files for Hunyuan3D-2.1 finetuning dataset')
    parser.add_argument('--input_dir', type=str, default=DEFAULT_INPUT_DIR,
                        help='Directory containing GLB files')
    parser.add_argument('--output_dir', type=str, default=DEFAULT_OUTPUT_DIR,
                        help='Output directory for preprocessed data')
    parser.add_argument('--blender_path', type=str, default=DEFAULT_BLENDER_PATH,
                        help='Path to Blender executable')
    parser.add_argument('--resolution', type=int, default=512,
                        help='Render resolution')
    parser.add_argument('--views', type=int, default=24,
                        help='Number of views to render')
    parser.add_argument('--skip_existing', action='store_true',
                        help='Skip if output already exists')
    return parser.parse_args()

def main():
    args = parse_args()

    input_dir = args.input_dir
    output_dir = args.output_dir
    blender_path = args.blender_path
    resolution = args.resolution
    views = args.views
    skip_existing = args.skip_existing

    os.makedirs(output_dir, exist_ok=True)

    glb_files = glob.glob(os.path.join(input_dir, '*.glb'))
    if not glb_files:
        print(f'No GLB files found in {input_dir}')
        sys.exit(1)

    print(f'Found {len(glb_files)} GLB files to process')

    render_script = os.path.join(TOOLS_DIR, 'render', 'render.py')
    watertight_script = os.path.join(TOOLS_DIR, 'watertight', 'watertight_and_sample.py')

    for glb_path in glb_files:
        model_name = os.path.splitext(os.path.basename(glb_path))[0]
        print(f'\n{"="*60}')
        print(f'Processing: {model_name}')
        print(f'{"="*60}')

        render_cond_dir = os.path.join(output_dir, model_name, 'render_cond')
        geo_data_dir = os.path.join(output_dir, model_name, 'geo_data')

        if skip_existing and os.path.exists(os.path.join(geo_data_dir, f'{model_name}_surface.npz')):
            print(f'Skipping {model_name} - already processed')
            continue

        os.makedirs(render_cond_dir, exist_ok=True)
        os.makedirs(geo_data_dir, exist_ok=True)

        print(f'\n[Step 1/2] Rendering {model_name}...')
        render_cmd = [
            blender_path, '-b', '-P', render_script, '--',
            '--object', glb_path,
            '--output_folder', render_cond_dir,
            '--geo_mode',
            '--resolution', str(resolution),
            '--views', str(views)
        ]

        print(f'Running: {" ".join(render_cmd)}')
        result = subprocess.run(render_cmd, capture_output=False)
        if result.returncode != 0:
            print(f'ERROR: Rendering failed for {model_name}')
            continue

        mesh_path = os.path.join(render_cond_dir, 'mesh.ply')
        if not os.path.exists(mesh_path):
            print(f'ERROR: mesh.ply not found at {mesh_path}')
            continue

        print(f'\n[Step 2/2] Processing watertight mesh for {model_name}...')
        surface_output = os.path.join(geo_data_dir, model_name)

        watertight_cmd = [
            sys.executable, watertight_script,
            '--input_obj', mesh_path,
            '--output_prefix', surface_output
        ]

        print(f'Running: {" ".join(watertight_cmd)}')
        result = subprocess.run(watertight_cmd, capture_output=False)
        if result.returncode != 0:
            print(f'ERROR: Watertight processing failed for {model_name}')
            continue

        surface_npz = f'{surface_output}_surface.npz'
        sdf_npz = f'{surface_output}_sdf.npz'

        if os.path.exists(surface_npz) and os.path.exists(sdf_npz):
            print(f'Successfully processed {model_name}')
            print(f'  - {surface_npz}')
            print(f'  - {sdf_npz}')
        else:
            print(f'WARNING: Expected output files not found')

        print(f'\nCompleted: {model_name}')

    print(f'\n{"="*60}')
    print(f'Batch processing completed!')
    print(f'Output directory: {output_dir}')
    print(f'{"="*60}')
    print(f'\nUsage in config:')
    print(f'  train_data_list: {output_dir}')
    print(f'  val_data_list: {output_dir}')

if __name__ == '__main__':
    main()

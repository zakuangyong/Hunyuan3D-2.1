import importlib.util
import os
import sys
import types
from pathlib import Path

import bpy

RENDER_PY = r"..\hy3dshape\tools\render\render.py"
MODEL_DIR = r"..\datasets\3d_model_by_forza"
OUTPUT_ROOT = r"..\hy3dshape\out_24views"
CAR_NAMES = [
    "BMW_M4_21.glb",
    "MCL_720S_18.glb",
    "MCL_P1_13.glb",
    "MER_AMGOne_21.glb",
    "MER_C63AMG_12.glb",
]
VIEWS = 24
RESOLUTION = 512
ENGINE = "CYCLES"
GEO_MODE = False
SAVE_DEPTH = False
SAVE_NORMAL = False
SAVE_ALBEDO = False
SAVE_MR = False
SAVE_MIST = False
SPLIT_NORMAL = False
SAVE_MESH = False


def _find_repo_root() -> Path:
    starts = []
    if bpy.data.filepath:
        starts.append(Path(bpy.data.filepath).resolve().parent)
    starts.append(Path.cwd().resolve())

    for start in starts:
        p = start
        for _ in range(10):
            if (p / "hy3dshape" / "tools" / "render" / "render.py").exists():
                return p
            if p.parent == p:
                break
            p = p.parent

    raise FileNotFoundError("Cannot locate repo root (missing hy3dshape/tools/render/render.py).")

def _load_render_module():
    if RENDER_PY != r"..\hy3dshape\tools\render\render.py":
        render_py = Path(os.path.abspath(RENDER_PY))
    else:
        repo_root = _find_repo_root()
        render_py = repo_root / "hy3dshape" / "tools" / "render" / "render.py"

    if not render_py.exists():
        raise FileNotFoundError(f"render.py not found: {render_py}")

    spec = importlib.util.spec_from_file_location("hy3dshape_tools_render", str(render_py))
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to import render.py from {render_py}")

    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def run_render(
    mod,
    object_path: str,
    output_folder: str,
    views: int = 24,
    resolution: int = 512,
    engine: str = "CYCLES",
    geo_mode: bool = False,
    save_depth: bool = False,
    save_normal: bool = False,
    save_albedo: bool = False,
    save_mr: bool = False,
    save_mist: bool = False,
    split_normal: bool = False,
    save_mesh: bool = False,
):
    object_path = os.path.abspath(object_path)
    output_folder = os.path.abspath(output_folder)
    os.makedirs(output_folder, exist_ok=True)

    args = types.SimpleNamespace(
        views=int(views),
        object=object_path,
        output_folder=output_folder,
        resolution=int(resolution),
        engine=str(engine),
        geo_mode=bool(geo_mode),
        save_depth=bool(save_depth),
        save_normal=bool(save_normal),
        save_albedo=bool(save_albedo),
        save_mr=bool(save_mr),
        save_mist=bool(save_mist),
        split_normal=bool(split_normal),
        save_mesh=bool(save_mesh),
    )
    mod.main(args)


if __name__ == "__main__":
    if RENDER_PY == r"..\hy3dshape\tools\render\render.py":
        raise ValueError("Please set RENDER_PY to your render.py absolute path.")
    if OUTPUT_ROOT == r"..\hy3dshape\out_24views":
        raise ValueError("Please set OUTPUT_ROOT to an output directory.")

    mod = _load_render_module()
    car_names = CAR_NAMES
    if not car_names:
        car_names = sorted([f for f in os.listdir(MODEL_DIR) if f.lower().endswith(".glb")])

    for car in car_names:
        object_path = os.path.join(MODEL_DIR, car)
        car_base = car.removesuffix(".glb")
        output_folder = os.path.join(OUTPUT_ROOT, car_base)
        run_render(
            mod=mod,
            object_path=object_path,
            output_folder=output_folder,
            views=VIEWS,
            resolution=RESOLUTION,
            engine=ENGINE,
            geo_mode=GEO_MODE,
            save_depth=SAVE_DEPTH,
            save_normal=SAVE_NORMAL,
            save_albedo=SAVE_ALBEDO,
            save_mr=SAVE_MR,
            save_mist=SAVE_MIST,
            split_normal=SPLIT_NORMAL,
            save_mesh=SAVE_MESH,
        )

"""Blender execution utilities for Arrival.

Provides functions for running Arrival scripts in Blender headless mode.
"""

import subprocess
import sys
import os
from typing import Optional


def run_script(script_path: str,
               blend_path: Optional[str] = None,
               output_path: Optional[str] = None,
               python_script: Optional[str] = None) -> subprocess.CompletedProcess:
    """Run a Python script in Blender headless mode.
    
    This is the primary way to execute Arrival scenes. The script should
    use the Arrival API to construct and render a scene.
    
    Args:
        script_path: Path to the Python script to run (mutually exclusive with python_script)
        blend_path: Optional path to a .blend file to open first
        output_path: Optional output path for the render
        python_script: Optional Python code string to run (mutually exclusive with script_path)
    
    Returns:
        subprocess.CompletedProcess with stdout/stderr
    
    Example:
        result = blender.run_script("/path/to/my_scene.py")
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
    """
    cmd = ["blender", "--background", "--python", script_path]
    
    if blend_path:
        cmd.insert(2, blend_path)
        cmd.insert(3, "--")
    
    if output_path:
        # Blender uses environment variable or -o flag
        env = os.environ.copy()
        env['ARRIVAL_OUTPUT'] = output_path
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    
    return result


def render_blend_file(blend_path: str,
                     output_path: str,
                     resolution: tuple = (960, 720),
                     samples: int = 64) -> subprocess.CompletedProcess:
    """Render a .blend file headlessly.
    
    Args:
        blend_path: Path to .blend file
        output_path: Path to save output image
        resolution: (width, height)
        samples: Render samples
    
    Returns:
        subprocess.CompletedProcess
    """
    cmd = [
        "blender",
        "--background",
        blend_path,
        "--",
        "--render-output", output_path,
        "--render-resolution-x", str(resolution[0]),
        "--render-resolution-y", str(resolution[1]),
        "--cycles-samples", str(samples)
    ]
    
    return subprocess.run(cmd, capture_output=True, text=True)


def check_blender() -> dict:
    """Check Blender installation and version.
    
    Returns:
        dict with 'installed' (bool), 'version' (str), 'path' (str)
    """
    import shutil
    
    path = shutil.which("blender")
    if not path:
        return {'installed': False, 'version': None, 'path': None}
    
    result = subprocess.run(
        ["blender", "--version"],
        capture_output=True,
        text=True
    )
    
    version = result.stdout.split('\n')[0] if result.returncode == 0 else None
    
    return {
        'installed': True,
        'version': version,
        'path': path
    }


def create_render_script(scene_code: str,
                        output_path: str,
                        resolution: tuple = (960, 720),
                        samples: int = 64) -> str:
    """Create a complete render script with scene code embedded.
    
    Args:
        scene_code: Python code that creates and renders a scene
        output_path: Path for output image
        resolution: (width, height)
        samples: Render samples
    
    Returns:
        Path to the generated script file
    """
    script = f'''
import sys
import os

# Add arrival to path
sys.path.insert(0, "{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")

# Import arrival
import bpy
from arrival import Scene, Material
from arrival.nodes import NodeTreeBuilder

# Resolution and samples
RESOLUTION = {resolution}
SAMPLES = {samples}
OUTPUT_PATH = "{output_path}"

# Scene code
{scene_code}

# Render
scene.render(OUTPUT_PATH, resolution=RESOLUTION, samples=SAMPLES)
bpy.ops.render.render(write_still=True)
'''
    
    # Write to temp file
    import tempfile
    fd, path = tempfile.mkstemp(suffix='.py', prefix='arrival_render_')
    with os.fdopen(fd, 'w') as f:
        f.write(script)
    
    return path


def execute_scene(scene_builder_code: str,
                 output_path: str = "/tmp/arrival_render.png",
                 resolution: tuple = (960, 720),
                 samples: int = 64) -> subprocess.CompletedProcess:
    """Execute scene builder code in Blender headless.
    
    This is the most convenient way to render an Arrival scene. You provide
    the scene construction code and this handles the rest.
    
    Args:
        scene_builder_code: Python code that builds a scene using Arrival API
        output_path: Path for output image
        resolution: (width, height)
        samples: Render samples
    
    Returns:
        subprocess.CompletedProcess
    
    Example:
        result = blender.execute_scene('''
        with Scene("MyScene") as scene:
            scene.add_mesh(scene.mesh_cube())
            scene.camera()
            scene.light()
        ''', output_path="/tmp/my_render.png")
    """
    # Create a complete script
    script = f'''
import bpy
import sys
import os

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Set up render
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.render.resolution_x = {resolution[0]}
scene.render.resolution_y = {resolution[1]}
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = "{output_path}"
scene.cycles.samples = {samples}

# Scene code
{scene_builder_code}

# Render
bpy.ops.render.render(write_still=True)
print(f"Rendered to {{"{output_path}"}}")
'''
    
    # Write to temp file
    import tempfile
    fd, script_path = tempfile.mkstemp(suffix='.py', prefix='arrival_')
    with os.fdopen(fd, 'w') as f:
        f.write(script)
    
    # Run in Blender
    result = subprocess.run(
        ["blender", "--background", "--python", script_path],
        capture_output=True,
        text=True
    )
    
    # Clean up temp file
    try:
        os.unlink(script_path)
    except:
        pass
    
    return result

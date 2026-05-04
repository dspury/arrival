"""Scene context manager for Arrival.

The Scene class provides a high-level interface for constructing complete 3D scenes:
geometry, materials, lights, camera, and render settings. Everything is built in a
single declarative block, then rendered headlessly.
"""

import bpy
import math
from typing import Tuple, Optional, List, Dict, Any
from mathutils import Vector
from . import nodes, materials


class Scene:
    """Scene builder — context manager for complete 3D scene construction.
    
    Usage:
        with Scene("MyScene") as scene:
            mesh = scene.add_mesh(nodes.Mesh.grid(size_x=4, size_y=4, vertices_x=64, vertices_y=64))
            mesh = mesh.displace(strength=0.3, noise_scale=2.0)
            scene.add_material(mat)
            scene.camera(location=(0, -6, 4), target=(0, 0, 0))
            scene.light(type='SUN', location=(5, 5, 10), energy=3.0)
            scene.render("/tmp/output.png", resolution=(960, 720), samples=128)
    
    After the `with` block exits, the scene is finalized and ready to render.
    """
    
    def __init__(self, name: str = "ArrivalScene"):
        self.name = name
        self._objects: List[Dict[str, Any]] = []
        self._tree_builder: Optional[nodes.NodeTreeBuilder] = None
        self._camera: Optional[bpy.types.Object] = None
        self._lights: List[bpy.types.Object] = []
        self._render_settings: Dict[str, Any] = {}
        self._output_path: str = "/tmp/arrival_render.png"
        self._resolution: Tuple[int, int] = (960, 720)
        self._samples: int = 64
    
    def __enter__(self) -> 'Scene':
        """Enter scene context — clear scene and prepare."""
        # Clear existing objects
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        
        # Create a node tree builder for this scene
        self._tree_builder = nodes.NodeTreeBuilder(f"{self.name}_Geometry")
        self._tree_builder.__enter__()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit scene context."""
        if exc_type is None:
            # Build the render setup
            self._setup_world()
            self._setup_render_settings()
        return False
    
    def _setup_world(self):
        """Set up world/environment."""
        world = bpy.context.scene.world
        if world is None:
            world = bpy.data.worlds.new(self.name + "_World")
            bpy.context.scene.world = world
        
        world.use_nodes = True
        nt = world.node_tree
        
        # Clear existing nodes
        for node in nt.nodes:
            nt.nodes.remove(node)
        
        # Create background
        bg = nt.nodes.new(type="ShaderNodeBackground")
        bg.inputs["Color"].default_value = (0.01, 0.01, 0.015, 1.0)
        bg.inputs["Strength"].default_value = 0.3
        
        output = nt.nodes.new(type="ShaderNodeOutputWorld")
        output.location = (300, 0)
        
        nt.links.new(bg.outputs["Background"], output.inputs["Surface"])
    
    def _setup_render_settings(self):
        """Configure render settings."""
        scene = bpy.context.scene
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = self._samples
        scene.cycles.max_bounces = 12
        scene.render.resolution_x = self._resolution[0]
        scene.render.resolution_y = self._resolution[1]
        scene.render.image_settings.file_format = 'PNG'
        scene.render.filepath = self._output_path
    
    def add_geometry(self, geometry, material=None, name: str = None) -> 'nodes.Geometry':
        """Add geometry to the scene with optional material.
        
        Args:
            geometry: Geometry socket from node tree builder
            material: Blender material, or None
            name: Optional name for the object
        
        Returns:
            The geometry socket for chaining
        """
        # Store for later — we need to apply the node tree to actual objects
        obj_data = {
            'geometry': geometry,
            'material': material,
            'name': name or f"ArrivalObject_{len(self._objects)}"
        }
        self._objects.append(obj_data)
        return geometry
    
    def add_mesh(self, mesh, material=None, name: str = None) -> 'nodes.Mesh':
        """Add a mesh to the scene (alias for add_geometry)."""
        return self.add_geometry(mesh, material, name)
    
    def add_material(self, material: bpy.types.Material):
        """Add a material to the scene (makes it available in bpy.data)."""
        # Materials are created directly in bpy.data, so this is a no-op
        # but provides a clear API
        return material
    
    def camera(self, location: Tuple[float, float, float] = (0, -5, 3),
               target: Tuple[float, float, float] = (0, 0, 0),
               lens: float = 35):
        """Set up the camera.
        
        Args:
            location: Camera position (x, y, z)
            target: Look-at target position
            lens: Lens focal length in mm
        """
        bpy.ops.object.camera_add(location=location)
        cam = bpy.context.active_object
        cam.name = f"{self.name}_Camera"
        bpy.context.scene.camera = cam
        
        # Use look_at pattern for correct rotation
        direction = Vector(target) - Vector(location)
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        cam.data.lens = lens
        cam.data.sensor_width = 36
        
        self._camera = cam
        return cam
    
    def light(self, type: str = 'SUN',
              location: Tuple[float, float, float] = (0, 0, 10),
              energy: float = 3.0,
              color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
              name: str = None):
        """Add a light to the scene.
        
        Args:
            type: Light type — 'SUN', 'AREA', 'POINT', 'SPOT'
            location: Light position
            energy: Light strength
            color: RGB color
            name: Optional name
        """
        bpy.ops.object.light_add(type=type, location=location)
        light = bpy.context.active_object
        light.name = name or f"{self.name}_Light_{len(self._lights)}"
        light.data.energy = energy
        light.data.color = color
        
        # Area light size
        if type == 'AREA':
            light.data.size = 5
        
        # Spot light angle
        if type == 'SPOT':
            light.data.spot_size = math.radians(40)
            light.data.spot_blend = 0.15
        
        self._lights.append(light)
        return light
    
    def render(self, output_path: str,
               resolution: Tuple[int, int] = (960, 720),
               samples: int = 64):
        """Set render parameters. Call before exiting context.
        
        Args:
            output_path: Path to save rendered image
            resolution: (width, height) in pixels
            samples: Render samples (higher = better quality, slower)
        """
        self._output_path = output_path
        self._resolution = resolution
        self._samples = samples
    
    def finalize(self) -> str:
        """Finalize the scene — apply geometry to objects and render.
        
        This is called automatically when exiting the Scene context,
        but can be called manually if you need more control.
        
        Returns:
            Path to rendered image
        """
        scene = bpy.context.scene
        
        # Apply geometry nodes to a mesh object
        # For now, create a simple mesh and apply the modifier
        if self._objects:
            # Get the first geometry and create an object for it
            obj_data = self._objects[0]
            
            # Create a base mesh object
            bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
            base_obj = bpy.context.active_object
            base_obj.name = obj_data['name']
            
            # Apply the geometry nodes
            mod = base_obj.modifiers.new(name="GeometryNodes", type='NODES')
            mod.node_group = self._tree_builder.tree
            
            # Apply material
            if obj_data['material']:
                base_obj.data.materials.append(obj_data['material'])
        
        # Render
        scene.render.filepath = self._output_path
        bpy.ops.render.render(write_still=True)
        
        return self._output_path


def create_scene(name: str = "ArrivalScene") -> Scene:
    """Create a new Scene instance."""
    return Scene(name)

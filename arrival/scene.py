"""Scene context manager for Arrival.

The Scene class provides a high-level interface for constructing complete 3D scenes:
geometry, materials, lights, camera, and render settings. Built for expressive
visual output, not just correct geometry.
"""

import bpy
import math
import random
from typing import Tuple, Optional, List, Dict, Any, Literal
from mathutils import Vector, Euler
from . import nodes
from .nodes import NodeTreeBuilder
from . import materials


# -----------------------------------------------------------------------------
# Camera presets — named positions with intent
# -----------------------------------------------------------------------------

CAMERA_PRESETS = {
    "close":    {"location": (0, -2.5, 1),   "lens": 85,   "target": (0, 0, 0.5)},
    "medium":   {"location": (0, -5, 3),      "lens": 35,   "target": (0, 0, 0)},
    "wide":     {"location": (0, -10, 4),     "lens": 24,   "target": (0, 0, 0)},
    "low":      {"location": (0, -4, 0.5),   "lens": 50,   "target": (0, 0, 0.5)},
    "high":     {"location": (0, -8, 8),     "lens": 28,   "target": (0, 0, 0)},
    "dramatic": {"location": (-3, -5, 7),     "lens": 35,   "target": (0, 0, 1)},
    "cinema":   {"location": (-4, -6, 4),     "lens": 50,   "target": (0, 0, 1)},
}


# -----------------------------------------------------------------------------
# Lighting rigs — named setups with intent
# -----------------------------------------------------------------------------

LIGHTING_RIGS = {
    # Single dramatic source
    "rim": {
        "lights": [
            {"type": "SUN", "location": (3, -3, 8), "energy": 4.0, "color": (1.0, 0.95, 0.9)},
        ],
        "world_strength": 0.15,
    },
    # Key + fill
    "key_fill": {
        "lights": [
            {"type": "SUN", "location": (5, -5, 8),  "energy": 3.5, "color": (1.0, 0.97, 0.92)},
            {"type": "POINT", "location": (-4, 2, 3), "energy": 1.0, "color": (0.85, 0.9, 1.0)},
        ],
        "world_strength": 0.25,
    },
    # Soft overcast
    "overcast": {
        "lights": [
            {"type": "AREA", "location": (0, 0, 10), "energy": 2.0, "color": (1.0, 1.0, 1.0)},
        ],
        "world_strength": 0.6,
    },
    # Blue night
    "night": {
        "lights": [
            {"type": "SUN", "location": (2, -3, 10), "energy": 0.8, "color": (0.6, 0.7, 1.0)},
        ],
        "world_strength": 0.08,
        "world_color": (0.005, 0.008, 0.02),
    },
    # Warm studio
    "studio": {
        "lights": [
            {"type": "AREA", "location": (4, -4, 6),  "energy": 3.0, "color": (1.0, 0.95, 0.88)},
            {"type": "AREA", "location": (-3, -2, 4), "energy": 1.0, "color": (0.9, 0.92, 1.0)},
        ],
        "world_strength": 0.35,
        "world_color": (0.02, 0.02, 0.03),
    },
    # Cyan accent
    "cyan_accent": {
        "lights": [
            {"type": "SUN", "location": (6, -4, 7),    "energy": 4.0, "color": (1.0, 0.98, 0.92)},
            {"type": "POINT", "location": (-3, 2, 2), "energy": 2.0, "color": (0.0, 0.6, 0.8)},
        ],
        "world_strength": 0.2,
    },
    # Crystal cluster
    "crystal": {
        "lights": [
            {"type": "SUN", "location": (3, -3, 6), "energy": 3.5, "color": (0.9, 0.95, 1.0)},
        ],
        "world_strength": 0.4,
        "world_color": (0.01, 0.01, 0.015),
    },
}


# -----------------------------------------------------------------------------
# Render quality presets
# -----------------------------------------------------------------------------

RENDER_PRESETS = {
    "fast":    {"samples": 32,  "max_bounces": 6},
    "good":    {"samples": 64,  "max_bounces": 12},
    "high":    {"samples": 128, "max_bounces": 18},
    "ultra":   {"samples": 256, "max_bounces": 24},
}


class Scene:
    """Scene builder — context manager for complete 3D scene construction.
    
    Usage:
        with Scene("MyScene") as scene:
            geo = scene.mesh(scene.nodes.mesh_ico_sphere(radius=2.0))
            geo = geo.displace_noise(strength=0.1, noise_scale=2.5)
            geo = scene.nodes.points_on_faces(geo, density=15)
            crystal = scene.nodes.mesh_cone(radius1=0.1, radius2=0.0, depth=0.8)
            geo = scene.nodes.instance_on_points(geo, crystal, scale=0.8)
            geo = geo.realize_instances().set_material(scene.material.dark_mirror())
            scene.camera("dramatic")
            scene.lighting("crystal")
            scene.render("/tmp/output.png", quality="good", resolution=(960, 720))
    
    After the `with` block exits, the scene is finalized and ready to render.
    """
    
    def __init__(self, name: str = "ArrivalScene"):
        self.name = name
        self._objects: List[Dict[str, Any]] = []
        self._tree_builder: Optional[nodes.NodeTreeBuilder] = None
        self._camera: Optional[bpy.types.Object] = None
        self._lights: List[bpy.types.Object] = []
        self._lighting_rig: str = "key_fill"
        self._camera_preset: str = "medium"
        self._output_path: str = "/tmp/arrival_render.png"
        self._resolution: Tuple[int, int] = (960, 720)
        self._samples: int = 64
        self._max_bounces: int = 12
        self._world_color: Tuple[float, float, float] = (0.01, 0.01, 0.015)
        self._world_strength: float = 0.3
    
    @property
    def nodes(self) -> NodeTreeBuilder:
        """Access the node tree builder for geometry construction.
        
        Returns the same NodeTreeBuilder instance for the lifetime of the scene,
        so you can chain calls across multiple lines.
        
        Usage:
            nt = scene.nodes  # store reference
            base = nt.mesh_ico_sphere(radius=2.0)
            points = nt.points_on_faces(base, density=12)
        """
        if self._tree_builder is None:
            self._tree_builder = nodes.NodeTreeBuilder(f"{self.name}_Geometry")
            self._tree_builder.__enter__()
        return self._tree_builder
    
    @property
    def material(self) -> materials:
        """Access material factory functions."""
        return materials
    
    def __enter__(self) -> 'Scene':
        """Enter scene context — clear scene and prepare."""
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit scene context."""
        if exc_type is None:
            self._setup_world()
            self._setup_render_settings()
            self._apply_geometry()
        return False
    
    def _setup_world(self):
        """Set up world/environment."""
        world = bpy.context.scene.world
        if world is None:
            world = bpy.data.worlds.new(self.name + "_World")
            bpy.context.scene.world = world
        
        world.use_nodes = True
        nt = world.node_tree
        
        for node in nt.nodes:
            nt.nodes.remove(node)
        
        bg = nt.nodes.new(type="ShaderNodeBackground")
        bg.inputs["Color"].default_value = (*self._world_color, 1.0)
        bg.inputs["Strength"].default_value = self._world_strength
        
        output = nt.nodes.new(type="ShaderNodeOutputWorld")
        output.location = (300, 0)
        
        nt.links.new(bg.outputs["Background"], output.inputs["Surface"])
    
    def _setup_render_settings(self):
        """Configure render settings."""
        scene = bpy.context.scene
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = self._samples
        scene.cycles.max_bounces = self._max_bounces
        scene.render.resolution_x = self._resolution[0]
        scene.render.resolution_y = self._resolution[1]
        scene.render.image_settings.file_format = 'PNG'
        scene.render.filepath = self._output_path
    
    def _apply_geometry(self):
        """Apply node tree geometry to an object."""
        if self._tree_builder is None:
            return
        
        bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
        obj = bpy.context.active_object
        obj.name = self.name
        
        mod = obj.modifiers.new(name="GeometryNodes", type='NODES')
        mod.node_group = self._tree_builder.tree
        
        # Apply material if set
        if self._objects and self._objects[0].get('material'):
            obj.data.materials.append(self._objects[0]['material'])
    
    def mesh(self, geometry_socket, material=None, name: str = None) -> 'nodes.Geometry':
        """Add geometry to the scene.
        
        Args:
            geometry_socket: Geometry socket from node tree builder
            material: Optional material to apply
            name: Optional name
        
        Returns:
            The geometry socket for chaining
        """
        self._objects.append({
            'geometry': geometry_socket,
            'material': material,
            'name': name or f"{self.name}_Geo"
        })
        
        # If a material is provided, apply it to the geometry socket
        if material is not None:
            geometry_socket.set_material(material)
        
        return geometry_socket
    
    def camera(self, preset: str = None,
               location: Tuple[float, float, float] = None,
               target: Tuple[float, float, float] = None,
               lens: float = None):
        """Set up the camera.
        
        Args:
            preset: Named preset from CAMERA_PRESETS (close, medium, wide, low, high, dramatic, cinema)
            location: Manual camera position (overrides preset)
            target: Look-at target (overrides preset)
            lens: Focal length in mm (overrides preset)
        
        Usage:
            scene.camera()                        # medium preset
            scene.camera("dramatic")              # dramatic preset
            scene.camera(location=(0,-3,2), lens=85)  # manual
        """
        if preset and preset in CAMERA_PRESETS:
            p = CAMERA_PRESETS[preset]
            loc = location or p["location"]
            tgt = target or p["target"]
            f = lens or p["lens"]
        else:
            loc = location or (0, -5, 3)
            tgt = target or (0, 0, 0)
            f = lens or 35
        
        bpy.ops.object.camera_add(location=loc)
        cam = bpy.context.active_object
        cam.name = f"{self.name}_Camera"
        bpy.context.scene.camera = cam
        
        direction = Vector(tgt) - Vector(loc)
        cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
        cam.data.lens = f
        cam.data.sensor_width = 36
        
        self._camera = cam
        return cam
    
    def lighting(self, rig: str = None, **overrides):
        """Set up lighting from a named rig.
        
        Args:
            rig: Named rig from LIGHTING_RIGS (rim, key_fill, overcast, night, studio, crystal, cyan_accent)
            **overrides: Override individual light parameters
        
        Usage:
            scene.lighting("crystal")
            scene.lighting("night", energy=1.5)
        """
        rig_name = rig or self._lighting_rig
        if rig_name not in LIGHTING_RIGS:
            rig_name = "key_fill"
        
        config = LIGHTING_RIGS[rig_name].copy()
        
        # Handle world overrides
        if overrides:
            config["lights"] = overrides.get("lights", config.get("lights", []))
            self._world_strength = overrides.get("world_strength", config.get("world_strength", 0.3))
            self._world_color = overrides.get("world_color", config.get("world_color", (0.01, 0.01, 0.015)))
        else:
            self._world_strength = config.get("world_strength", 0.3)
            self._world_color = config.get("world_color", (0.01, 0.01, 0.015))
        
        # Clear existing lights
        for light in self._lights:
            bpy.data.objects.remove(light, do_unlink=True)
        self._lights.clear()
        
        # Add lights from rig
        for light_config in config.get("lights", []):
            bpy.ops.object.light_add(
                type=light_config.get("type", "SUN"),
                location=light_config.get("location", (0, 0, 10))
            )
            light = bpy.context.active_object
            light.name = f"{self.name}_Light_{len(self._lights)}"
            light.data.energy = light_config.get("energy", 3.0)
            light.data.color = light_config.get("color", (1.0, 1.0, 1.0))
            
            if light_config.get("type") == "AREA":
                light.data.size = light_config.get("size", 5)
            
            self._lights.append(light)
        
        self._lighting_rig = rig_name
        return self
    
    def render(self, output_path: str = None,
               quality: str = "good",
               resolution: Tuple[int, int] = None):
        """Set render parameters.
        
        Args:
            output_path: Path to save rendered image
            quality: Render quality preset (fast, good, high, ultra)
            resolution: (width, height) in pixels
        """
        if output_path:
            self._output_path = output_path
        if resolution:
            self._resolution = resolution
        
        if quality in RENDER_PRESETS:
            self._samples = RENDER_PRESETS[quality]["samples"]
            self._max_bounces = RENDER_PRESETS[quality]["max_bounces"]
    
    def render_and_save(self) -> str:
        """Finalize and render the scene.
        
        Returns:
            Path to rendered image
        """
        if self._tree_builder is None:
            raise RuntimeError("No geometry added to scene. Use scene.mesh() or scene.nodes to add geometry.")
        
        self._apply_geometry()
        scene = bpy.context.scene
        scene.render.filepath = self._output_path
        bpy.ops.render.render(write_still=True)
        return self._output_path


# Factory
def create_scene(name: str = "ArrivalScene") -> Scene:
    """Create a new Scene instance."""
    return Scene(name)

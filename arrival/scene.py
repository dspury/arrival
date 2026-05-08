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
from . import sockets
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

# NOTE: Energy values are tuned so that dark/low-albedo materials (obsidian, dark_mirror)
# render with visible detail out of the box. Area lights need much higher energy than Suns
# (Sun energy is "watts/m^2 over the whole scene"; Area is "total watts" and falls off with
# distance). World strength is also bumped from earlier defaults so global fill isn't crushed.
LIGHTING_RIGS = {
    # Single dramatic source
    "rim": {
        "lights": [
            {"type": "SUN", "location": (3, -3, 8), "energy": 5.0, "color": (1.0, 0.95, 0.9)},
        ],
        "world_strength": 0.5,
    },
    # Key + fill
    "key_fill": {
        "lights": [
            {"type": "SUN",   "location": (5, -5, 8),  "energy": 4.5, "color": (1.0, 0.97, 0.92)},
            {"type": "AREA",  "location": (-4, 2, 3),  "energy": 200.0, "size": 5, "color": (0.85, 0.9, 1.0)},
        ],
        "world_strength": 0.8,
    },
    # Soft overcast
    "overcast": {
        "lights": [
            {"type": "AREA", "location": (0, 0, 10), "energy": 600.0, "size": 10, "color": (1.0, 1.0, 1.0)},
        ],
        "world_strength": 1.5,
    },
    # Blue night
    "night": {
        "lights": [
            {"type": "SUN", "location": (2, -3, 10), "energy": 1.5, "color": (0.6, 0.7, 1.0)},
        ],
        "world_strength": 0.3,
        "world_color": (0.005, 0.008, 0.02),
    },
    # Warm studio — tuned for dark materials (obsidian, dark_mirror)
    "studio": {
        "lights": [
            {"type": "AREA", "location": (4, -4, 6),  "energy": 500.0, "size": 5, "color": (1.0, 0.95, 0.88)},
            {"type": "AREA", "location": (-3, -2, 4), "energy": 200.0, "size": 4, "color": (0.9, 0.92, 1.0)},
        ],
        "world_strength": 2.0,
        "world_color": (0.04, 0.04, 0.06),
    },
    # Cyan accent
    "cyan_accent": {
        "lights": [
            {"type": "SUN",   "location": (6, -4, 7),  "energy": 5.0, "color": (1.0, 0.98, 0.92)},
            {"type": "AREA",  "location": (-3, 2, 2),  "energy": 150.0, "size": 3, "color": (0.0, 0.6, 0.8)},
        ],
        "world_strength": 0.6,
    },
    # Crystal cluster
    "crystal": {
        "lights": [
            {"type": "SUN",  "location": (3, -3, 6),  "energy": 4.5, "color": (0.9, 0.95, 1.0)},
            {"type": "AREA", "location": (-2, -3, 4), "energy": 250.0, "size": 4, "color": (0.95, 0.97, 1.0)},
        ],
        "world_strength": 1.2,
        "world_color": (0.015, 0.018, 0.025),
    },
    # Bright studio — strong illumination for very dark/absorptive materials
    "bright_studio": {
        "lights": [
            {"type": "AREA", "location": (4, -4, 6),  "energy": 1000.0, "size": 6, "color": (1.0, 0.97, 0.92)},
            {"type": "AREA", "location": (-3, -2, 4), "energy": 400.0,  "size": 4, "color": (0.9, 0.93, 1.0)},
        ],
        "world_strength": 2.5,
        "world_color": (0.05, 0.05, 0.07),
    },
    # HDRI-like — use a procedural sky for ambient illumination, no direct lights
    "hdri": {
        "lights": [
            {"type": "SUN", "location": (4, -3, 8), "energy": 3.0, "color": (1.0, 0.97, 0.92)},
        ],
        "use_sky": True,
        "world_strength": 1.0,
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
        self._world_color: Tuple[float, float, float] = (0.04, 0.04, 0.06)
        self._world_strength: float = 1.0
        self._use_sky: bool = False
        self._sky_params: Dict[str, Any] = {
            "sun_elevation": 0.6,    # radians (~34°)
            "sun_rotation": 0.3,
            "sun_intensity": 0.8,
            "air_density": 1.0,
            "dust_density": 1.0,
            "ozone_density": 1.0,
            "ground_albedo": 0.3,
        }
    
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
        bg.inputs["Strength"].default_value = self._world_strength

        output = nt.nodes.new(type="ShaderNodeOutputWorld")
        output.location = (400, 0)

        if self._use_sky:
            sky = nt.nodes.new(type="ShaderNodeTexSky")
            sky.location = (-300, 0)
            # Nishita is the modern physical sky in Blender 3.0+/4.x/5.x
            try:
                sky.sky_type = 'NISHITA'
                sp = self._sky_params
                sky.sun_elevation = sp.get("sun_elevation", 0.6)
                sky.sun_rotation = sp.get("sun_rotation", 0.3)
                sky.sun_intensity = sp.get("sun_intensity", 0.8)
                sky.air_density = sp.get("air_density", 1.0)
                sky.dust_density = sp.get("dust_density", 1.0)
                sky.ozone_density = sp.get("ozone_density", 1.0)
                sky.ground_albedo = sp.get("ground_albedo", 0.3)
            except (AttributeError, TypeError):
                pass
            nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
        else:
            bg.inputs["Color"].default_value = (*self._world_color, 1.0)

        nt.links.new(bg.outputs["Background"], output.inputs["Surface"])
    
    def _setup_render_settings(self):
        """Configure render settings."""
        scene = bpy.context.scene
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = self._samples
        scene.cycles.max_bounces = self._max_bounces
        scene.cycles.use_denoising = True
        scene.render.resolution_x = self._resolution[0]
        scene.render.resolution_y = self._resolution[1]
        scene.render.image_settings.file_format = 'PNG'
        scene.render.filepath = self._output_path
        # Fix dark renders: Filmic/AgX crushes mid-tones on near-black materials.
        # Bump exposure so dark objects read as "dark" instead of "black hole".
        scene.view_settings.exposure = 0.5
        scene.view_settings.look = "AgX - Medium High Contrast"
    
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
        
        # Wire geometry to group output so the node tree actually outputs something.
        # Use the geometry socket's own tree — the geometry was built by whatever
        # helper created it (e.g. crystal_cluster), and that tree's GroupOutput
        # is where we need to wire the modifier.
        builder = geometry_socket._node
        builder.set_output(geometry_socket)
        
        # Point the scene's tree builder at the correct tree BEFORE _apply_geometry runs.
        # This matters because scene.nodes property creates a new tree if _tree_builder
        # is None — so we must set it here, before anything else accesses scene.nodes.
        self._tree_builder = builder
        
        return geometry_socket
    
    # ─────────────────────────────────────────────────────────────────────────────
    # Convenience shape constructors — one call to get a complete shape
    # ─────────────────────────────────────────────────────────────────────────────
    
    def crystal_cluster(
        self,
        radius: float = 2.0,
        subdivisions: int = 3,
        density: float = 12.0,
        crystal_radius: float = 0.12,
        crystal_depth: float = 0.9,
        crystal_scale: float = 0.7,
        seed: int = 7,
        displacement_strength: float = 0.08,
        displacement_scale: float = 3.0,
        material=None,
        location: Tuple[float, float, float] = (0, 0, 0),
        name: str = None,
    ) -> sockets.Geometry:
        """Create a crystal cluster: ico sphere base with pointed crystal instances.
        
        This is a complete shape in one call — no need to manually chain
        mesh_ico_sphere -> points_on_faces -> instance_on_points -> realize_instances.
        
        Args:
            radius: Size of the base ico sphere
            subdivisions: Detail level of the base (higher = more facets)
            density: Number of crystal instances per face
            crystal_radius: Base radius of crystal cones
            crystal_depth: Height of crystal cones  
            crystal_scale: Scale factor for crystal instances
            seed: Random seed for point distribution
            displacement_strength: How much to displace the base surface
            displacement_scale: Scale of the noise displacement
            material: Optional material to apply to the cluster
            location: Optional translation for the entire cluster
            name: Optional name for this geometry
        
        Returns:
            Geometry socket with realized instances
        
        Example:
            with Scene("MyScene") as scene:
                geo = scene.crystal_cluster(density=15.0, material=dark_mirror())
                scene.camera("dramatic")
                scene.lighting("crystal")
                scene.render("/tmp/crystals.png")
        """
        from examples.recipes import crystal_cluster
        realized = crystal_cluster(
            radius=radius,
            subdivisions=subdivisions,
            density=density,
            crystal_radius=crystal_radius,
            crystal_depth=crystal_depth,
            crystal_scale=crystal_scale,
            seed=seed,
            displacement_strength=displacement_strength,
            displacement_scale=displacement_scale,
            material=material,
        )
        
        # Apply optional location transform
        if location != (0, 0, 0):
            realized = realized.transform(translation=location)
        
        return self.mesh(realized, material=None, name=name or "CrystalCluster")
    
    def rocky_cluster(
        self,
        radius: float = 2.0,
        subdivisions: int = 2,
        density: float = 10.0,
        seed: int = 42,
        displacement_strength: float = 0.15,
        displacement_scale: float = 2.5,
        material=None,
        location: Tuple[float, float, float] = (0, 0, 0),
        name: str = None,
    ) -> sockets.Geometry:
        """Create a rocky cluster: displaced ico sphere with no crystal instances.
        
        Good for asteroids, ore deposits, or organic rock formations.
        
        Args:
            radius: Size of the base ico sphere
            subdivisions: Detail level
            density: Point density for surface detail
            seed: Random seed
            displacement_strength: Surface roughness
            displacement_scale: Scale of displacement noise
            material: Optional material
            location: Optional translation for the entire cluster
            name: Optional name for this geometry
        
        Returns:
            Geometry socket
        """
        from examples.recipes import rocky_cluster
        realized = rocky_cluster(
            radius=radius,
            subdivisions=subdivisions,
            density=density,
            seed=seed,
            displacement_strength=displacement_strength,
            displacement_scale=displacement_scale,
            material=material,
        )
        
        if location != (0, 0, 0):
            realized = realized.transform(translation=location)
        
        return self.mesh(realized, material=None, name=name or "RockyCluster")
    
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

        self._world_strength = overrides.get("world_strength", config.get("world_strength", 1.0))
        self._world_color = overrides.get("world_color", config.get("world_color", (0.04, 0.04, 0.06)))
        if "use_sky" in overrides:
            self._use_sky = overrides["use_sky"]
        elif "use_sky" in config:
            self._use_sky = config["use_sky"]
        if "lights" in overrides:
            config["lights"] = overrides["lights"]
        
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
    
    def hdri(self, enabled: bool = True,
             sun_elevation: float = None,
             sun_rotation: float = None,
             sun_intensity: float = None,
             strength: float = None,
             ground_albedo: float = None) -> 'Scene':
        """Enable a procedural sky (Nishita Sky Texture) as the world environment.

        This uses Blender's built-in physical sky model — no external HDRI files needed.
        Provides realistic ambient illumination that helps dark materials read properly.

        Args:
            enabled: Toggle sky on/off
            sun_elevation: Sun angle above horizon, in radians (0 = horizon, ~1.57 = zenith)
            sun_rotation: Sun azimuth, in radians
            sun_intensity: Sun disc brightness multiplier
            strength: World background strength multiplier
            ground_albedo: Reflectance of virtual ground (0-1)

        Returns:
            self, for chaining
        """
        self._use_sky = enabled
        if sun_elevation is not None:
            self._sky_params["sun_elevation"] = sun_elevation
        if sun_rotation is not None:
            self._sky_params["sun_rotation"] = sun_rotation
        if sun_intensity is not None:
            self._sky_params["sun_intensity"] = sun_intensity
        if ground_albedo is not None:
            self._sky_params["ground_albedo"] = ground_albedo
        if strength is not None:
            self._world_strength = strength
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

        self._setup_world()
        self._setup_render_settings()
        scene = bpy.context.scene
        scene.render.filepath = self._output_path
        bpy.ops.render.render(write_still=True)
        return self._output_path

    # ─────────────────────────────────────────────────────────────────────────────
    # JSON Serialization
    # ─────────────────────────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialize the scene to a dictionary for JSON round-trip.
        
        Returns:
            dict with keys: name, geometry (output node name, named geometries),
            camera_position, camera_rotation, lights (list of light configs),
            background (color, world_strength, use_sky, sky_params),
            render_settings (samples, resolution, max_bounces)
        """
        # Camera position/rotation
        camera_position = None
        camera_rotation = None
        if self._camera is not None:
            camera_position = tuple(self._camera.location)
            camera_rotation = tuple(self._camera.rotation_euler)
        
        # Light configs
        lights_config = []
        for light in self._lights:
            light_dict = {
                "type": light.type,
                "location": tuple(light.location),
                "energy": light.data.energy,
                "color": tuple(light.data.color),
            }
            if light.type == "AREA":
                light_dict["size"] = light.data.size
            lights_config.append(light_dict)
        
        # Geometry info - output node tree name and any named geometries
        geometry_info = {
            "node_tree_name": self._tree_builder.tree.name if self._tree_builder else None,
            "named_geometries": [
                obj.get("name") for obj in self._objects if obj.get("name")
            ],
        }
        
        # Background/environment
        background = {
            "color": self._world_color,
            "world_strength": self._world_strength,
            "use_sky": self._use_sky,
            "sky_params": self._sky_params.copy() if self._sky_params else {},
        }
        
        # Render settings
        render_settings = {
            "samples": self._samples,
            "resolution": self._resolution,
            "max_bounces": self._max_bounces,
        }
        
        return {
            "name": self.name,
            "geometry": geometry_info,
            "camera_position": camera_position,
            "camera_rotation": camera_rotation,
            "lights": lights_config,
            "background": background,
            "render_settings": render_settings,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Scene':
        """Reconstruct a Scene from a dictionary.
        
        Args:
            data: Dictionary with scene configuration
            
        Returns:
            Scene object (not yet entered - caller must use context manager)
        """
        scene = cls(name=data.get("name", "ArrivalScene"))
        
        # Restore render settings
        rs = data.get("render_settings", {})
        scene._samples = rs.get("samples", 64)
        scene._resolution = rs.get("resolution", (960, 720))
        scene._max_bounces = rs.get("max_bounces", 12)
        
        # Restore background
        bg = data.get("background", {})
        scene._world_color = tuple(bg.get("color", (0.04, 0.04, 0.06)))
        scene._world_strength = bg.get("world_strength", 1.0)
        scene._use_sky = bg.get("use_sky", False)
        scene._sky_params = bg.get("sky_params", {}).copy()
        
        # Restore camera position/rotation if provided
        # Note: Camera won't be created until scene is entered (requires Blender context)
        # Store for later restoration
        scene._camera_data = data.get("camera_position"), data.get("camera_rotation")
        
        # Restore light configs (lights won't be created until scene is entered)
        scene._light_configs = data.get("lights", [])
        
        # Store geometry info
        geo = data.get("geometry", {})
        scene._geometry_node_tree_name = geo.get("node_tree_name")
        scene._named_geometries = geo.get("named_geometries", [])
        
        return scene


# Factory
def create_scene(name: str = "ArrivalScene") -> Scene:
    """Create a new Scene instance."""
    return Scene(name)


# ─────────────────────────────────────────────────────────────────────────────
# One-call render — the matplotlib moment
# ─────────────────────────────────────────────────────────────────────────────

def show(geometry,
         *,
         output_path: str = None,
         resolution: Tuple[int, int] = (800, 600),
         samples: int = 128,
         background: str = "dark",
         camera: str = "medium",
         material = None) -> str:
    """Render geometry with sensible defaults — no setup required.

    This is the ``plt.show()`` equivalent for Arrival. It wraps geometry in
    a complete scene (camera, lights, material, background) and renders it.

    Args:
        geometry: A Geometry or Mesh socket wrapper from NodeTreeBuilder
        output_path: Where to save the PNG. Default: ``/tmp/arrival_render_YYYYMMDD_HHMMSS.png``
        resolution: (width, height) in pixels. Default: (800, 600)
        samples: Render samples. 128 is fast and clean for preview. Default: 128
        background: ``"dark"`` (dark gray), ``"sky"`` (procedural Nishita sky),
            or ``"black"``. Default: ``"dark"``
        camera: Camera preset from ``Scene`` presets. Default: ``"medium"``
        material: A Material from ``arrival.materials``, or None for auto.
            Default: None (uses a neutral gray material)

    Returns:
        Path to the rendered PNG file.

    Example:
        >>> path = arrival.show(geometry)
        >>> print(path)
        /tmp/arrival_render_20260507_143052.png
    """
    from datetime import datetime
    from .nodes import Geometry, Mesh

    # Resolve geometry type
    if not isinstance(geometry, (Geometry, Mesh)):
        raise TypeError(
            f"show() requires a Geometry or Mesh socket wrapper, "
            f"got: {type(geometry).__name__}"
        )

    # Default output path with timestamp
    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/tmp/arrival_render_{ts}.png"

    # Auto-material: neutral gray if none provided
    if material is None:
        from . import materials as _m
        material = _m.gray()

    # Build the scene
    scene = Scene("ArrivalShow")
    scene.mesh(geometry, material=material)
    scene.camera(preset=camera)

    # Background
    if background == "sky":
        scene.hdri(enabled=True)
    elif background == "black":
        scene.background(color=(0, 0, 0))

    # Lighting
    scene.lighting(rig="studio")

    # Render settings
    scene._samples = samples
    scene._resolution = resolution
    scene._output_path = output_path

    return scene.render_and_save()


# ─────────────────────────────────────────────────────────────────────────────
# Scene description for LLM context windows
# ─────────────────────────────────────────────────────────────────────────────

def describe(scene_or_path) -> str:
    """Describe a rendered scene for inclusion in an LLM context window.

    Takes either a Scene object (which will be rendered first) or a path to
    an existing rendered PNG. Returns a concise text description covering
    geometry type/complexity, approximate bounding box, material colors,
    lighting mood, and overall composition.

    Note: this function returns the description *text directly*. If you are
    running inside an agent context with access to a vision tool, use
    ``arrival.vision_describe(path)`` instead — it pipes the image through
    vision analysis for richer output.

    Args:
        scene_or_path: A Scene object to render and describe, or a path string
                       to an already-rendered PNG file.

    Returns:
        str: A concise text description suitable for an LLM context window.

    Example:
        >>> path = arrival.show(geometry)
        >>> desc = arrival.describe(path)
        >>> print(desc)
        A crystal cluster floating in dark space. Geometry: pointed hexagonal
        prisms in a roughly spherical formation (~2m diameter)...
    """
    import os

    # Resolve scene or path to an image file path
    if isinstance(scene_or_path, Scene):
        if scene_or_path._tree_builder is None:
            raise RuntimeError(
                "Scene has no geometry. Add geometry with scene.mesh() or "
                "scene.nodes before describing."
            )
        image_path = scene_or_path.render_and_save()
    elif isinstance(scene_or_path, str) and os.path.isfile(scene_or_path):
        image_path = scene_or_path
    else:
        raise TypeError(
            "Expected a Scene object or a path to a PNG file. "
            f"Got: {type(scene_or_path).__name__}"
        )

    # Use vision analysis to produce the description
    # NOTE: this requires the caller to be an agent with vision tool access.
    # The vision_analyze tool is mcp_minimax_understand_image. If called from
    # a non-agent context, this will fail. If called from an agent that has
    # the vision tool available, the agent should call vision_analyze directly
    # rather than invoking describe() — describe() is the public API, the agent
    # bridges to the tool.
    #
    # For programmatic use (tests, scripts): use _describe_via_subprocess
    # which runs a headless Blender + vision analysis as a subprocess.
    try:
        from hermes_tools import vision_analyze as _va
        result = _va(
            image_url=image_path,
            question=(
                "Provide a concise description of this 3D render suitable for an LLM context window. "
                "Include all of the following:\n"
                "1. Geometry type and complexity (e.g., crystalline forms, organic surfaces, hard-surface primitives)\n"
                "2. Approximate bounding box or scale (e.g., 'spanning ~2m across')\n"
                "3. Dominant material colors and surface qualities (e.g., dark mirror-like, pale matte, metallic gold)\n"
                "4. Lighting mood (e.g., dramatic contrast, soft overcast, cool night)\n"
                "5. Overall composition and visual impression (e.g., centered subject, sparse background, dense cluster)\n"
                "Keep the description under 300 words."
            ),
        )
        return result if isinstance(result, str) else str(result)
    except (ImportError, Exception):
        # Fallback: basic scene stats if vision isn't available
        return (
            f"Arrival scene rendered to {image_path}. "
            "Run with an agent that has vision tool access for full description."
        )

import bpy
import os
import math
import sys

# Disable glTF background notifications
try:
    import io_scene_gltf2.blender.exp.export as gltf_export
    def dummy_notify(*args, **kwargs):
        pass
    gltf_export.__notify_start = dummy_notify
    gltf_export.__notify_end = dummy_notify
except Exception as e:
    pass

# Mock window and context for background Blender running
class MockWindow:
    def __init__(self):
        self._scene = None
    @property
    def scene(self):
        return self._scene or bpy.context.scene
    @scene.setter
    def scene(self, value):
        self._scene = value
    def cursor_set(self, *args, **kwargs):
        pass
    def cursor_modal_set(self, *args, **kwargs):
        pass
    def cursor_modal_restore(self, *args, **kwargs):
        pass

if not hasattr(sys.modules['bpy'].context, "is_mocked"):
    class MockContext:
        is_mocked = True
        def __init__(self, original_context):
            self._orig = original_context
            self.window = MockWindow()
        def __getattr__(self, name):
            if name == "active_object":
                return self._orig.view_layer.objects.active
            return getattr(self._orig, name)
    sys.modules['bpy'].context = MockContext(sys.modules['bpy'].context)

# Cozy Thailand Palette definitions
PALETTE = {
    # Chiang Mai
    "MountainGreen": (0.15, 0.45, 0.25, 1.0),
    "WarmOrange": (0.85, 0.35, 0.1, 1.0),
    "LanternGold": (0.92, 0.72, 0.2, 1.0),
    "SoftBrown": (0.6, 0.42, 0.28, 1.0),
    "PineGreen": (0.1, 0.35, 0.2, 1.0),
    
    # Phuket
    "OceanBlue": (0.15, 0.55, 0.8, 1.0),
    "CoralOrange": (0.9, 0.4, 0.3, 1.0),
    "CoconutGreen": (0.25, 0.65, 0.35, 1.0),
    "SunsetPink": (0.88, 0.5, 0.6, 1.0),
    "BeachSand": (0.92, 0.82, 0.62, 1.0),
    "PureWhite": (0.95, 0.95, 0.95, 1.0),
    
    # Ayutthaya
    "SandstoneGold": (0.82, 0.62, 0.32, 1.0),
    "TempleCream": (0.92, 0.88, 0.8, 1.0),
    "WarmBrown": (0.5, 0.35, 0.22, 1.0),
    "RiverBlue": (0.25, 0.5, 0.7, 1.0),
    "RuinRed": (0.68, 0.3, 0.22, 1.0),
    "LeafGreen": (0.3, 0.55, 0.3, 1.0),
}

def get_material(name, color):
    if name in bpy.data.materials:
        mat = bpy.data.materials[name]
    else:
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    principled = nodes.get("Principled BSDF")
    if principled:
        principled.inputs['Base Color'].default_value = color
        if 'Roughness' in principled.inputs:
            principled.inputs['Roughness'].default_value = 0.7
        if 'Metallic' in principled.inputs:
            principled.inputs['Metallic'].default_value = 0.05
    return mat

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for col in list(bpy.data.collections):
        bpy.data.collections.remove(col)
    for block in list(bpy.data.meshes):
        bpy.data.meshes.remove(block)
    for block in list(bpy.data.materials):
        if block.name not in ["mat_gold", "mat_sandstone", "mat_lanna_wood", "mat_ocean_blue", "mat_tropical_green", "mat_roof_red", "mat_temple_cream"]:
            bpy.data.materials.remove(block)

def select_and_activate(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def make_root(name):
    empty = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(empty)
    return empty

def make_cube(name, size, location, rotation=(0, 0, 0), parent=None, material=None):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    obj.rotation_euler = rotation
    obj.location = location
    
    select_and_activate(obj)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    
    if parent:
        obj.parent = parent
    if material:
        obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj

def make_cylinder(name, radius, depth, location, rotation=(0, 0, 0), parent=None, material=None, vertices=8):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    
    select_and_activate(obj)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    
    if parent:
        obj.parent = parent
    if material:
        obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj

def make_sphere(name, radius, location, parent=None, material=None, segments=8, rings=6):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    
    if parent:
        obj.parent = parent
    if material:
        obj.data.materials.append(material)
    select_and_activate(obj)
    bpy.ops.object.shade_smooth()
    return obj

def make_cone(name, radius, depth, location, rotation=(0, 0, 0), parent=None, material=None, vertices=8):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    
    select_and_activate(obj)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    
    if parent:
        obj.parent = parent
    if material:
        obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj

def export_glb(root_obj, filepath):
    bpy.ops.object.select_all(action='DESELECT')
    def select_recursive(obj):
        obj.select_set(True)
        for child in obj.children:
            select_recursive(child)
    select_recursive(root_obj)
    bpy.context.view_layer.objects.active = root_obj
    
    # Apply visual transforms to all selected mesh children
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH':
            select_and_activate(obj)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            
    # Set parent empty at origin
    select_and_activate(root_obj)
    root_obj.location = (0, 0, 0)
    root_obj.rotation_euler = (0, 0, 0)
    root_obj.scale = (1, 1, 1)
    
    # Reselect all
    bpy.ops.object.select_all(action='DESELECT')
    select_recursive(root_obj)
    
    # Export Selected GLB
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format='GLB',
        use_selection=True
    )

# --- CHIANG MAI MODELS ---

def create_doi_suthep(dir_path):
    root = make_root("doi_suthep")
    m_gold = get_material("mat_gold", PALETTE["LanternGold"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    m_wood = get_material("mat_lanna_wood", PALETTE["SoftBrown"])
    m_red = get_material("mat_roof_red", PALETTE["RuinRed"])
    
    # Platform Base Steps
    make_cube("base1", (0.9, 0.9, 0.12), (0.0, 0.0, 0.06), parent=root, material=m_cream)
    make_cube("base2", (0.7, 0.7, 0.12), (0.0, 0.0, 0.18), parent=root, material=m_cream)
    make_cube("base3", (0.5, 0.5, 0.1), (0.0, 0.0, 0.29), parent=root, material=m_cream)
    
    # Golden multi-tier pagoda main body (spire)
    make_cylinder("chedi_base", 0.2, 0.2, (0.0, 0.0, 0.44), parent=root, material=m_gold, vertices=8)
    make_cylinder("chedi_tier1", 0.16, 0.15, (0.0, 0.0, 0.615), parent=root, material=m_gold, vertices=8)
    make_cone("chedi_spire1", 0.12, 0.22, (0.0, 0.0, 0.8), parent=root, material=m_gold, vertices=8)
    make_cone("chedi_spire2", 0.08, 0.18, (0.0, 0.0, 1.0), parent=root, material=m_gold, vertices=8)
    make_cylinder("chedi_top", 0.015, 0.18, (0.0, 0.0, 1.18), parent=root, material=m_gold)
    
    # Golden roof canopy (Lanna architecture style) at the front
    make_cube("front_pillar_l", (0.04, 0.04, 0.3), (-0.24, 0.24, 0.49), parent=root, material=m_wood)
    make_cube("front_pillar_r", (0.04, 0.04, 0.3), (0.24, 0.24, 0.49), parent=root, material=m_wood)
    # Layered roofs
    make_cone("lanna_roof1", 0.28, 0.14, (0.0, 0.24, 0.71), rotation=(0.15, 0, math.pi/4), parent=root, material=m_red, vertices=4)
    make_cone("lanna_roof2", 0.2, 0.1, (0.0, 0.24, 0.83), rotation=(0.15, 0, math.pi/4), parent=root, material=m_gold, vertices=4)
    
    # Decorative Naga Stairs (flanking the front steps)
    make_cube("stair_step1", (0.28, 0.12, 0.06), (0.0, 0.45, 0.03), parent=root, material=m_cream)
    make_cube("stair_step2", (0.28, 0.12, 0.06), (0.0, 0.38, 0.09), parent=root, material=m_cream)
    # Naga banisters (zigzag low-poly snake shapes)
    make_cube("naga_left_body", (0.06, 0.24, 0.12), (-0.16, 0.38, 0.14), rotation=(-0.4, 0, 0), parent=root, material=m_gold)
    make_cube("naga_right_body", (0.06, 0.24, 0.12), (0.16, 0.38, 0.14), rotation=(-0.4, 0, 0), parent=root, material=m_gold)
    # Naga heads
    make_cylinder("naga_left_head", 0.04, 0.08, (-0.16, 0.52, 0.08), rotation=(math.pi/2, 0, 0), parent=root, material=m_red)
    make_cylinder("naga_right_head", 0.04, 0.08, (0.16, 0.52, 0.08), rotation=(math.pi/2, 0, 0), parent=root, material=m_red)
    
    # Golden parasols next to the base
    parasol_coords = [(-0.35, -0.35), (0.35, -0.35)]
    for idx, c in enumerate(parasol_coords):
        make_cylinder(f"parasol_pole_{idx}", 0.01, 0.5, (c[0], c[1], 0.25), parent=root, material=m_wood)
        make_cone(f"parasol_top_{idx}", 0.14, 0.08, (c[0], c[1], 0.54), parent=root, material=m_gold)
        make_cylinder(f"parasol_fringe_{idx}", 0.142, 0.02, (c[0], c[1], 0.5), parent=root, material=m_cream)
        
    export_glb(root, os.path.join(dir_path, "doi_suthep.glb"))

def create_tha_phae_gate(dir_path):
    root = make_root("tha_phae_gate")
    m_red = get_material("mat_roof_red", PALETTE["WarmOrange"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    m_wood = get_material("mat_lanna_wood", PALETTE["SoftBrown"])
    m_gold = get_material("mat_gold", PALETTE["LanternGold"])
    
    # Left Brick Wall
    make_cube("wall_l", (0.32, 0.16, 0.72), (-0.45, 0.0, 0.36), parent=root, material=m_red)
    make_cube("wall_l_cap", (0.34, 0.18, 0.06), (-0.45, 0.0, 0.75), parent=root, material=m_cream)
    # Wall crenellations
    make_cube("cren_l1", (0.08, 0.14, 0.1), (-0.56, 0.0, 0.83), parent=root, material=m_red)
    make_cube("cren_l2", (0.08, 0.14, 0.1), (-0.34, 0.0, 0.83), parent=root, material=m_red)
    
    # Right Brick Wall
    make_cube("wall_r", (0.32, 0.16, 0.72), (0.45, 0.0, 0.36), parent=root, material=m_red)
    make_cube("wall_r_cap", (0.34, 0.18, 0.06), (0.45, 0.0, 0.75), parent=root, material=m_cream)
    # Wall crenellations
    make_cube("cren_r1", (0.08, 0.14, 0.1), (0.34, 0.0, 0.83), parent=root, material=m_red)
    make_cube("cren_r2", (0.08, 0.14, 0.1), (0.56, 0.0, 0.83), parent=root, material=m_red)
    
    # Central Gateway Arch
    make_cube("arch_beam", (0.6, 0.16, 0.15), (0.0, 0.0, 0.655), parent=root, material=m_red)
    make_cube("arch_cap", (0.64, 0.18, 0.06), (0.0, 0.0, 0.76), parent=root, material=m_cream)
    
    # Tiled Lanna roof above center arch
    make_cone("roof_center", 0.35, 0.22, (0.0, 0.0, 0.9), rotation=(0, 0, math.pi/4), parent=root, material=m_red, vertices=4)
    make_cone("roof_spire", 0.05, 0.15, (0.0, 0.0, 1.085), parent=root, material=m_gold)
    
    # Open wooden gate doors
    make_cube("gate_door_l", (0.02, 0.22, 0.5), (-0.16, 0.14, 0.25), rotation=(0, 0, 0.6), parent=root, material=m_wood)
    make_cube("gate_door_r", (0.02, 0.22, 0.5), (0.16, 0.14, 0.25), rotation=(0, 0, -0.6), parent=root, material=m_wood)
    
    # Cute yellow and red banners hanging on the walls
    make_cube("banner_l", (0.08, 0.02, 0.38), (-0.45, -0.09, 0.45), parent=root, material=m_gold)
    make_cube("banner_r", (0.08, 0.02, 0.38), (0.45, -0.09, 0.45), parent=root, material=m_red)
    
    export_glb(root, os.path.join(dir_path, "tha_phae_gate.glb"))

def create_yi_peng_lantern(dir_path):
    root = make_root("yi_peng_lantern")
    m_gold = get_material("mat_gold", PALETTE["LanternGold"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    m_orange = get_material("mat_roof_red", PALETTE["WarmOrange"])
    
    # Low poly spherical/cylindrical lantern shape
    make_cylinder("lantern_body", 0.16, 0.32, (0.0, 0.0, 0.5), parent=root, material=m_cream, vertices=8)
    make_cylinder("lantern_rim_top", 0.18, 0.04, (0.0, 0.0, 0.66), parent=root, material=m_orange, vertices=8)
    make_cylinder("lantern_rim_bot", 0.18, 0.04, (0.0, 0.0, 0.34), parent=root, material=m_orange, vertices=8)
    
    # Hanging tassels
    make_cube("tassel_c", (0.08, 0.02, 0.18), (0.0, 0.0, 0.23), parent=root, material=m_gold)
    make_cube("tassel_l", (0.03, 0.01, 0.14), (-0.05, 0.0, 0.21), rotation=(0, 0.1, 0), parent=root, material=m_orange)
    make_cube("tassel_r", (0.03, 0.01, 0.14), (0.05, 0.0, 0.21), rotation=(0, -0.1, 0), parent=root, material=m_orange)
    
    export_glb(root, os.path.join(dir_path, "yi_peng_lantern.glb"))

def create_coffee_cart(dir_path):
    root = make_root("coffee_cart")
    m_brown = get_material("mat_lanna_wood", PALETTE["SoftBrown"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    m_orange = get_material("mat_roof_red", PALETTE["WarmOrange"])
    m_dark = get_material("mat_dark", (0.2, 0.2, 0.22, 1.0))
    
    # Cart body counter
    make_cube("counter", (0.45, 0.7, 0.35), (0.0, 0.0, 0.225), parent=root, material=m_cream)
    make_cube("wooden_table", (0.5, 0.75, 0.04), (0.0, 0.0, 0.42), parent=root, material=m_brown)
    
    # 2 Wheels
    make_cylinder("wheel_l", 0.14, 0.03, (-0.24, 0.0, 0.14), rotation=(0, math.pi/2, 0), parent=root, material=m_dark)
    make_cylinder("wheel_r", 0.14, 0.03, (0.24, 0.0, 0.14), rotation=(0, math.pi/2, 0), parent=root, material=m_dark)
    
    # Cart canopy on poles
    make_cylinder("pole_fl", 0.01, 0.4, (-0.2, 0.25, 0.6), parent=root, material=m_brown)
    make_cylinder("pole_fr", 0.01, 0.4, (0.2, 0.25, 0.6), parent=root, material=m_brown)
    make_cylinder("pole_rl", 0.01, 0.4, (-0.2, -0.25, 0.6), parent=root, material=m_brown)
    make_cylinder("pole_rr", 0.01, 0.4, (0.2, -0.25, 0.6), parent=root, material=m_brown)
    make_cube("canopy", (0.48, 0.78, 0.05), (0.0, 0.0, 0.8), parent=root, material=m_orange)
    
    # Coffee maker cylinder on table
    make_cylinder("coffee_pot", 0.06, 0.12, (-0.1, 0.1, 0.5), parent=root, material=m_dark)
    make_cylinder("pot_lid", 0.062, 0.02, (-0.1, 0.1, 0.57), parent=root, material=m_orange)
    
    export_glb(root, os.path.join(dir_path, "coffee_cart.glb"))

def create_coffee_village(dir_path):
    root = make_root("coffee_village")
    m_wood = get_material("mat_lanna_wood", PALETTE["SoftBrown"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    m_green = get_material("mat_tropical_green", PALETTE["PineGreen"])
    m_red = get_material("mat_roof_red", PALETTE["WarmOrange"])
    m_white = get_material("mat_white", PALETTE["PureWhite"])
    m_dark = get_material("mat_dark", (0.15, 0.15, 0.17, 1.0))
    
    # Ground Base
    make_cube("base", (0.75, 0.75, 0.06), (0.0, 0.0, 0.03), parent=root, material=m_green)
    
    # Wooden Hut Cabin
    make_cube("hut_body", (0.48, 0.48, 0.38), (0.0, 0.0, 0.22), parent=root, material=m_wood)
    # Sloped roof (curved Lanna look)
    make_cone("hut_roof", 0.38, 0.28, (0.0, 0.0, 0.54), rotation=(0, 0, math.pi/4), parent=root, material=m_red, vertices=4)
    # Chimney/top accent
    make_cylinder("chimney", 0.03, 0.16, (0.12, -0.12, 0.62), parent=root, material=m_cream)
    
    # Door and Window
    make_cube("hut_door", (0.02, 0.12, 0.2), (0.0, -0.25, 0.14), parent=root, material=m_cream)
    make_sphere("hut_window", 0.08, (0.0, 0.24, 0.25), parent=root, material=m_white)
    
    # Coffee Cup Sign
    make_cylinder("sign_pole", 0.016, 0.45, (-0.26, -0.26, 0.225), parent=root, material=m_wood)
    make_cube("sign_board", (0.18, 0.04, 0.12), (-0.26, -0.26, 0.45), parent=root, material=m_wood)
    # Coffee cup model
    make_cylinder("cup", 0.045, 0.07, (-0.26, -0.26, 0.54), parent=root, material=m_white)
    make_cylinder("cup_handle", 0.02, 0.015, (-0.22, -0.26, 0.54), rotation=(math.pi/2, 0, 0), parent=root, material=m_white)
    make_cylinder("coffee_fill", 0.04, 0.01, (-0.26, -0.26, 0.575), parent=root, material=m_dark)
    
    # Small flower pots
    make_cylinder("pot1", 0.04, 0.08, (0.24, -0.24, 0.1), parent=root, material=m_red)
    make_sphere("flower1", 0.05, (0.24, -0.24, 0.15), parent=root, material=m_cream)
    
    make_cylinder("pot2", 0.04, 0.08, (-0.24, 0.24, 0.1), parent=root, material=m_red)
    make_sphere("flower2", 0.05, (-0.24, 0.24, 0.15), parent=root, material=m_cream)
    
    export_glb(root, os.path.join(dir_path, "coffee_village.glb"))

def create_elephant_sanctuary(dir_path):
    root = make_root("elephant_sanctuary")
    m_wood = get_material("mat_lanna_wood", PALETTE["SoftBrown"])
    m_green = get_material("mat_tropical_green", PALETTE["MountainGreen"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    m_grey = get_material("mat_elephant_grey", (0.5, 0.52, 0.56, 1.0))
    m_white = get_material("mat_white", PALETTE["PureWhite"])
    
    # Ground Base
    make_cube("base", (0.75, 0.75, 0.06), (0.0, 0.0, 0.03), parent=root, material=m_green)
    
    # Stylized Cute Elephant Statue
    make_cube("ele_body", (0.2, 0.32, 0.2), (0.0, 0.0, 0.25), parent=root, material=m_grey)
    # Legs
    make_cylinder("ele_leg_fl", 0.04, 0.16, (-0.08, 0.1, 0.08), parent=root, material=m_grey)
    make_cylinder("ele_leg_fr", 0.04, 0.16, (0.08, 0.1, 0.08), parent=root, material=m_grey)
    make_cylinder("ele_leg_bl", 0.04, 0.16, (-0.08, -0.1, 0.08), parent=root, material=m_grey)
    make_cylinder("ele_leg_br", 0.04, 0.16, (0.08, -0.1, 0.08), parent=root, material=m_grey)
    # Head and Ears
    make_sphere("ele_head", 0.1, (0.0, 0.16, 0.37), parent=root, material=m_grey)
    make_cylinder("ele_ear_l", 0.08, 0.02, (-0.1, 0.14, 0.38), rotation=(0, math.pi/2, 0), parent=root, material=m_grey)
    make_cylinder("ele_ear_r", 0.08, 0.02, (0.1, 0.14, 0.38), rotation=(0, math.pi/2, 0), parent=root, material=m_grey)
    # Trunk and Tusks
    make_cylinder("ele_trunk1", 0.025, 0.08, (0.0, 0.25, 0.32), rotation=(0.4, 0, 0), parent=root, material=m_grey)
    make_cylinder("ele_trunk2", 0.02, 0.08, (0.0, 0.28, 0.28), rotation=(1.1, 0, 0), parent=root, material=m_grey)
    make_cone("ele_tusk_l", 0.01, 0.06, (-0.03, 0.22, 0.32), rotation=(-0.4, 0, 0), parent=root, material=m_white)
    make_cone("ele_tusk_r", 0.01, 0.06, (0.03, 0.22, 0.32), rotation=(-0.4, 0, 0), parent=root, material=m_white)
    
    # Wooden Fence
    # Front fence posts
    make_cylinder("fence_p1", 0.018, 0.26, (-0.32, -0.32, 0.13), parent=root, material=m_wood)
    make_cylinder("fence_p2", 0.018, 0.26, (0.32, -0.32, 0.13), parent=root, material=m_wood)
    make_cylinder("fence_p3", 0.018, 0.26, (-0.32, 0.32, 0.13), parent=root, material=m_wood)
    make_cylinder("fence_p4", 0.018, 0.26, (0.32, 0.32, 0.13), parent=root, material=m_wood)
    # Rails
    make_cube("fence_rail_b", (0.64, 0.02, 0.04), (0.0, -0.32, 0.18), parent=root, material=m_wood)
    make_cube("fence_rail_l", (0.02, 0.64, 0.04), (-0.32, 0.0, 0.18), parent=root, material=m_wood)
    
    # Small tropical banana tree
    make_cylinder("tree_trunk", 0.025, 0.36, (0.24, 0.24, 0.18), parent=root, material=m_wood)
    make_sphere("tree_leaf1", 0.1, (0.24, 0.24, 0.36), parent=root, material=m_green)
    make_sphere("tree_leaf2", 0.08, (0.2, 0.2, 0.42), parent=root, material=m_green)
    
    export_glb(root, os.path.join(dir_path, "elephant_sanctuary.glb"))

def create_mountain_resort(dir_path):
    root = make_root("mountain_resort")
    m_green = get_material("mat_tropical_green", PALETTE["MountainGreen"])
    m_brown = get_material("mat_lanna_wood", PALETTE["SoftBrown"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    
    # Resort stone base deck
    make_cube("deck", (0.75, 0.75, 0.08), (0.0, 0.0, 0.04), parent=root, material=m_cream)
    
    # Main house cabin
    make_cube("cabin", (0.55, 0.55, 0.45), (0.0, 0.0, 0.305), parent=root, material=m_brown)
    
    # Triangular A-frame sloped roof
    make_cone("roof", 0.46, 0.45, (0.0, 0.0, 0.75), rotation=(0, 0, math.pi/4), parent=root, material=m_green, vertices=4)
    
    # Door and chimney
    make_cube("door", (0.02, 0.14, 0.25), (0.0, 0.27, 0.175), parent=root, material=m_cream)
    make_cylinder("chimney", 0.03, 0.25, (0.16, -0.16, 0.75), parent=root, material=m_cream)
    
    export_glb(root, os.path.join(dir_path, "mountain_resort.glb"))

def create_elephant_sign(dir_path):
    root = make_root("elephant_sign")
    m_brown = get_material("mat_lanna_wood", PALETTE["SoftBrown"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    m_dark = get_material("mat_dark", (0.45, 0.45, 0.48, 1.0))
    
    # Wooden post
    make_cylinder("post", 0.025, 0.7, (0.0, 0.0, 0.35), parent=root, material=m_brown)
    # Signboard
    make_cube("board", (0.5, 0.06, 0.28), (0.0, 0.0, 0.65), parent=root, material=m_brown)
    # Border
    make_cube("board_face", (0.44, 0.07, 0.22), (0.0, 0.0, 0.65), parent=root, material=m_cream)
    
    # Small low-poly elephant emblem detail
    make_cube("emblem_head", (0.1, 0.08, 0.08), (0.0, 0.04, 0.65), parent=root, material=m_dark)
    make_cube("emblem_ear_l", (0.05, 0.08, 0.08), (-0.06, 0.04, 0.67), parent=root, material=m_dark)
    make_cube("emblem_ear_r", (0.05, 0.08, 0.08), (0.06, 0.04, 0.67), parent=root, material=m_dark)
    
    export_glb(root, os.path.join(dir_path, "elephant_sign.glb"))

def create_lanna_craft_stall(dir_path):
    root = make_root("lanna_craft_stall")
    m_brown = get_material("mat_lanna_wood", PALETTE["SoftBrown"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    m_orange = get_material("mat_roof_red", PALETTE["WarmOrange"])
    
    # Wooden desk/table
    make_cube("table", (0.5, 0.8, 0.3), (0.0, 0.0, 0.15), parent=root, material=m_brown)
    
    # Bamboo roof frame columns
    make_cylinder("pole_l", 0.015, 0.5, (-0.22, 0.35, 0.4), parent=root, material=m_brown)
    make_cylinder("pole_r", 0.015, 0.5, (0.22, 0.35, 0.4), parent=root, material=m_brown)
    
    # Slanted thatched straw roof
    make_cube("roof", (0.55, 0.9, 0.06), (0.0, 0.0, 0.65), rotation=(0.12, 0, 0), parent=root, material=m_cream)
    
    # Crafts on table
    make_cube("basket1", (0.12, 0.12, 0.1), (-0.12, 0.1, 0.35), parent=root, material=m_orange)
    make_cube("basket2", (0.1, 0.1, 0.08), (0.12, -0.1, 0.34), parent=root, material=m_cream)
    
    export_glb(root, os.path.join(dir_path, "lanna_craft_stall.glb"))

def create_flower_garden(dir_path):
    root = make_root("flower_garden")
    m_green = get_material("mat_tropical_green", PALETTE["MountainGreen"])
    m_orange = get_material("mat_roof_red", PALETTE["WarmOrange"])
    m_gold = get_material("mat_gold", PALETTE["LanternGold"])
    
    # Soil/grass base
    make_cube("soil_base", (0.75, 0.75, 0.08), (0.0, 0.0, 0.04), parent=root, material=m_green)
    
    # Tiny flowers (cylinders with spheres)
    flower_positions = [
        (-0.2, -0.2, 0.08),
        (0.2, -0.1, 0.08),
        (-0.1, 0.2, 0.08),
        (0.15, 0.22, 0.08),
        (0.0, 0.0, 0.08)
    ]
    for idx, pos in enumerate(flower_positions):
        color = m_orange if idx % 2 == 0 else m_gold
        make_cylinder(f"stem_{idx}", 0.008, 0.12, (pos[0], pos[1], pos[2]+0.06), parent=root, material=m_green)
        make_sphere(f"petal_{idx}", 0.04, (pos[0], pos[1], pos[2]+0.13), parent=root, material=color)
        
    export_glb(root, os.path.join(dir_path, "flower_garden.glb"))

def create_northern_food_stall(dir_path):
    root = make_root("northern_food_stall")
    m_brown = get_material("mat_lanna_wood", PALETTE["SoftBrown"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    m_orange = get_material("mat_roof_red", PALETTE["WarmOrange"])
    m_dark = get_material("mat_dark", (0.22, 0.22, 0.24, 1.0))
    
    # Stall base counter
    make_cube("counter", (0.5, 0.75, 0.38), (0.0, 0.0, 0.19), parent=root, material=m_brown)
    
    # Striped awning roof canopy
    make_cylinder("p_l", 0.012, 0.5, (-0.22, -0.32, 0.55), parent=root, material=m_brown)
    make_cylinder("p_r", 0.012, 0.5, (0.22, -0.32, 0.55), parent=root, material=m_brown)
    make_cube("awning", (0.54, 0.8, 0.04), (0.0, 0.0, 0.8), parent=root, material=m_orange)
    
    # Large metal pot
    make_cylinder("soup_pot", 0.1, 0.14, (-0.1, 0.1, 0.45), parent=root, material=m_dark)
    make_sphere("pot_handle", 0.02, (-0.1, 0.1, 0.53), parent=root, material=m_cream)
    
    # Stool in front
    make_cylinder("stool", 0.09, 0.2, (0.2, 0.3, 0.1), parent=root, material=m_brown)
    
    export_glb(root, os.path.join(dir_path, "food_stall.glb"))

def create_pine_tree(dir_path):
    root = make_root("pine_tree")
    m_brown = get_material("mat_lanna_wood", PALETTE["SoftBrown"])
    m_pine = get_material("mat_tropical_green", PALETTE["PineGreen"])
    
    # Trunk cylinder
    make_cylinder("trunk", 0.04, 0.35, (0.0, 0.0, 0.175), parent=root, material=m_brown)
    
    # Stacked cones
    make_cone("cone1", 0.28, 0.28, (0.0, 0.0, 0.4), parent=root, material=m_pine)
    make_cone("cone2", 0.22, 0.24, (0.0, 0.0, 0.58), parent=root, material=m_pine)
    make_cone("cone3", 0.16, 0.2, (0.0, 0.0, 0.75), parent=root, material=m_pine)
    
    export_glb(root, os.path.join(dir_path, "pine_tree.glb"))

def create_mountain_bg(dir_path):
    root = make_root("mountain_bg")
    m_green1 = get_material("mat_tropical_green", PALETTE["MountainGreen"])
    m_green2 = get_material("mat_green2", (0.1, 0.38, 0.22, 1.0))
    m_green3 = get_material("mat_green3", (0.08, 0.32, 0.18, 1.0))
    
    # Three layered flat diorama peaks
    make_cone("peak_back", 0.45, 0.8, (-0.15, -0.15, 0.4), rotation=(0, 0, 0), parent=root, material=m_green3, vertices=4)
    make_cone("peak_mid", 0.35, 0.65, (0.15, -0.05, 0.325), rotation=(0, 0, math.pi/4), parent=root, material=m_green2, vertices=4)
    make_cone("peak_front", 0.28, 0.5, (-0.05, 0.05, 0.25), rotation=(0, 0, 0), parent=root, material=m_green1, vertices=4)
    
    export_glb(root, os.path.join(dir_path, "mountain_bg.glb"))


# --- PHUKET MODELS ---

def create_longtail_boat(dir_path):
    root = make_root("longtail_boat")
    m_wood = get_material("mat_lanna_wood", PALETTE["SoftBrown"])
    m_blue = get_material("mat_ocean_blue", PALETTE["OceanBlue"])
    m_pink = get_material("mat_roof_red", PALETTE["SunsetPink"])
    m_gold = get_material("mat_gold", PALETTE["LanternGold"])
    m_dark = get_material("mat_dark", (0.2, 0.2, 0.22, 1.0))
    m_white = get_material("mat_white", PALETTE["PureWhite"])
    
    # Curved hull: central deck and tapered bow/stern wedges
    make_cube("hull_mid", (0.24, 0.5, 0.14), (0.0, 0.0, 0.07), parent=root, material=m_wood)
    # Bow (tapered wedge rising up)
    make_cone("hull_bow", 0.12, 0.32, (0.0, 0.36, 0.15), rotation=(math.pi/2.4, 0, 0), parent=root, material=m_wood)
    # Stern (back wedge)
    make_cone("hull_stern", 0.12, 0.24, (0.0, -0.32, 0.1), rotation=(-math.pi/2, 0, 0), parent=root, material=m_wood)
    
    # Inside seating bench planks
    make_cube("bench1", (0.22, 0.08, 0.02), (0.0, 0.12, 0.11), parent=root, material=m_white)
    make_cube("bench2", (0.22, 0.08, 0.02), (0.0, -0.12, 0.11), parent=root, material=m_white)
    
    # Bow ribbons (multi-colored bands wrapped around bow tip)
    make_cylinder("ribbon_red", 0.08, 0.04, (0.0, 0.44, 0.24), rotation=(math.pi/2.4, 0, 0), parent=root, material=m_pink)
    make_cylinder("ribbon_yellow", 0.08, 0.04, (0.0, 0.45, 0.28), rotation=(math.pi/2.4, 0, 0), parent=root, material=m_gold)
    make_cylinder("ribbon_blue", 0.08, 0.04, (0.0, 0.46, 0.32), rotation=(math.pi/2.4, 0, 0), parent=root, material=m_blue)
    
    # Tail motor and propeller assembly
    make_cube("motor_box", (0.08, 0.08, 0.1), (0.0, -0.38, 0.22), parent=root, material=m_dark)
    make_cylinder("motor_stick", 0.012, 0.5, (0.0, -0.58, 0.12), rotation=(-0.24, 0, 0), parent=root, material=m_dark)
    make_cylinder("propeller_blade", 0.05, 0.015, (0.0, -0.78, -0.01), rotation=(math.pi/2, 0, 0), parent=root, material=m_dark)
    
    export_glb(root, os.path.join(dir_path, "longtail_boat.glb"))

def create_beach_umbrella(dir_path):
    root = make_root("beach_umbrella")
    m_pink = get_material("mat_roof_red", PALETTE["SunsetPink"])
    m_white = get_material("mat_white", PALETTE["PureWhite"])
    m_brown = get_material("mat_lanna_wood", PALETTE["SoftBrown"])
    
    # Slanted umbrella pole
    make_cylinder("pole", 0.016, 0.75, (0.06, 0.0, 0.35), rotation=(0.12, 0, 0), parent=root, material=m_brown)
    
    # Striped cone canopy
    make_cone("canopy_p", 0.38, 0.15, (0.1, 0.0, 0.72), rotation=(0.12, 0, 0), parent=root, material=m_pink, vertices=12)
    # Alternating white segments
    make_cone("canopy_w", 0.37, 0.14, (0.1, 0.0, 0.725), rotation=(0.12, 0, math.pi/6), parent=root, material=m_white, vertices=12)
    
    export_glb(root, os.path.join(dir_path, "beach_umbrella.glb"))

def create_coconut_shop(dir_path):
    root = make_root("coconut_shop")
    m_brown = get_material("mat_lanna_wood", PALETTE["SoftBrown"])
    m_green = get_material("mat_tropical_green", PALETTE["CoconutGreen"])
    m_sand = get_material("mat_sandstone", PALETTE["BeachSand"])
    
    # Wooden desk/cart
    make_cube("counter", (0.45, 0.7, 0.35), (0.0, 0.0, 0.175), parent=root, material=m_brown)
    make_cube("signboard", (0.42, 0.02, 0.16), (0.0, -0.36, 0.28), parent=root, material=m_sand)
    
    # Tiny green coconuts stacked on counter
    make_sphere("coco1", 0.045, (-0.08, 0.12, 0.395), parent=root, material=m_green)
    make_sphere("coco2", 0.045, (0.08, 0.12, 0.395), parent=root, material=m_green)
    make_sphere("coco3", 0.04, (0.0, 0.1, 0.44), parent=root, material=m_green)
    
    export_glb(root, os.path.join(dir_path, "coconut_shop.glb"))

def create_phuket_old_town(dir_path):
    root = make_root("phuket_old_town")
    m_pink = get_material("mat_roof_red", PALETTE["SunsetPink"])
    m_white = get_material("mat_white", PALETTE["PureWhite"])
    m_sand = get_material("mat_sandstone", PALETTE["BeachSand"])
    m_dark = get_material("mat_dark", (0.2, 0.2, 0.22, 1.0))
    
    # Main Sino-Portuguese block structure
    make_cube("building", (0.5, 0.55, 0.8), (0.0, 0.0, 0.4), parent=root, material=m_pink)
    
    # Terracotta tiles sloped roof
    make_cube("roof_l", (0.32, 0.62, 0.06), (-0.14, 0.0, 0.86), rotation=(0, 0.4, 0), parent=root, material=m_sand)
    make_cube("roof_r", (0.32, 0.62, 0.06), (0.14, 0.0, 0.86), rotation=(0, -0.4, 0), parent=root, material=m_sand)
    
    # Ground arched door indentation
    make_cube("door_frame", (0.24, 0.04, 0.32), (0.0, 0.26, 0.16), parent=root, material=m_white)
    make_cube("door_panel", (0.2, 0.02, 0.28), (0.0, 0.27, 0.14), parent=root, material=m_dark)
    
    # Upper window slots
    make_cube("win_l", (0.08, 0.04, 0.16), (-0.14, 0.26, 0.52), parent=root, material=m_white)
    make_cube("win_r", (0.08, 0.04, 0.16), (0.14, 0.26, 0.52), parent=root, material=m_white)
    
    export_glb(root, os.path.join(dir_path, "phuket_old_town.glb"))

def create_big_buddha(dir_path):
    root = make_root("big_buddha")
    m_white = get_material("mat_white", PALETTE["PureWhite"])
    m_gold = get_material("mat_gold", PALETTE["LanternGold"])
    m_pink = get_material("mat_roof_red", PALETTE["SunsetPink"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    
    # Double-tiered lotus platform base
    make_cylinder("lotus_base1", 0.45, 0.12, (0.0, 0.0, 0.06), parent=root, material=m_cream, vertices=12)
    make_cylinder("lotus_base2", 0.38, 0.12, (0.0, 0.0, 0.18), parent=root, material=m_pink, vertices=12)
    
    # 12 Petals around base
    for i in range(12):
        angle = i * (2 * math.pi / 12)
        px = math.cos(angle) * 0.4
        py = math.sin(angle) * 0.4
        make_cone(f"petal_{i}", 0.06, 0.1, (px, py, 0.18), rotation=(0.4, 0, angle + math.pi/2), parent=root, material=m_white, vertices=4)
        
    # Seated Buddha - Folded legs base
    make_cylinder("legs_folded", 0.24, 0.12, (0.0, 0.0, 0.3), parent=root, material=m_white, vertices=8)
    make_cube("lap_overlay", (0.34, 0.16, 0.12), (0.0, 0.0, 0.31), parent=root, material=m_white)
    
    # Torso
    make_cube("torso", (0.18, 0.14, 0.28), (0.0, 0.0, 0.46), parent=root, material=m_white)
    
    # Head & serene face
    make_sphere("head", 0.09, (0.0, 0.0, 0.655), parent=root, material=m_white)
    # Ushnisha and Flame Spire
    make_sphere("ushnisha", 0.03, (0.0, 0.0, 0.745), parent=root, material=m_white)
    make_cone("flame_spire", 0.02, 0.08, (0.0, 0.0, 0.795), parent=root, material=m_gold)
    
    export_glb(root, os.path.join(dir_path, "big_buddha.glb"))

def create_promthep_cape(dir_path):
    root = make_root("promthep_cape")
    m_green = get_material("mat_tropical_green", PALETTE["CoconutGreen"])
    m_white = get_material("mat_white", PALETTE["PureWhite"])
    m_gold = get_material("mat_gold", PALETTE["LanternGold"])
    m_wood = get_material("mat_lanna_wood", PALETTE["SoftBrown"])
    m_dark = get_material("mat_dark", (0.32, 0.32, 0.34, 1.0))
    
    # Rocky Cliff Hill
    make_cube("rock1", (0.55, 0.55, 0.22), (0.0, 0.0, 0.11), parent=root, material=m_dark)
    make_cube("rock2", (0.42, 0.42, 0.18), (-0.15, 0.12, 0.22), rotation=(0.1, 0.2, -0.3), parent=root, material=m_dark)
    make_cube("soil_top", (0.45, 0.45, 0.06), (0.0, 0.0, 0.23), parent=root, material=m_green)
    
    # Viewpoint Platform Balcony
    make_cube("deck", (0.32, 0.32, 0.04), (0.0, 0.0, 0.27), parent=root, material=m_white)
    # Railing posts
    make_cylinder("rail_l", 0.01, 0.15, (-0.15, -0.15, 0.34), parent=root, material=m_white)
    make_cylinder("rail_r", 0.01, 0.15, (0.15, -0.15, 0.34), parent=root, material=m_white)
    make_cube("rail_top", (0.32, 0.02, 0.02), (0.0, -0.15, 0.41), parent=root, material=m_white)
    
    # Golden Spire Beacon on Cliff
    make_cylinder("beacon_base", 0.08, 0.16, (-0.18, 0.18, 0.38), parent=root, material=m_white)
    make_cone("beacon_spire", 0.06, 0.14, (-0.18, 0.18, 0.53), parent=root, material=m_gold)
    
    # Palm tree cluster next to platform
    # Tall Palm
    make_cylinder("palm_tr1", 0.02, 0.4, (0.2, 0.2, 0.38), rotation=(0.12, -0.12, 0), parent=root, material=m_wood)
    make_cone("palm_leaf1", 0.18, 0.06, (0.24, 0.16, 0.57), parent=root, material=m_green, vertices=5)
    # Short Palm
    make_cylinder("palm_tr2", 0.018, 0.28, (0.22, 0.02, 0.32), rotation=(0.22, -0.22, 0), parent=root, material=m_wood)
    make_cone("palm_leaf2", 0.15, 0.05, (0.27, -0.04, 0.45), parent=root, material=m_green, vertices=5)
    
    export_glb(root, os.path.join(dir_path, "promthep_cape.glb"))

def create_beach_resort(dir_path):
    root = make_root("beach_resort")
    m_wood = get_material("mat_lanna_wood", PALETTE["SoftBrown"])
    m_blue = get_material("mat_ocean_blue", PALETTE["OceanBlue"])
    m_sand = get_material("mat_sandstone", PALETTE["BeachSand"])
    m_green = get_material("mat_tropical_green", PALETTE["CoconutGreen"])
    m_pink = get_material("mat_roof_red", PALETTE["SunsetPink"])
    m_white = get_material("mat_white", PALETTE["PureWhite"])
    
    # Ground Base
    make_cube("base", (0.75, 0.75, 0.06), (0.0, 0.0, 0.03), parent=root, material=m_sand)
    
    # Stilts for bungalow
    make_cylinder("stilt1", 0.015, 0.16, (-0.2, -0.2, 0.11), parent=root, material=m_wood)
    make_cylinder("stilt2", 0.015, 0.16, (0.2, -0.2, 0.11), parent=root, material=m_wood)
    make_cylinder("stilt3", 0.015, 0.16, (-0.2, 0.2, 0.11), parent=root, material=m_wood)
    make_cylinder("stilt4", 0.015, 0.16, (0.2, 0.2, 0.11), parent=root, material=m_wood)
    make_cube("deck", (0.54, 0.54, 0.04), (0.0, 0.0, 0.21), parent=root, material=m_wood)
    
    # Bungalow hut structure
    make_cube("walls", (0.42, 0.42, 0.32), (0.0, 0.0, 0.37), parent=root, material=m_blue)
    make_cone("straw_roof", 0.35, 0.25, (0.0, 0.0, 0.635), rotation=(0, 0, math.pi/4), parent=root, material=m_sand, vertices=4)
    
    # Door & windows
    make_cube("door", (0.02, 0.12, 0.2), (-0.1, -0.21, 0.33), parent=root, material=m_white)
    make_cube("win", (0.1, 0.02, 0.12), (0.1, -0.21, 0.37), parent=root, material=m_white)
    
    # Beach Umbrella
    make_cylinder("umb_pole", 0.012, 0.45, (0.26, -0.26, 0.225), rotation=(0.1, 0, 0), parent=root, material=m_wood)
    make_cone("umb_top", 0.2, 0.08, (0.28, -0.26, 0.44), rotation=(0.1, 0, 0), parent=root, material=m_pink, vertices=8)
    
    # Two Surfboards leaning against bungalow
    make_cube("surf1", (0.08, 0.015, 0.32), (-0.26, -0.16, 0.26), rotation=(0, -0.15, -0.15), parent=root, material=m_pink)
    make_cube("surf2", (0.08, 0.015, 0.32), (-0.24, -0.24, 0.24), rotation=(0, -0.15, 0.15), parent=root, material=m_blue)
    
    export_glb(root, os.path.join(dir_path, "beach_resort.glb"))

def create_pearl_shop(dir_path):
    root = make_root("pearl_shop")
    m_white = get_material("mat_white", PALETTE["PureWhite"])
    m_pink = get_material("mat_roof_red", PALETTE["SunsetPink"])
    m_blue = get_material("mat_ocean_blue", PALETTE["OceanBlue"])
    
    # Pearl shop building
    make_cube("shop_body", (0.5, 0.5, 0.45), (0.0, 0.0, 0.225), parent=root, material=m_pink)
    make_cube("shop_roof", (0.54, 0.54, 0.05), (0.0, 0.0, 0.46), parent=root, material=m_blue)
    
    # Open giant clam display shell
    make_sphere("shell_bot", 0.16, (-0.05, 0.0, 0.56), parent=root, material=m_white)
    make_sphere("shell_top", 0.16, (0.05, 0.0, 0.64), parent=root, material=m_white)
    make_sphere("pearl", 0.065, (0.0, 0.0, 0.575), parent=root, material=m_white)
    
    export_glb(root, os.path.join(dir_path, "pearl_shop.glb"))

def create_seafood_stall(dir_path):
    root = make_root("seafood_stall")
    m_brown = get_material("mat_lanna_wood", PALETTE["SoftBrown"])
    m_blue = get_material("mat_ocean_blue", PALETTE["OceanBlue"])
    m_white = get_material("mat_white", PALETTE["PureWhite"])
    m_dark = get_material("mat_dark", (0.45, 0.45, 0.48, 1.0))
    
    # Stand desk
    make_cube("stand", (0.48, 0.75, 0.35), (0.0, 0.0, 0.175), parent=root, material=m_brown)
    
    # Ice box container
    make_cube("ice_box", (0.4, 0.65, 0.12), (0.0, 0.0, 0.41), parent=root, material=m_white)
    # Ice plane
    make_cube("ice_plane", (0.36, 0.6, 0.02), (0.0, 0.0, 0.46), parent=root, material=m_blue)
    
    # Small fish/shrimp block details on ice
    make_cone("fish1", 0.035, 0.14, (-0.08, 0.1, 0.485), rotation=(0.1, 0.2, 0.5), parent=root, material=m_dark)
    make_cone("fish2", 0.035, 0.14, (0.08, -0.1, 0.485), rotation=(-0.1, -0.2, -0.5), parent=root, material=m_dark)
    
    export_glb(root, os.path.join(dir_path, "seafood_stall.glb"))

def create_palm_tree(dir_path):
    root = make_root("palm_tree")
    m_brown = get_material("mat_lanna_wood", PALETTE["SoftBrown"])
    m_green = get_material("mat_tropical_green", PALETTE["CoconutGreen"])
    
    # Curved trunk (three connected cylinders)
    make_cylinder("trunk1", 0.04, 0.25, (0.0, 0.0, 0.125), parent=root, material=m_brown)
    make_cylinder("trunk2", 0.035, 0.25, (0.04, 0.0, 0.35), rotation=(0, 0.15, 0), parent=root, material=m_brown)
    make_cylinder("trunk3", 0.03, 0.25, (0.1, 0.0, 0.56), rotation=(0, 0.28, 0), parent=root, material=m_brown)
    
    # Star-shaped coconut palm leaf fans
    make_cube("leaf_n", (0.12, 0.45, 0.02), (0.12, 0.22, 0.74), rotation=(0.25, 0, 0), parent=root, material=m_green)
    make_cube("leaf_s", (0.12, 0.45, 0.02), (0.12, -0.22, 0.74), rotation=(-0.25, 0, 0), parent=root, material=m_green)
    make_cube("leaf_e", (0.45, 0.12, 0.02), (0.32, 0.0, 0.74), rotation=(0, 0.25, 0), parent=root, material=m_green)
    make_cube("leaf_w", (0.45, 0.12, 0.02), (-0.08, 0.0, 0.7), rotation=(0, -0.25, 0), parent=root, material=m_green)
    
    export_glb(root, os.path.join(dir_path, "palm_tree.glb"))

def create_coral_rock(dir_path):
    root = make_root("coral_rock")
    m_coral = get_material("mat_roof_red", PALETTE["CoralOrange"])
    m_pink = get_material("mat_candy_pink", PALETTE["SunsetPink"])
    m_blue = get_material("mat_ocean_blue", PALETTE["OceanBlue"])
    
    # Stacked blocky colorful ocean floor coral pieces
    make_sphere("coral_c", 0.22, (0.0, 0.0, 0.16), parent=root, material=m_coral)
    make_sphere("coral_l", 0.14, (-0.16, 0.08, 0.1), parent=root, material=m_pink)
    make_sphere("coral_r", 0.14, (0.16, -0.08, 0.1), parent=root, material=m_blue)
    
    export_glb(root, os.path.join(dir_path, "coral_rock.glb"))

def create_ocean_wave(dir_path):
    root = make_root("ocean_wave")
    m_blue = get_material("mat_ocean_blue", PALETTE["OceanBlue"])
    m_white = get_material("mat_white", PALETTE["PureWhite"])
    
    # Flat layered cartoon scroll waves
    make_cube("wave_back", (0.6, 0.14, 0.35), (0.0, 0.0, 0.175), parent=root, material=m_blue)
    make_cube("wave_front", (0.5, 0.1, 0.25), (0.0, 0.06, 0.125), parent=root, material=m_blue)
    # Wave foam crest
    make_cube("foam_crest", (0.52, 0.08, 0.04), (0.0, 0.07, 0.24), parent=root, material=m_white)
    
    export_glb(root, os.path.join(dir_path, "ocean_wave.glb"))

def create_beach_resort_sign(dir_path):
    root = make_root("beach_resort_sign")
    m_brown = get_material("mat_lanna_wood", PALETTE["SoftBrown"])
    m_sand = get_material("mat_sandstone", PALETTE["BeachSand"])
    m_blue = get_material("mat_ocean_blue", PALETTE["OceanBlue"])
    
    # Twin posts
    make_cylinder("post_l", 0.02, 0.65, (-0.18, 0.0, 0.325), parent=root, material=m_brown)
    make_cylinder("post_r", 0.02, 0.65, (0.18, 0.0, 0.325), parent=root, material=m_brown)
    
    # Board sign
    make_cube("board", (0.52, 0.05, 0.25), (0.0, 0.0, 0.52), parent=root, material=m_brown)
    # Inner face
    make_cube("board_face", (0.46, 0.06, 0.2), (0.0, 0.0, 0.52), parent=root, material=m_sand)
    # Decorative shell badge
    make_sphere("badge_shell", 0.04, (0.0, -0.04, 0.52), parent=root, material=m_blue)
    
    export_glb(root, os.path.join(dir_path, "beach_resort_sign.glb"))


# --- AYUTTHAYA MODELS ---

def create_wat_mahathat(dir_path):
    root = make_root("wat_mahathat")
    m_red = get_material("mat_roof_red", PALETTE["RuinRed"])
    m_sand = get_material("mat_sandstone", PALETTE["SandstoneGold"])
    m_wood = get_material("mat_lanna_wood", PALETTE["WarmBrown"])
    m_green = get_material("mat_tropical_green", PALETTE["LeafGreen"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    
    # Ruined Brick Base Platform
    make_cube("base", (0.75, 0.75, 0.08), (0.0, 0.0, 0.04), parent=root, material=m_red)
    
    # Ruined prang pillar ruins
    make_cube("ruin_wall_l", (0.16, 0.45, 0.42), (-0.24, 0.0, 0.25), parent=root, material=m_red)
    make_cube("ruin_wall_r", (0.16, 0.24, 0.28), (0.24, 0.12, 0.18), parent=root, material=m_red)
    
    # Old Bodhi Tree Trunk & Canopy
    make_cylinder("tree_trunk", 0.06, 0.48, (0.18, -0.15, 0.28), parent=root, material=m_wood)
    make_sphere("tree_leaves1", 0.22, (0.18, -0.15, 0.58), parent=root, material=m_green)
    make_sphere("tree_leaves2", 0.16, (0.06, -0.05, 0.65), parent=root, material=m_green)
    
    # Buddha head inside roots (at base of tree)
    make_sphere("buddha_head", 0.045, (0.14, -0.06, 0.13), parent=root, material=m_sand)
    make_cone("buddha_spire", 0.015, 0.03, (0.14, -0.06, 0.18), parent=root, material=m_sand)
    
    # Wrapping roots (three curved cylinders)
    make_cylinder("root1", 0.015, 0.12, (0.1, -0.05, 0.08), rotation=(0, 0.5, 0.5), parent=root, material=m_wood)
    make_cylinder("root2", 0.015, 0.12, (0.17, -0.03, 0.08), rotation=(0, -0.5, -0.5), parent=root, material=m_wood)
    make_cylinder("root_arch", 0.014, 0.08, (0.14, -0.08, 0.16), rotation=(0, 0, math.pi/2), parent=root, material=m_wood)
    
    export_glb(root, os.path.join(dir_path, "wat_mahathat.glb"))

def create_wat_chaiwatthanaram(dir_path):
    root = make_root("wat_chaiwatthanaram")
    m_sand = get_material("mat_sandstone", PALETTE["SandstoneGold"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    m_red = get_material("mat_roof_red", PALETTE["RuinRed"])
    
    # Sandstone platform
    make_cube("platform1", (0.85, 0.85, 0.1), (0.0, 0.0, 0.05), parent=root, material=m_sand)
    make_cube("platform2", (0.7, 0.7, 0.1), (0.0, 0.0, 0.15), parent=root, material=m_sand)
    
    # Central Tall Prang Stupa
    make_cylinder("prang_base", 0.16, 0.28, (0.0, 0.0, 0.34), parent=root, material=m_sand, vertices=8)
    make_cylinder("prang_mid", 0.13, 0.22, (0.0, 0.0, 0.59), parent=root, material=m_sand, vertices=8)
    # Corn-cob tiered top
    make_cone("prang_top1", 0.13, 0.18, (0.0, 0.0, 0.79), parent=root, material=m_sand, vertices=8)
    make_cone("prang_top2", 0.09, 0.14, (0.0, 0.0, 0.95), parent=root, material=m_sand, vertices=8)
    make_cylinder("prang_spire", 0.012, 0.12, (0.0, 0.0, 1.08), parent=root, material=m_cream)
    
    # Four Symmetrical Corner Chedis
    corners = [(-0.24, -0.24), (0.24, -0.24), (-0.24, 0.24), (0.24, 0.24)]
    for idx, c in enumerate(corners):
        make_cylinder(f"chedi_b_{idx}", 0.06, 0.16, (c[0], c[1], 0.28), parent=root, material=m_sand, vertices=6)
        make_cone(f"chedi_t_{idx}", 0.05, 0.14, (c[0], c[1], 0.43), parent=root, material=m_sand, vertices=6)
        make_cylinder(f"chedi_s_{idx}", 0.01, 0.08, (c[0], c[1], 0.54), parent=root, material=m_cream)
        
    export_glb(root, os.path.join(dir_path, "wat_chaiwatthanaram.glb"))

def create_ancient_palace_wall(dir_path):
    root = make_root("ancient_palace_wall")
    m_red = get_material("mat_roof_red", PALETTE["RuinRed"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    
    # Main wall segment
    make_cube("wall_body", (0.22, 0.8, 0.5), (0.0, 0.0, 0.25), parent=root, material=m_red)
    
    # Crenelations on top
    make_cube("cren1", (0.24, 0.16, 0.12), (0.0, -0.32, 0.56), parent=root, material=m_cream)
    make_cube("cren2", (0.24, 0.16, 0.12), (0.0, 0.0, 0.56), parent=root, material=m_cream)
    make_cube("cren3", (0.24, 0.16, 0.12), (0.0, 0.32, 0.56), parent=root, material=m_cream)
    
    export_glb(root, os.path.join(dir_path, "ancient_palace_wall.glb"))

def create_old_city_gate(dir_path):
    root = make_root("old_city_gate")
    m_sand = get_material("mat_sandstone", PALETTE["SandstoneGold"])
    m_red = get_material("mat_roof_red", PALETTE["RuinRed"])
    
    # Left pillar ruins
    make_cube("pillar_l", (0.18, 0.18, 0.65), (-0.32, 0.0, 0.325), parent=root, material=m_sand)
    # Right pillar ruins
    make_cube("pillar_r", (0.18, 0.18, 0.52), (0.32, 0.0, 0.26), parent=root, material=m_sand)
    
    # Broken top portal arch beam
    make_cube("arch_beam", (0.58, 0.18, 0.15), (-0.12, 0.0, 0.725), parent=root, material=m_red)
    
    export_glb(root, os.path.join(dir_path, "old_city_gate.glb"))

def create_river_boat_pier(dir_path):
    root = make_root("river_boat_pier")
    m_brown = get_material("mat_lanna_wood", PALETTE["WarmBrown"])
    m_blue = get_material("mat_ocean_blue", PALETTE["RiverBlue"])
    
    # River base plane
    make_cube("river_surface", (0.75, 0.75, 0.04), (0.0, 0.0, 0.02), parent=root, material=m_blue)
    
    # 2 Wooden support poles
    make_cylinder("pole_l", 0.025, 0.45, (-0.2, 0.15, 0.225), parent=root, material=m_brown)
    make_cylinder("pole_r", 0.025, 0.45, (0.2, 0.15, 0.225), parent=root, material=m_brown)
    
    # Wooden deck planks
    make_cube("deck", (0.55, 0.45, 0.06), (0.0, -0.05, 0.35), parent=root, material=m_brown)
    
    export_glb(root, os.path.join(dir_path, "river_boat_pier.glb"))

def create_roti_sai_mai_cart(dir_path):
    root = make_root("roti_sai_mai_cart")
    m_green = get_material("mat_tropical_green", PALETTE["LeafGreen"])
    m_red = get_material("mat_roof_red", PALETTE["RuinRed"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    m_brown = get_material("mat_lanna_wood", PALETTE["WarmBrown"])
    m_dark = get_material("mat_dark", (0.18, 0.18, 0.2, 1.0))
    m_pink = get_material("mat_candy_pink", (0.9, 0.5, 0.65, 1.0))
    m_yellow = get_material("mat_gold", PALETTE["LanternGold"])
    
    # Main cart body
    make_cube("cart_body", (0.42, 0.68, 0.32), (0.0, 0.0, 0.22), parent=root, material=m_green)
    make_cube("cart_table", (0.46, 0.72, 0.04), (0.0, 0.0, 0.4), parent=root, material=m_brown)
    
    # Large wheels
    make_cylinder("wheel_l", 0.16, 0.03, (-0.23, 0.0, 0.16), rotation=(0, math.pi/2, 0), parent=root, material=m_dark)
    make_cylinder("wheel_r", 0.16, 0.03, (0.23, 0.0, 0.16), rotation=(0, math.pi/2, 0), parent=root, material=m_dark)
    
    # Canopy with striped fabric cover
    make_cylinder("pole_l", 0.01, 0.42, (-0.18, 0.0, 0.61), parent=root, material=m_brown)
    make_cylinder("pole_r", 0.01, 0.42, (0.18, 0.0, 0.61), parent=root, material=m_brown)
    make_cone("canopy_r", 0.28, 0.1, (0.0, 0.0, 0.84), parent=root, material=m_red, vertices=8)
    make_cone("canopy_w", 0.27, 0.09, (0.0, 0.0, 0.845), rotation=(0, 0, math.pi/8), parent=root, material=m_cream, vertices=8)
    
    # Sai Mai candy rolls on table
    make_cube("box_tray", (0.18, 0.28, 0.06), (-0.08, -0.1, 0.45), parent=root, material=m_cream)
    make_cylinder("roll_pink", 0.02, 0.18, (-0.12, -0.1, 0.49), rotation=(math.pi/2, 0, 0), parent=root, material=m_pink)
    make_cylinder("roll_green", 0.02, 0.18, (-0.08, -0.1, 0.49), rotation=(math.pi/2, 0, 0), parent=root, material=m_green)
    make_cylinder("roll_yellow", 0.02, 0.18, (-0.04, -0.1, 0.49), rotation=(math.pi/2, 0, 0), parent=root, material=m_yellow)
    
    export_glb(root, os.path.join(dir_path, "roti_sai_mai_cart.glb"))

def create_floating_market(dir_path):
    root = make_root("floating_market")
    m_wood = get_material("mat_lanna_wood", PALETTE["WarmBrown"])
    m_blue = get_material("mat_ocean_blue", PALETTE["RiverBlue"])
    m_green = get_material("mat_tropical_green", PALETTE["LeafGreen"])
    m_orange = get_material("mat_roof_red", PALETTE["WarmOrange"])
    m_yellow = get_material("mat_gold", PALETTE["SandstoneGold"])
    
    # River base
    make_cube("water", (0.75, 0.75, 0.04), (0.0, 0.0, 0.02), parent=root, material=m_blue)
    
    # Wooden Rowing Boat
    make_cube("boat_mid", (0.2, 0.54, 0.1), (0.0, 0.0, 0.08), parent=root, material=m_wood)
    # Curved pointed bow and stern
    make_cone("boat_bow", 0.1, 0.22, (0.0, 0.36, 0.13), rotation=(math.pi/2.4, 0, 0), parent=root, material=m_wood)
    make_cone("boat_stern", 0.1, 0.22, (0.0, -0.36, 0.13), rotation=(-math.pi/2.4, 0, 0), parent=root, material=m_wood)
    
    # Fruit baskets (two circular plates)
    make_cylinder("basket1", 0.08, 0.04, (0.0, 0.1, 0.14), parent=root, material=m_wood)
    make_cylinder("basket2", 0.08, 0.04, (0.0, -0.1, 0.14), parent=root, material=m_wood)
    
    # Colorful fruit piles
    # Mangoes
    make_sphere("mango1", 0.025, (-0.02, 0.08, 0.17), parent=root, material=m_yellow)
    make_sphere("mango2", 0.02, (0.02, 0.12, 0.17), parent=root, material=m_yellow)
    make_sphere("mango3", 0.022, (0.0, 0.09, 0.2), parent=root, material=m_yellow)
    
    # Coconuts
    make_sphere("coco1", 0.03, (0.02, -0.08, 0.17), parent=root, material=m_green)
    make_sphere("coco2", 0.028, (-0.02, -0.12, 0.17), parent=root, material=m_green)
    make_sphere("coco3", 0.026, (0.0, -0.09, 0.21), parent=root, material=m_green)
    
    export_glb(root, os.path.join(dir_path, "floating_market.glb"))

def create_thai_dessert_stall(dir_path):
    root = make_root("thai_dessert_stall")
    m_brown = get_material("mat_lanna_wood", PALETTE["WarmBrown"])
    m_gold = get_material("mat_gold", PALETTE["SandstoneGold"])
    m_red = get_material("mat_roof_red", PALETTE["RuinRed"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    
    # Market counter
    make_cube("counter", (0.48, 0.75, 0.36), (0.0, 0.0, 0.18), parent=root, material=m_brown)
    
    # Brass pans with golden dessert balls
    make_cylinder("pan_l", 0.12, 0.02, (-0.1, 0.12, 0.37), parent=root, material=m_gold)
    make_sphere("foy_thong1", 0.035, (-0.1, 0.12, 0.39), parent=root, material=m_gold)
    make_sphere("foy_thong2", 0.025, (-0.08, 0.08, 0.41), parent=root, material=m_gold)
    
    make_cylinder("pan_r", 0.12, 0.02, (0.1, -0.12, 0.37), parent=root, material=m_gold)
    make_sphere("thong_yip", 0.04, (0.1, -0.12, 0.39), parent=root, material=m_red)
    
    export_glb(root, os.path.join(dir_path, "thai_dessert_stall.glb"))

def create_elephant_camp_sign(dir_path):
    root = make_root("elephant_camp_sign")
    m_brown = get_material("mat_lanna_wood", PALETTE["WarmBrown"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    m_red = get_material("mat_roof_red", PALETTE["RuinRed"])
    
    # Two sign poles
    make_cylinder("pole_l", 0.018, 0.62, (-0.16, 0.0, 0.31), parent=root, material=m_brown)
    make_cylinder("pole_r", 0.018, 0.62, (0.16, 0.0, 0.31), parent=root, material=m_brown)
    
    # Board
    make_cube("board", (0.46, 0.05, 0.22), (0.0, 0.0, 0.52), parent=root, material=m_brown)
    # Center face
    make_cube("board_face", (0.4, 0.06, 0.16), (0.0, 0.0, 0.52), parent=root, material=m_cream)
    # Red flag decorations on top corners
    make_cone("flag_l", 0.03, 0.12, (-0.16, 0.0, 0.68), parent=root, material=m_red)
    make_cone("flag_r", 0.03, 0.12, (0.16, 0.0, 0.68), parent=root, material=m_red)
    
    export_glb(root, os.path.join(dir_path, "elephant_camp_sign.glb"))

def create_temple_ruin_blocks(dir_path):
    root = make_root("temple_ruin_blocks")
    m_gold = get_material("mat_gold", PALETTE["SandstoneGold"])
    m_red = get_material("mat_roof_red", PALETTE["RuinRed"])
    
    # Stacked broken blocks
    make_cube("block1", (0.25, 0.25, 0.25), (-0.12, -0.06, 0.125), parent=root, material=m_gold)
    make_cube("block2", (0.2, 0.2, 0.2), (0.12, 0.08, 0.1), rotation=(0.1, 0, 0.6), parent=root, material=m_gold)
    make_cube("block3", (0.16, 0.16, 0.16), (-0.05, 0.08, 0.3), rotation=(-0.2, 0.3, -0.3), parent=root, material=m_red)
    
    export_glb(root, os.path.join(dir_path, "temple_ruin_blocks.glb"))

def create_sandstone_pillar(dir_path):
    root = make_root("sandstone_pillar")
    m_gold = get_material("mat_gold", PALETTE["SandstoneGold"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    
    # Cracked sandstone cylinder
    make_cylinder("pillar_base", 0.14, 0.1, (0.0, 0.0, 0.05), parent=root, material=m_cream, vertices=8)
    make_cylinder("pillar_body", 0.1, 0.68, (0.0, 0.0, 0.44), parent=root, material=m_gold, vertices=8)
    make_cylinder("pillar_top", 0.12, 0.08, (0.0, 0.0, 0.82), parent=root, material=m_cream, vertices=8)
    
    # Chipped detail box
    make_cube("chip", (0.04, 0.04, 0.15), (0.07, 0.05, 0.5), rotation=(0.1, -0.2, 0), parent=root, material=m_cream)
    
    export_glb(root, os.path.join(dir_path, "sandstone_pillar.glb"))

def create_river_bg(dir_path):
    root = make_root("river_bg")
    m_blue = get_material("mat_ocean_blue", PALETTE["RiverBlue"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    
    # Curved river block
    make_cube("water_body", (0.55, 0.85, 0.04), (0.0, 0.0, 0.02), parent=root, material=m_blue)
    # Foam ripples
    make_cube("ripple1", (0.42, 0.05, 0.01), (-0.04, 0.2, 0.045), parent=root, material=m_cream)
    make_cube("ripple2", (0.35, 0.05, 0.01), (0.06, -0.2, 0.045), parent=root, material=m_cream)
    
    export_glb(root, os.path.join(dir_path, "river_bg.glb"))

def create_heritage_museum_sign(dir_path):
    root = make_root("heritage_museum_sign")
    m_gold = get_material("mat_gold", PALETTE["SandstoneGold"])
    m_cream = get_material("mat_temple_cream", PALETTE["TempleCream"])
    m_brown = get_material("mat_lanna_wood", PALETTE["WarmBrown"])
    
    # Wooden display board
    make_cube("sign_base", (0.32, 0.55, 0.1), (0.0, 0.0, 0.05), parent=root, material=m_brown)
    make_cylinder("support_column", 0.022, 0.45, (0.0, 0.0, 0.325), parent=root, material=m_brown)
    
    # Double-sided display cabinet board
    make_cube("display_board", (0.45, 0.08, 0.28), (0.0, 0.0, 0.65), parent=root, material=m_brown)
    # Glass showcase area
    make_cube("glass_window", (0.4, 0.09, 0.22), (0.0, 0.0, 0.65), parent=root, material=m_cream)
    # Golden spire on top
    make_cone("golden_spire", 0.06, 0.15, (0.0, 0.0, 0.865), parent=root, material=m_gold)
    
    export_glb(root, os.path.join(dir_path, "heritage_museum_sign.glb"))


# --- BATCH EXECUTION RUNNER ---

def main():
    assets_dir = "d:/AnimeBangkokGame/assets/models/boards"
    
    cm_dir = os.path.join(assets_dir, "chiangmai")
    pk_dir = os.path.join(assets_dir, "phuket")
    ay_dir = os.path.join(assets_dir, "ayutthaya")
    
    os.makedirs(cm_dir, exist_ok=True)
    os.makedirs(pk_dir, exist_ok=True)
    os.makedirs(ay_dir, exist_ok=True)
    
    # 1. Chiang Mai Pack
    print("Generating Chiang Mai Asset Pack...")
    clear_scene()
    create_doi_suthep(cm_dir)
    clear_scene()
    create_tha_phae_gate(cm_dir)
    clear_scene()
    create_yi_peng_lantern(cm_dir)
    clear_scene()
    create_coffee_cart(cm_dir)
    clear_scene()
    create_coffee_village(cm_dir)
    clear_scene()
    create_elephant_sanctuary(cm_dir)
    clear_scene()
    create_mountain_resort(cm_dir)
    clear_scene()
    create_elephant_sign(cm_dir)
    clear_scene()
    create_lanna_craft_stall(cm_dir)
    clear_scene()
    create_flower_garden(cm_dir)
    clear_scene()
    create_northern_food_stall(cm_dir)
    clear_scene()
    create_pine_tree(cm_dir)
    clear_scene()
    create_mountain_bg(cm_dir)
    print("Chiang Mai Asset Pack completed!")
    
    # 2. Phuket Pack
    print("Generating Phuket Asset Pack...")
    clear_scene()
    create_longtail_boat(pk_dir)
    clear_scene()
    create_beach_umbrella(pk_dir)
    clear_scene()
    create_coconut_shop(pk_dir)
    clear_scene()
    create_phuket_old_town(pk_dir)
    clear_scene()
    create_big_buddha(pk_dir)
    clear_scene()
    create_promthep_cape(pk_dir)
    clear_scene()
    create_beach_resort(pk_dir)
    clear_scene()
    create_pearl_shop(pk_dir)
    clear_scene()
    create_seafood_stall(pk_dir)
    clear_scene()
    create_palm_tree(pk_dir)
    clear_scene()
    create_coral_rock(pk_dir)
    clear_scene()
    create_ocean_wave(pk_dir)
    clear_scene()
    create_beach_resort_sign(pk_dir)
    print("Phuket Asset Pack completed!")
    
    # 3. Ayutthaya Pack
    print("Generating Ayutthaya Asset Pack...")
    clear_scene()
    create_wat_mahathat(ay_dir)
    clear_scene()
    create_wat_chaiwatthanaram(ay_dir)
    clear_scene()
    create_ancient_palace_wall(ay_dir)
    clear_scene()
    create_old_city_gate(ay_dir)
    clear_scene()
    create_river_boat_pier(ay_dir)
    clear_scene()
    create_roti_sai_mai_cart(ay_dir)
    clear_scene()
    create_floating_market(ay_dir)
    clear_scene()
    create_thai_dessert_stall(ay_dir)
    clear_scene()
    create_elephant_camp_sign(ay_dir)
    clear_scene()
    create_temple_ruin_blocks(ay_dir)
    clear_scene()
    create_sandstone_pillar(ay_dir)
    clear_scene()
    create_river_bg(ay_dir)
    clear_scene()
    create_heritage_museum_sign(ay_dir)
    print("Ayutthaya Asset Pack completed!")
    
    print("All 3 Board Asset Packs generated successfully!")

if __name__ == "__main__":
    main()

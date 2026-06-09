import bpy
import os
import math
import shutil

# Mock context for background mode
import sys
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

def clear_scene():
    # Deselect all
    bpy.ops.object.select_all(action='DESELECT')
    # Select all objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # Remove orphan data
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)

def setup_diorama_environment(bg_color):
    # Setup world background
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs['Color'].default_value = bg_color
        bg_node.inputs['Strength'].default_value = 1.0

    # Add ground plane
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    ground = bpy.context.object
    ground.name = "Ground"
    ground_mat = bpy.data.materials.new("Ground_Mat")
    ground_mat.use_nodes = True
    bsdf = ground_mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (bg_color[0]*0.9, bg_color[1]*0.9, bg_color[2]*0.9, 1.0)
        if 'Roughness' in bsdf.inputs:
            bsdf.inputs['Roughness'].default_value = 0.95
    ground.data.materials.append(ground_mat)

    # Add sun light
    bpy.ops.object.light_add(type='SUN', radius=1, location=(5, -5, 10))
    sun = bpy.context.object
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(45), math.radians(30), math.radians(-45))

    # Add camera
    bpy.ops.object.camera_add(location=(8.5, -8.5, 8.5))
    cam = bpy.context.object
    cam.rotation_euler = (math.radians(54.736), 0, math.radians(45))
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 6.2
    bpy.context.scene.camera = cam

def import_and_arrange_assets(dir_path):
    files = [f for f in os.listdir(dir_path) if f.endswith('.glb')]
    cols = 4
    spacing_x = 1.4
    spacing_y = 1.4
    
    for idx, f in enumerate(files):
        row = idx // cols
        col = idx % cols
        
        # Calculate position centered around origin
        x_pos = (col - (cols - 1) / 2.0) * spacing_x
        y_pos = - (row - (len(files) / cols - 1) / 2.0) * spacing_y
        
        filepath = os.path.join(dir_path, f)
        # Import GLB
        bpy.ops.import_scene.gltf(filepath=filepath)
        imported_objs = [obj for obj in bpy.context.selected_objects]
        
        # Find root of imported group
        for obj in imported_objs:
            if obj.parent is None:
                obj.location = (x_pos, y_pos, 0.05)
                # Apply tiny rotation for diorama look
                obj.rotation_euler.z = math.radians(15)

def render_preview(dir_path, output_path, bg_color):
    print(f"Setting up render for {dir_path}...")
    clear_scene()
    setup_diorama_environment(bg_color)
    import_and_arrange_assets(dir_path)
    
    # Configure render settings
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 800
    scene.render.resolution_y = 600
    scene.render.filepath = output_path
    
    # Render
    print(f"Rendering to {output_path}...")
    bpy.ops.render.render(write_still=True)

def main():
    boards_dir = "d:/AnimeBangkokGame/assets/models/boards"
    artifact_dir = "C:/Users/iaun/.gemini/antigravity/brain/300bbbbb-1060-457a-93b8-06acdbfc3024"
    
    os.makedirs(boards_dir, exist_ok=True)
    os.makedirs(artifact_dir, exist_ok=True)
    
    packs = [
        ("chiangmai", (0.94, 0.92, 0.88, 1.0)), # Cream background
        ("phuket", (0.8, 0.92, 0.96, 1.0)),    # Soft sky blue
        ("ayutthaya", (0.92, 0.86, 0.78, 1.0))   # Soft sandstone grey/gold
    ]
    
    for pack_name, bg_color in packs:
        pack_path = os.path.join(boards_dir, pack_name)
        if not os.path.exists(pack_path):
            print(f"Pack dir {pack_path} does not exist. Skipping.")
            continue
            
        local_out = os.path.join(boards_dir, f"{pack_name}_preview.png")
        render_preview(pack_path, local_out, bg_color)
        
        # Copy to artifacts directory
        artifact_out = os.path.join(artifact_dir, f"{pack_name}_preview.png")
        try:
            shutil.copy2(local_out, artifact_out)
            print(f"Successfully copied preview to artifacts: {artifact_out}")
        except Exception as e:
            print(f"Failed to copy to artifacts: {e}")
            
    print("All preview renders completed successfully!")

if __name__ == "__main__":
    main()

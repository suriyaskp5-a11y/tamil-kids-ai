"""
Blender 3D Procedural Scene Generation & Animation Script
Executed headlessly via:
  blender -b -P generate_scene.py -- --scene-json <path_to_json> --output-video <path_to_mp4>
"""

import sys
import os
import json
import math

def parse_args():
    argv = sys.argv
    if "--" not in argv:
        return {}
    args = argv[argv.index("--") + 1:]
    parsed = {}
    for i in range(0, len(args), 2):
        if i + 1 < len(args):
            parsed[args[i].lstrip("-")] = args[i + 1]
    return parsed

def build_scene(scene_data, output_path):
    import bpy

    # Clean existing default objects
    bpy.ops.wm.read_factory_settings(use_empty=True)

    scene = bpy.context.scene
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.fps = 24

    # Calculate frame length based on duration
    duration = int(scene_data.get("duration_seconds", 30))
    scene.frame_start = 1
    scene.frame_end = duration * 24

    # Use EEVEE or Workbench for low-resource fast rendering
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except Exception:
        try:
            scene.render.engine = 'BLENDER_EEVEE'
        except Exception:
            scene.render.engine = 'BLENDER_WORKBENCH'

    # 1. Sky & World Background (Warm Golden Kids Ambience)
    world = bpy.data.worlds.new("KidsWorld")
    scene.world = world
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs['Color'].default_value = (0.52, 0.81, 0.98, 1.0) # Sky blue
        bg_node.inputs['Strength'].default_value = 1.2

    # 2. Ground Terrain (Vibrant Green stylized meadow)
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "MeadowGround"
    mat_ground = bpy.data.materials.new(name="MeadowGreen")
    mat_ground.use_nodes = True
    bsdf = mat_ground.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.24, 0.70, 0.29, 1.0) # Cartoon grass green
    ground.data.materials.append(mat_ground)

    # 3. Stylized Low-Poly Cartoon Trees
    tree_coords = [(-6, 8), (5, 9), (-8, -4), (7, -5), (0, 12)]
    for idx, (tx, ty) in enumerate(tree_coords):
        # Trunk
        bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=3.5, location=(tx, ty, 1.75))
        trunk = bpy.context.active_object
        mat_trunk = bpy.data.materials.new(name=f"TrunkMat_{idx}")
        mat_trunk.use_nodes = True
        bsdf = mat_trunk.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = (0.45, 0.25, 0.12, 1.0)
        trunk.data.materials.append(mat_trunk)

        # Foliage (Cartoon Sphere Cones)
        bpy.ops.mesh.primitive_cone_add(radius1=2.0, depth=3.0, location=(tx, ty, 4.0))
        foliage = bpy.context.active_object
        mat_foliage = bpy.data.materials.new(name=f"FoliageMat_{idx}")
        mat_foliage.use_nodes = True
        bsdf = mat_foliage.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = (0.15, 0.82, 0.35, 1.0)
        foliage.data.materials.append(mat_foliage)

    # 4. Main Character Proxy (Kid / Bunny stylized body)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.9, location=(0, 0, 1.8))
    character_head = bpy.context.active_object
    character_head.name = "CharacterHead"
    mat_char = bpy.data.materials.new(name="CharacterSkin")
    mat_char.use_nodes = True
    bsdf = mat_char.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.95, 0.88, 0.80, 1.0)
    character_head.data.materials.append(mat_char)

    # Character gentle breathing / nodding animation
    character_head.keyframe_insert(data_path="location", frame=1)
    character_head.location.z = 2.0
    character_head.keyframe_insert(data_path="location", frame=int(scene.frame_end / 2))
    character_head.location.z = 1.8
    character_head.keyframe_insert(data_path="location", frame=scene.frame_end)

    # 5. Sun Light
    bpy.ops.object.light_add(type='SUN', location=(10, -10, 15))
    sun = bpy.context.active_object
    sun.data.energy = 3.5
    sun.data.color = (1.0, 0.95, 0.85)

    # 6. Camera & Cinematic Movement
    bpy.ops.object.camera_add(location=(0, -8, 2.5), rotation=(math.radians(78), 0, 0))
    camera = bpy.context.active_object
    scene.camera = camera

    # Animate gentle camera pan / drift across the scene
    camera.keyframe_insert(data_path="location", frame=1)
    camera.location.x = 1.5
    camera.location.y = -7.0
    camera.keyframe_insert(data_path="location", frame=scene.frame_end)

    # 7. Render Settings (Output MP4)
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    scene.render.filepath = output_path

    print(f"[Blender] Starting render to: {output_path} (Frames {scene.frame_start} to {scene.frame_end})")
    bpy.ops.render.render(animation=True)
    print(f"[Blender] Finished rendering successfully.")

if __name__ == "__main__":
    args = parse_args()
    json_path = args.get("scene-json")
    out_video = args.get("output-video")

    scene_data = {}
    if json_path and os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            scene_data = json.load(f)

    if not out_video:
        out_video = os.path.abspath("scene_output.mp4")

    build_scene(scene_data, out_video)

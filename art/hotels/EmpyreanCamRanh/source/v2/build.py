"""Build the Empyrean Cam Ranh v2 exterior scene.

Run from anywhere:
  blender -b --factory-startup -P source/v2/build.py -- --out source/Empyrean_CamRanh_Exterior_v2.blend

Options:
  --parts towers,villas,site,planting,props,cameras   (default: all)
  --report qa/v2_geometry_report.json
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
import materials  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))   # art/hotels/EmpyreanCamRanh
materials.TEX_DIR = os.path.join(ROOT, "source", "textures")


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    out = dict(out=os.path.join(ROOT, "source", "Empyrean_CamRanh_Exterior_v2.blend"),
               parts="towers,villas,site,planting,props,cameras",
               report=os.path.join(ROOT, "qa", "v2_geometry_report.json"))
    for i in range(0, len(argv) - 1, 2):
        out[argv[i].lstrip("-")] = argv[i + 1]
    out["parts"] = set(out["parts"].split(","))
    return out


def reset_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for b in list(block):
            block.remove(b)
    sc = bpy.context.scene
    sc.name = "Empyrean_Exterior_v2"
    sc.unit_settings.system = "METRIC"
    return sc


def main():
    a = args()
    t0 = time.time()
    sc = reset_scene()
    root = bpy.data.collections.new("EMP2_Empyrean_Cam_Ranh")
    sc.collection.children.link(root)
    L = materials.build_library()
    info = {}
    if "towers" in a["parts"]:
        import towers
        res = towers.build_towers(L, root)
        info["towers"] = {k: dict(bays=v["plan"]["n"], floors=max(v["plan"]["floors"]),
                                  min_floors=min(v["plan"]["floors"]), windows=v["windows"],
                                  height_m=round(v["height"], 2)) for k, v in res.items()}
    if "villas" in a["parts"]:
        import villas
        info["villas"] = villas.build(L, root)
    if "site" in a["parts"]:
        import ground
        info["site"] = ground.build(L, root)
    if "planting" in a["parts"]:
        import planting
        info["planting"] = planting.build(L, root)
    if "props" in a["parts"]:
        import props
        info["props"] = props.build(L, root)
    if "cameras" in a["parts"]:
        import cameras
        info["cameras"] = cameras.build(sc, root)
    import qa
    rows = qa.mesh_report()
    tot, bad = qa.summary(rows)
    info["geometry"] = tot
    info["non_manifold_objects"] = [r["name"] for r in bad][:50]
    info["build_seconds"] = round(time.time() - t0, 1)
    os.makedirs(os.path.dirname(a["report"]), exist_ok=True)
    with open(a["report"], "w") as fh:
        json.dump(dict(summary=info, objects=rows), fh, indent=1)
    out_dir = os.path.dirname(os.path.abspath(a["out"]))
    for im in bpy.data.images:
        if im.filepath and not im.packed_file and os.path.isabs(bpy.path.abspath(im.filepath)):
            try:
                im.filepath = "//" + os.path.relpath(bpy.path.abspath(im.filepath), out_dir).replace(os.sep, "/")
            except ValueError:
                pass
    bpy.ops.wm.save_as_mainfile(filepath=a["out"], compress=True, relative_remap=False)
    print("BUILD_DONE", json.dumps(info))


if __name__ == "__main__":
    main()

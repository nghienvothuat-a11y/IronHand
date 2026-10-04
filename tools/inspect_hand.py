import bpy, json, math
from pathlib import Path
from mathutils import Vector

ROOT = Path('/Users/mrk/IronHand')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'assets/source/IronHand_MK1_Tripo_Source.fbx'))
report = {'objects': []}
for obj in list(bpy.context.scene.objects):
    item = {'name': obj.name, 'type': obj.type, 'location': list(obj.location), 'rotation': list(obj.rotation_euler), 'scale': list(obj.scale)}
    if obj.type == 'MESH':
        mesh = obj.data
        mesh.calc_loop_triangles()
        adjacency = [set() for _ in mesh.vertices]
        for edge in mesh.edges:
            a,b = edge.vertices
            adjacency[a].add(b); adjacency[b].add(a)
        seen=set(); components=[]
        for i in range(len(mesh.vertices)):
            if i in seen: continue
            stack=[i]; seen.add(i); ids=[]
            while stack:
                a=stack.pop(); ids.append(a)
                for b in adjacency[a]:
                    if b not in seen: seen.add(b); stack.append(b)
            coords=[obj.matrix_world @ mesh.vertices[k].co for k in ids]
            components.append({'vertices':len(ids), 'min':[min(v[k] for v in coords) for k in range(3)], 'max':[max(v[k] for v in coords) for k in range(3)], 'centroid':list(sum(coords,Vector())/len(coords))})
        coords=[obj.matrix_world @ v.co for v in mesh.vertices]
        item.update(vertices=len(mesh.vertices), faces=len(mesh.polygons), triangles=len(mesh.loop_triangles), materials=[m.name for m in mesh.materials], uv_layers=list(mesh.uv_layers.keys()), bounds={'min':[min(v[k] for v in coords) for k in range(3)],'max':[max(v[k] for v in coords) for k in range(3)]}, components=sorted(components,key=lambda c:c['vertices'],reverse=True))
        (ROOT/'art/blender/source_vertices.json').write_text(json.dumps([list(v) for v in coords]))
    report['objects'].append(item)
(ROOT/'art/blender/source_inspection.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'art/blender/IronHand_MK1_Source.blend'))
print(json.dumps(report,indent=2))

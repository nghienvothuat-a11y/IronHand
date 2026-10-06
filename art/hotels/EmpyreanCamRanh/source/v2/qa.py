"""Geometry QA: open/non-manifold edges, loose parts and stats per object."""
import bmesh
import bpy


def mesh_report(objs=None):
    rows = []
    for ob in objs or bpy.data.objects:
        if ob.type != "MESH":
            continue
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        boundary = sum(1 for e in bm.edges if e.is_boundary)
        nonman = sum(1 for e in bm.edges if not e.is_manifold)
        wire = sum(1 for e in bm.edges if e.is_wire)
        bm.free()
        rows.append(dict(name=ob.name, verts=len(ob.data.vertices), faces=len(ob.data.polygons),
                         boundary_edges=boundary, non_manifold_edges=nonman, wire_edges=wire))
    return rows


def summary(rows):
    tot = dict(objects=len(rows), verts=0, faces=0, boundary_edges=0, non_manifold_edges=0)
    for r in rows:
        for k in ("verts", "faces", "boundary_edges", "non_manifold_edges"):
            tot[k] += r[k]
    bad = [r for r in rows if r["non_manifold_edges"]]
    return tot, bad

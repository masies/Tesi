# MMBP:Desktop MS$ blender -b -P blenderTest.py 

import math;
import bpy;
import bmesh
import numpy as np;
from bpy import context as C
from  mathutils import Vector
import os

obj = None;


def clean_folder():
    # remove from target folder all old
    d = '/Users/MS/Desktop/test_tesi'
    filesToRemove = [os.path.join(d,f) for f in os.listdir(d)]
    for f in filesToRemove:
        os.remove(f) 

# Delete all object in scene, setup and clean
def clean_scene():
    # gather list of items of interest.
    candidate_list = [item.name for item in bpy.data.objects if item.type == "MESH"]
    # select them only.
    for object_name in candidate_list:
      bpy.data.objects[object_name].select = True
    # remove all selected.
    bpy.ops.object.delete()
    # remove the meshes, they have no users anymore.
    for item in bpy.data.meshes:
      bpy.data.meshes.remove(item)

def setup():
    clean_scene()
    clean_folder()
    import_mesh();

# import plus some tranformations
def import_mesh():
    bpy.ops.import_mesh.stl(filepath="/Users/MS/Desktop/Resegone.stl")
    global obj;
    obj = bpy.data.objects['Resegone']
    obj.hide_render = False;    

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all( action = 'DESELECT' )
    obj.select = True
    bpy.context.scene.objects.active = obj
    bpy.ops.transform.translate( value = ( 0, 0, -280 ) )
    #bpy.ops.transform.resize(value=(0.2, 0.2, 1))

setup();

def newobj(bm, name):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    ob = bpy.data.objects.new(name,me)
    C.scene.objects.link(ob)
    return ob

# values inside bounding box
def bounds(obj, local=False):

    local_coords = obj.bound_box[:]
    om = obj.matrix_world

    if not local:    
        worldify = lambda p: om * Vector(p[:]) 
        coords = [worldify(p).to_tuple() for p in local_coords]
    else:
        coords = [p[:] for p in local_coords]

    rotated = zip(*coords[::-1])

    push_axis = []
    for (axis, _list) in zip('xyz', rotated):
        info = lambda: None
        info.max = max(_list)
        info.min = min(_list)
        info.distance = info.max - info.min
        push_axis.append(info)

    import collections

    originals = dict(zip(['x', 'y', 'z'], push_axis))

    o_details = collections.namedtuple('object_details', 'x y z')
    return o_details(**originals)

            
def myDelete(toDelete):
    bpy.ops.object.select_all(action='DESELECT')
    toDelete.select = True
    bpy.ops.object.delete() 

object_details = bounds(C.object, True)
bpy.ops.object.mode_set(mode='OBJECT')


# number of cuts performed on each axis
cut_region = 2

# idexes to identify cube global position
cut_index_y = 0
cut_index_x = 0
cut_index_z = 0

x_step_size = obj.dimensions[0]/cut_region
y_step_size = obj.dimensions[1]/cut_region
z_step_size = obj.dimensions[2]/cut_region

bisection_outer = bmesh.new()
bisection_outer.from_mesh(C.object.data)

cut_verts = []
cut_edges = []

i = int(round(object_details.x.min))
while i <= int(round(object_details.x.max)):
        cut_index_y = 0
        cut_index_z = 0

        if (i > int(round(object_details.x.min))):

            bisection_inner = bisection_outer.copy()
            ret_x_outer = bmesh.ops.bisect_plane(bisection_outer, geom=bisection_outer.verts[:]+bisection_outer.edges[:]+bisection_outer.faces[:], plane_co=(i,0,0), plane_no=(1,0,0), clear_inner=True)
            ret_x_inner = bmesh.ops.bisect_plane(bisection_inner, geom=bisection_inner.verts[:]+bisection_inner.edges[:]+bisection_inner.faces[:], plane_co=(i,0,0), plane_no=(1,0,0), clear_outer=True)
            
            cut_verts.extend([v.index for v in ret_x_inner['geom_cut'] if isinstance(v, bmesh.types.BMVert)])
            cut_edges.extend([e.index for e in ret_x_inner['geom_cut'] if isinstance(e, bmesh.types.BMEdge)])
            ret_x_inner = bmesh.ops.holes_fill(bisection_inner, edges=[e for e in ret_x_inner['geom_cut'] if isinstance(e, bmesh.types.BMEdge)])
                    
            cut_verts.extend([v.index for v in ret_x_outer['geom_cut'] if isinstance(v, bmesh.types.BMVert)])
            cut_edges.extend([e.index for e in ret_x_outer['geom_cut'] if isinstance(e, bmesh.types.BMEdge)])
            ret_x_outer = bmesh.ops.holes_fill(bisection_outer, edges=[e for e in ret_x_outer['geom_cut'] if isinstance(e, bmesh.types.BMEdge)])

            to_divide_y = newobj(bisection_inner, "bisect-"+str(cut_index_x))



            bisection_inner.free()  # free and prevent further access

            bisection_outer_x = bmesh.new()
            bisection_outer_x.from_mesh(to_divide_y.data)

            myDelete(to_divide_y)
             
            j = int(round(object_details.y.min))
            while j <= int(round(object_details.y.max)):
                cut_index_z = 0

                if (j > int(round(object_details.y.min))):

                    bisection_inner_x = bisection_outer_x.copy()
                    ret_y_outer = bmesh.ops.bisect_plane(bisection_outer_x, geom=bisection_outer_x.verts[:]+bisection_outer_x.edges[:]+bisection_outer_x.faces[:], plane_co=(0,j,0), plane_no=(0,1,0), clear_inner=True)
                    ret_y_inner = bmesh.ops.bisect_plane(bisection_inner_x, geom=bisection_inner_x.verts[:]+bisection_inner_x.edges[:]+bisection_inner_x.faces[:], plane_co=(0,j,0), plane_no=(0,1,0), clear_outer=True)
                    
                    cut_verts.extend([v.index for v in ret_y_inner['geom_cut'] if isinstance(v, bmesh.types.BMVert)])
                    cut_edges.extend([e.index for e in ret_y_inner['geom_cut'] if isinstance(e, bmesh.types.BMEdge)])
                    ret_y_inner = bmesh.ops.holes_fill(bisection_inner_x, edges=[e for e in ret_y_inner['geom_cut'] if isinstance(e, bmesh.types.BMEdge)])

                    cut_verts.extend([v.index for v in ret_y_outer['geom_cut'] if isinstance(v, bmesh.types.BMVert)])
                    cut_edges.extend([e.index for e in ret_y_outer['geom_cut'] if isinstance(e, bmesh.types.BMEdge)])
                    ret_y_outer = bmesh.ops.holes_fill(bisection_outer_x, edges=[e for e in ret_y_outer['geom_cut'] if isinstance(e, bmesh.types.BMEdge)])


                    to_divide_z = newobj(bisection_inner_x, "bisect-" + str(cut_index_x)+  "-"+str(cut_index_y))

                    bisection_inner_x.free()  # free and prevent further access

                    bisection_outer_y = bmesh.new()
                    bisection_outer_y.from_mesh(to_divide_z.data)

                    myDelete(to_divide_z)

                    k = int(round(object_details.z.min))
                    while k <= int(round(object_details.z.max)) + z_step_size:
                        if (k > int(round(object_details.z.min))):
                            bisection_inner_y = bisection_outer_y.copy()
                            ret_z_outer = bmesh.ops.bisect_plane(bisection_outer_y, geom=bisection_outer_y.verts[:]+bisection_outer_y.edges[:]+bisection_outer_y.faces[:], plane_co=(0,0,k), plane_no=(0,0,1), clear_inner=True)
                            ret_z_inner = bmesh.ops.bisect_plane(bisection_inner_y, geom=bisection_inner_y.verts[:]+bisection_inner_y.edges[:]+bisection_inner_y.faces[:], plane_co=(0,0,k), plane_no=(0,0,1), clear_outer=True)
                            
                            cut_verts.extend([v.index for v in ret_z_inner['geom_cut'] if isinstance(v, bmesh.types.BMVert)])
                            cut_edges.extend([e.index for e in ret_z_inner['geom_cut'] if isinstance(e, bmesh.types.BMEdge)])
                            ret_z_inner = bmesh.ops.holes_fill(bisection_inner_y, edges=[e for e in ret_z_inner['geom_cut'] if isinstance(e, bmesh.types.BMEdge)])

                            cut_verts.extend([v.index for v in ret_z_outer['geom_cut'] if isinstance(v, bmesh.types.BMVert)])
                            cut_edges.extend([e.index for e in ret_z_outer['geom_cut'] if isinstance(e, bmesh.types.BMEdge)])
                            ret_z_outer = bmesh.ops.holes_fill(bisection_outer_y, edges=[e for e in ret_z_outer['geom_cut'] if isinstance(e, bmesh.types.BMEdge)])

                            bmesh.ops.solidify(bisection_inner_y, geom=bisection_inner_y.verts[:]+bisection_inner_y.edges[:]+bisection_inner_y.faces[:], thickness=0.5)

                            if (bisection_inner_y.calc_volume() > 0):
                                # add object 
                                ob = newobj(bisection_inner_y, "bisect-" + str(cut_index_x)+  "-"+str(cut_index_y)+  "-"+str(cut_index_z))
                                
                                # # add bounding box to the object
                                # context = bpy.context
                                # scene = context.scene
                                # bm = bmesh.new()
                                # me = ob.data.copy()
                                # verts = [bm.verts.new(b) for b in ob.bound_box]
                                # bmesh.ops.convex_hull(bm, input=verts)
                                # bm.to_mesh(me)
                                # newobj(bm, "box-" + str(cut_index_x)+  "-"+str(cut_index_y)+  "-"+str(cut_index_z))



                            bisection_inner_y.free()  # free and prevent further access
                            
                            cut_index_z+=1
                        k += z_step_size

                    cut_index_y+=1
                j += y_step_size

            cut_index_x+=1
        i += x_step_size

# # attempt to fill holes in meshes
candidate_list = [item.name for item in bpy.data.objects if item.type == "MESH"]
# # select them only.
for object_name in candidate_list:
    bpy.data.objects[object_name].select = True

    m = bpy.data.objects[object_name].modifiers.new("Solidify", type='SOLIDIFY')
    m.thickness = 0.5






# context = bpy.context
# scene = context.scene
# bm = bmesh.new()
# mesh_obs = [o for o in scene.objects if o.type == 'MESH']
# for ob in mesh_obs:
#     # me = ob.data 
#     me = ob.data.copy() # create a copy

#     verts = [bm.verts.new(b) for b in ob.bound_box]
#     bmesh.ops.convex_hull(bm, input=verts)
#     bm.to_mesh(me)
#     newobj(bm, "bisect-")
    
#     bm.clear()
# bm.free()

# scn = bpy.context.scene
# scn.objects.active = bpy.data.objects[0]


# bpy.ops.object.mode_set(mode='EDIT')
# bpy.ops.mesh.select_all(action='SELECT')
# bpy.ops.mesh.solidify()
# # bpy.ops.mesh.select_all(action='SELECT')
# # bpy.ops.mesh.dissolve_limited()
# # bpy.ops.mesh.select_all(action='SELECT')
# # bpy.ops.mesh.fill_holes()
# # bpy.ops.mesh.select_all(action='SELECT')
# # bpy.ops.mesh.print3d_clean_non_manifold()
# bpy.ops.object.mode_set(mode='OBJECT')


# remove the original object
# bpy.data.objects.remove(C.object, True)


# code to export all the objects in separated files
def save_to_folder(location= '/Users/MS/Desktop/test_tesi'):
    # get the path where the blend file is located
    basedir = bpy.path.abspath(location)

    # deselect all objects
    bpy.ops.object.select_all(action='DESELECT')    

    # loop through all the objects in the scene
    scene = bpy.context.scene
    for ob in scene.objects:
        # make the current object active and select it
        scene.objects.active = ob
        ob.select = True

        # make sure that we only export meshes
        if ob.type == 'MESH':
            # export the currently selected object to its own file based on its name
            bpy.ops.export_mesh.stl(
                    filepath=(basedir + '/' + ob.name + '.stl'),
                    use_selection=True,
                    )
        # deselect the object and move on to another if any more are left
        ob.select = False

def final_clean():
    d = '/Users/MS/Desktop/test_tesi'
    filesToRemove = [os.path.join(d,f) for f in os.listdir(d)]
    for f in filesToRemove:
        if ".mtl" in f:
            os.remove(f) 

save_to_folder()
final_clean()

# bpy.ops.mesh.primitive_plane_add()
# bpy.data.objects["Plane"].scale[0] = 100
# bpy.data.objects["Plane"].scale[1] = 100
# bpy.data.objects["Plane"].rotation_euler[0] = 0
# bpy.data.objects["Plane"].location[0] = 20
# bpy.data.objects["Plane"].location[1] = 0
# bpy.data.objects["Plane"].select = True
# bpy.ops.object.modifier_add(type='BOOLEAN')
# bpy.data.objects["bisect-.001"].location[2] = 50
# bpy.data.objects["bisect-2-2-1"].location[2] = 50

# bpy.data.objects["Plane"].modifiers["Boolean"].object = bpy.data.objects["bisect-0"]
# bpy.ops.object.modifier_apply(type='BOOLEAN')

# MMBP:Desktop MS$ blender -b -P blenderTest.py 

import math;
import bpy;
import bmesh
import numpy as np;
from bpy import context as C
from  mathutils import Vector
import os
import fnmatch

obj = None;
DIRNAME = os.path.dirname(__file__);
DIRNAME = "/Users/MS/Desktop/Projects/TESI/Tesi/src"
RESULTS_DIR = '../results'
MESH_NAME = "2x2Remastered"
MODELS_DIR = '../models/finalCut/'+MESH_NAME+'.stl'
SCALE=1;
FINAL_SIZE = 1000;


def clean_folder():
    # remove from target folder all old
    filepath = os.path.join(DIRNAME, RESULTS_DIR)
    filesToRemove = [os.path.join(filepath,f) for f in os.listdir(filepath)]
    for filepath in filesToRemove:
        os.remove(filepath) 

# Delete all object in scene, setup and clean
def clean_scene():
    for bpy_data_iter in (
                bpy.data.objects,
                bpy.data.meshes,
                bpy.data.lamps,
                bpy.data.cameras,
        ):
            for id_data in bpy_data_iter:
                bpy_data_iter.remove(id_data)

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
    filepath = os.path.join(DIRNAME, MODELS_DIR)
    bpy.ops.import_mesh.stl(filepath=filepath)
    global obj;
    obj = bpy.data.objects[MESH_NAME]
    obj.hide_render = False;    
    bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN')
    bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN')
    
    
    

    # x, y, z = bpy.context.active_object.dimensions
    # print("x is : ", x)
    # print("y is : ", y)
    # print("z is : ", z)
    # global SCALE
    # SCALE = FINAL_SIZE/obj.dimensions[0];
    #bpy.ops.transform.resize(value=(SCALE, SCALE, SCALE))
    
    # global SCALE
    # SCALE = x/20;
    # if y > x:
    #     SCALE = y/25
    # if z > y:
    #     SCALE = z/20;
    #     if y > z:
    #         SCALE = y/25

    bpy.ops.object.mode_set(mode='EDIT')
    #bpy.ops.mesh.dissolve_limited()
    bpy.ops.object.mode_set(mode='OBJECT')

    #bpy.ops.transform.translate( value = ( 0, 0, -280 ) )

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
cut_region =5

# idexes to identify cube global position
cut_index_y = 0
cut_index_x = 0
cut_index_z = 0

print("x is : ", obj.dimensions[0])
print("y is : ", obj.dimensions[1])
print("z is : ", obj.dimensions[2])

x_step_size = obj.dimensions[0]/cut_region
y_step_size = obj.dimensions[1]/cut_region
z_step_size = 100

print("x_step_size is : ", x_step_size)
print("y_step_size is : ", y_step_size)
print("z_step_size is : ", z_step_size)

bisection_outer = bmesh.new()
bisection_outer.from_mesh(C.object.data)

def fill(geom,mesh):

    bmesh.ops.holes_fill(mesh, edges=[e for e in geom['geom_cut'] if isinstance(e, bmesh.types.BMEdge)])
    # bmesh.ops.face_attribute_fill(mesh, use_data=True, faces=[f for f in geom['geom'] if isinstance(f, bmesh.types.BMFace)])
    # bmesh.ops.dissolve_limit(mesh, angle_limit=0.02, use_dissolve_boundaries=True, verts=[f for f in geom['geom'] if isinstance(f, bmesh.types.BMVert)], edges=[f for f in geom['geom'] if isinstance(f, bmesh.types.BMEdge)])

    # bmesh.ops.face_attribute_fill(bisection_inner_x, use_data=True, faces=[f for f in ret_y_inner['geom'] if isinstance(f, bmesh.types.BMFace)])
    # bmesh.ops.solidify(mesh, geom=mesh.verts[:]+mesh.edges[:]+mesh.faces[:], thickness=0.1)

    return mesh




i = int(round(object_details.y.min)) 
while i <= int(round(object_details.y.max)):
        # print("y cutting is :",i)
        cut_index_y = 0
        cut_index_z = 0

        if (i > int(round(object_details.y.min))):
            bisection_inner = bisection_outer.copy()
            #  TODO : put this in the separate funtion
            ret_x_inner = bmesh.ops.bisect_plane(bisection_inner, geom=bisection_inner.verts[:]+bisection_inner.edges[:]+bisection_inner.faces[:], plane_co=(0,i,0), plane_no=(0,1,0), clear_outer=True)
            fill(ret_x_inner,bisection_inner)
            
            ret_x_outer = bmesh.ops.bisect_plane(bisection_outer, geom=bisection_outer.verts[:]+bisection_outer.edges[:]+bisection_outer.faces[:], plane_co=(0,i,0), plane_no=(0,1,0), clear_inner=True)
            fill(ret_x_outer,bisection_outer)


            

            to_divide_y = newobj(bisection_inner, "bisect-"+str(cut_index_x))

            bisection_inner.free()  # free and prevent further access

            bisection_outer_x = bmesh.new()
            bisection_outer_x.from_mesh(to_divide_y.data)

            myDelete(to_divide_y)
            
            j = int(round(object_details.x.min)) 
            while j <= int(round(object_details.x.max)) :
                # print("x cutting is :",j)

                cut_index_z = 0

                if (j > int(round(object_details.x.min))):
                    bisection_inner_x = bisection_outer_x.copy()
                    ret_y_inner = bmesh.ops.bisect_plane(bisection_inner_x, geom=bisection_inner_x.verts[:]+bisection_inner_x.edges[:]+bisection_inner_x.faces[:], plane_co=(j,0,0), plane_no=(1,0,0), clear_outer=True)
                    
                    # broken for pieces wich do not touch external
                    fill(ret_y_inner,bisection_inner_x)

                    ret_y_outer = bmesh.ops.bisect_plane(bisection_outer_x, geom=bisection_outer_x.verts[:]+bisection_outer_x.edges[:]+bisection_outer_x.faces[:], plane_co=(j,0,0), plane_no=(1,0,0), clear_inner=True)
                    fill(ret_y_outer,bisection_outer_x)

                    
                    

                    to_divide_z = newobj(bisection_inner_x, "bisect-" + str(cut_index_x)+  "-"+str(cut_index_y))

                    bisection_inner_x.free()  # free and prevent further access

                    bisection_outer_y = bmesh.new()
                    bisection_outer_y.from_mesh(to_divide_z.data)

                    ob = newobj(bisection_outer_y, "bisect-" + str(cut_index_x)+  "-"+str(cut_index_y))
                    print("obj      : ","bisect-" + str(cut_index_x)+  "-"+str(cut_index_y))
                    print("obj x is : ", ob.dimensions[0])
                    print("obj y is : ", ob.dimensions[1])


                    
                    ####################################################################

                    bpy.ops.object.text_add()
                    tx=bpy.context.object
                    tx.data.body = ">" + str(cut_index_x)+  "-"+str(cut_index_y)
                    bpy.ops.transform.resize(value=(-10, 10, 10))
                    tx.location[0] = j - ob.dimensions[0]/2 + tx.dimensions[0]/2 
                    tx.location[1] = i - ob.dimensions[1]/2 + tx.dimensions[1]/2 
                    tx.location[2] = int(round(object_details.z.min)) + 1
                    bpy.context.scene.objects.active = tx        #make sure my Text object is correctly selected
                    tx.select = True
                    bpy.ops.object.convert(target="MESH") 


                  
              




                    

                    
            
                    # import duplo
                    if i <= int(round(object_details.y.max)) - y_step_size:
                        if j  <= int(round(object_details.x.max)) - x_step_size:
                            prior_objects = [object.name for object in bpy.context.scene.objects]

                            duplopath = os.path.join(DIRNAME, '../models/DuploPlate.stl')
                            bpy.ops.import_mesh.stl(filepath=duplopath)

                            new_current_objects = [object.name for object in bpy.context.scene.objects]
                            new_objects = set(new_current_objects)-set(prior_objects) 
                     
                            bpy.ops.transform.resize(value=(0.13, 0.13, 0.13))
                            
                            plate = bpy.data.objects[next(iter(new_objects))]  
                            
                            plate.location[0] = j #- ob.dimensions[1] + plate.dimensions[1]/2
                            plate.location[1] = i #+ ob.dimensions[0] - plate.dimensions[0]/2 
                            plate.location[2] = int(round(object_details.z.min))  -1.4


                    ####################################################################








                    # bool_one = ob.modifiers.new(type="BOOLEAN", name="bool 1")
                    # bool_one.object = plate
                    # bool_one.operation = 'DIFFERENCE'
                    # for modifier in ob.modifiers:
                    #        bpy.ops.object.modifier_apply(modifier=modifier.name)
                    #        print(modifier.name)

                    # plate.hide = True
             
             
                    ####################################################################

                    myDelete(to_divide_z)

                    # k = int(round(object_details.z.min))
                    # while k <= int(round(object_details.z.max)) + z_step_size:
                    #     if (k > int(round(object_details.z.min))):
                    #         bisection_inner_y = bisection_outer_y.copy()
                    #         ret_z_inner = bmesh.ops.bisect_plane(bisection_inner_y, geom=bisection_inner_y.verts[:]+bisection_inner_y.edges[:]+bisection_inner_y.faces[:], plane_co=(0,0,k), plane_no=(0,0,1), clear_outer=True)
                    #         fill(ret_z_inner,bisection_inner_y)
                    #         ret_z_outer = bmesh.ops.bisect_plane(bisection_outer_y, geom=bisection_outer_y.verts[:]+bisection_outer_y.edges[:]+bisection_outer_y.faces[:], plane_co=(0,0,k), plane_no=(0,0,1), clear_inner=True)
                    #         fill(ret_z_outer,bisection_outer_y)


                            


                    #         # -------->>>> add this row in each process    
                    #         # bmesh.ops.solidify(bisection_inner_y, geom=bisection_inner_y.verts[:]+bisection_inner_y.edges[:]+bisection_inner_y.faces[:], thickness=0.1)

                    #         if (bisection_inner_y.calc_volume() > 0):
                    #             # add object 
                    #             ob = newobj(bisection_inner_y, "bisect-" + str(cut_index_x)+  "-"+str(cut_index_y)+  "-"+str(cut_index_z))
                                
                    #             # # add bounding box to the object
                    #             # context = bpy.context
                    #             # scene = context.scene
                    #             # bm = bmesh.new()
                    #             # me = ob.data.copy()
                    #             # verts = [bm.verts.new(b) for b in ob.bound_box]
                    #             # bmesh.ops.convex_hull(bm, input=verts)
                    #             # bm.to_mesh(me)
                    #             # newobj(bm, "box-" + str(cut_index_x)+  "-"+str(cut_index_y)+  "-"+str(cut_index_z))



                    #         bisection_inner_y.free()  # free and prevent further access
                            
                    #         cut_index_z+=1
                    #     k += z_step_size

                    cut_index_y+=1
                j += x_step_size

            cut_index_x+=1
        i += y_step_size

# # attempt to fill holes in meshes
candidate_list = [item.name for item in bpy.data.objects if item.type == "MESH"]
# # select them only.
for object_name in candidate_list:
    bpy.data.objects[object_name].select = True
    # bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN')
    #m = bpy.data.objects[object_name].modifiers.new("Solidify", type='SOLIDIFY')
    #m.thickness = 0.05
    #m.edge_crease_inner = 0.5
    #m.use_rim_only = True
    #m.use_quality_normals = True
    #m.use_even_offset = True



scene = bpy.context.scene


bisect_objs = [obj for obj in scene.objects if fnmatch.fnmatchcase(obj.name, "bisect*")]
plate_objs = [obj for obj in scene.objects if fnmatch.fnmatchcase(obj.name, "Duplo*")]
Texts = [obj for obj in scene.objects if fnmatch.fnmatchcase(obj.name, "Text*")]
    # # select them only.
for text in Texts:
    # text.select = True
    tx = text.modifiers.new("Solidify", type='SOLIDIFY')
    tx.thickness = 0.2
    # bpy.ops.object.convert(target='MESH')


for ob in bisect_objs:
    for on_p in plate_objs:
        bool_one = ob.modifiers.new(type="BOOLEAN", name="bool 1")
        bool_one.object = on_p
        bool_one.operation = 'DIFFERENCE'
    for modifier in ob.modifiers:
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            print(modifier.name)
    # print(ob)

for ob in bisect_objs:
    for on_p in Texts:
        bool_two = ob.modifiers.new(type="BOOLEAN", name="bool 2")
        bool_two.object = on_p
        bool_two.operation = 'DIFFERENCE'
    for modifier in ob.modifiers:
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            print(modifier.name)
    # print(ob)



# target_obj = context.active_object
#  tool_objs = [o for o in context.selected_objects if o != target_obj]

#  BOOL = 'BOOLEAN'
#  # first add them.
#  for obj in tool_objs:
#      bool_mod = target_obj.modifiers.new(name='diff_' + obj.name, type=BOOL)
#      bool_mod.operation = 'DIFFERENCE'
#      bool_mod.object = obj
#      obj.hide = True

#  # then apply them individually.
 # for modifier in target_obj.modifiers:
 #     bpy.ops.object.modifier_apply(modifier=modifier.name)

print(bisect_objs)
print(plate_objs)


# will need this line to have max scale for each
bpy.ops.transform.resize(value=(5, 5, 5))




# remove the original object
#bpy.data.objects.remove(C.object, True)


# code to export all the objects in separated files
def save_to_folder():
    # get the path where the blend file is located
    filepath = os.path.join(DIRNAME, RESULTS_DIR)
    basedir = bpy.path.abspath(filepath)

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
    filepath = os.path.join(DIRNAME, RESULTS_DIR)

    filesToRemove = [os.path.join(filepath,f) for f in os.listdir(filepath)]
    for f in filesToRemove:
        if ".mtl" in f:
            os.remove(f) 

save_to_folder()
final_clean()





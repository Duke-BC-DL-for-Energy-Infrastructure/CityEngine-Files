'''
Created on 06.26.2019

@author: Fanjie Kong



'''
from scripting import *
import time
import random
import math
import os
import shutil
# get a CityEngine instance
ce = CE()
TileSize=608
Resolution = 1
#TileSize=8824
STEP = Resolution * TileSize

def dynamic_attributes(adjust_list, camera_angle, light_angle, light_intensity, dynamic_range, mode):
    '''
    adjust_list: a list of strings
    camera_angle: number between 0~90
    light_angle: number between 0~90
    light_instensity: number between 0~1
    dynamic_range: a dictionary has the form
        {'ca': int, 'la': int, 'li': int}
        The value  will vary in range of [sv-dv, sv+dv]
    '''
    lightSettings = ce.getLighting()
    assert ('la' in adjust_list) or ('ca' in adjust_list) or ('li' in adjust_list), "Please select an attribute to augment"
    if 'la' in adjust_list:
        light_angle = light_angle + random.randint(-dynamic_range['la'], dynamic_range['la'])
        lightSettings.setSolarElevationAngle(light_angle)
    if 'ca' in adjust_list:
        camera_angle = camera_angle + random.randint(-dynamic_range['ca'], dynamic_range['ca'])
        camera_angle = '-' + str(camera_angle)
    if 'li' in adjust_list:
        light_intensity = min(1, light_intensity + 0.1 * random.randint(-int(10*dynamic_range['li']), int(10*dynamic_range['li'])))
        lightSettings.setSolarIntensity(light_intensity)
    if mode == 'GT':
        return camera_angle
    ce.setLighting(lightSettings)
    print("New attribute triple bracket is ", (light_angle, camera_angle, light_intensity))
    return camera_angle

'''
parse lines and look for id
prepare cam data in array
non-generic, works for specific fbx part only
'''
def drange(x, y, jump):
      while x < y:
        yield x
        x += jump

def parseLine(lines, id):
    data = False
    for line in lines:
        if line.find(id) >=0 :
            data = line.partition(id)[2]
            break
    if data:
        data = data[:len(data)-1] # strip \n
        data = data.split(",")
    return data

'''
parse lines from fbx file that store cam data
'''
def parseFbxCam(filename):
    f=open(filename)
    lines = f.readlines()
    cnt = 0
    loc =  parseLine(lines, 'Property: "Lcl Translation", "Lcl Translation", "A+",')
    rot =  parseLine(lines, 'Property: "Lcl Rotation", "Lcl Rotation", "A+",')
    return [loc,rot]


'''
helper functions
'''
def setCamPosV(v, vec):
    v.setCameraPosition(vec[0], vec[1], vec[2])

def setCamRotV(v, vec):
    v.setCameraRotation(vec[0], vec[1], vec[2])

'''
sets camera on first CE viewport
'''
def setCamData(data):
    v = ce.getObjectsFrom(ce.get3DViews(), ce.isViewport)[0]
    setCamPosV(v, data[0])
    setCamRotV(v, data[1])
#    print(dir(v))
#    exit(0)
    return v

'''
###############-----------------------------> need to change
'''
def setCamHeight(FOV=15, tile_width=608, resolution=0.3):
    '''
    Calculates proper height of camera in CityEngine based on current camera
    used (FOV in degrees), desired tile size, and desired resolution
    '''
    FOV = math.radians(FOV)
#    print('FOV', FOV)
    d = tile_width * resolution #pixel width of tile * resolution in m/pixel
    return str(d / (2*math.tan(FOV/2)))


'''
master function
'''
def importFbxCamera(fbxfile, axis, angle, height):
    data = parseFbxCam(fbxfile)
    if(data[0] and data[1]) :
        data[0][0]=str(axis[0])
        data[0][1] = height #200 #  height
        data[0][2]= str(axis[1])
        data[1][0] = data[1][1] = angle
        v = setCamData(data)
#        print(dir(v))
#        print "Camera set to "+str(data)
        return v
    else:
        print "No camera data found in file "+file

'''
###############-----------------------------> need to change
'''
def exportImages(directory, v, Tag=""):
   path = directory + "/" + Tag + ".png"
   v.snapshot(path, width = TileSize, height = TileSize)

'''
###############-----------------------------> need to change
'''
def exportGroundtruths(directory, v, Tag=""):
    path = directory + "/" + Tag + ".png"
    v.snapshot(path, width = TileSize, height = TileSize)

'''
###############-----------------------------> need to change
'''
def exportGroundtruths2(directory, v, Tag=""):
   path = directory + "/" + Tag + ".png"
   v.snapshot(path, width = TileSize, height = TileSize)

#def loop_capturer_dynamic_attributes(start_axis, end_axis, tag,
#                                     adjust_list = ['la', 'ca', 'li'],
#                                     light_angle = 90, light_intensity=1,
#                                     dynamic_range={'ca': 10, 'la': 10, 'li': 0.2},
#                                     camera_angle=90, height='651.7',mode='RGB',
#                                     folder_name='test')
def loop_capturer_dynamic_attributes(start_axis, end_axis, tag,
                                     adjust_list = ['la', 'ca', 'li'],
                                     light_angle=60,  camera_angle=90, light_intensity=1,
                                     dynamic_range={'ca': 0.0, 'la': 0, 'li': 0.0},
                                     mode='RGB', folder_name='test'):
    counter = 0
    print('Start Shooting!')
    camfile = ce.toFSPath("data/camera.fbx") 
    height = setCamHeight(tile_width=TileSize)
    height = 2500
    #height = 2400.0
    print("height: {}".format(height))
    angle = dynamic_attributes(adjust_list, camera_angle, light_angle, light_intensity, dynamic_range, mode)
    print("angle: {}".format(angle))
    print(start_axis[0], end_axis[0], STEP)
    
    for i in drange(start_axis[0], end_axis[0], STEP): # x
        for j in drange(start_axis[1], end_axis[1], STEP): # z
            view = importFbxCamera(camfile, (i, j), angle, height)
            print('i, j ', i, j)
            counter += 1
            print(counter)
            time.sleep(0.1) #time.sleep(0.02)
            
            if mode == 'RGB':
#                lightSettings = ce.getLighting()
#                lightSettings.setSolarElevationAngle(90)
#                lightSettings.setSolarIntensity(0.3)
#                ce.setLighting(lightSettings)
                exportImages(ce.toFSPath('images/{}'.format(folder_name)), view, Tag=tag+'_'+str(counter))
#                exportImages(ce.toFSPath('images/{}'.format(folder_name)), view, Tag=tag+'_'+str(counter))
#                exportImages(ce.toFSPath('images/{}'.format(folder_name)), view, Tag=tag+'_'+str(counter))
            elif mode == 'GT':
#                lightSettings = ce.getLighting()
#                lightSettings.setSolarElevationAngle(90)
#                lightSettings.setSolarIntensity(1)
#                ce.setLighting(lightSettings)
                ce.waitForUIIdle()
                exportGroundtruths(ce.toFSPath('images/{}'.format(folder_name)), view, Tag=tag+'_'+str(counter))
                exportGroundtruths(ce.toFSPath('images/{}'.format(folder_name)), view, Tag=tag+'_'+str(counter))
#                exportGroundtruths(ce.toFSPath('images/{}'.format(folder_name)), view, Tag=tag+'_'+str(counter))


'''
###############-----------------------------> need to change
'''
def load_rule_file(seed, rule_file_path):
#    ge_models = ce.getObjectsFrom(ce.scene, ce.isModel)
#    ce.cleanupShapes(ge_models)
    all_shapes = ce.getObjectsFrom(ce.scene, ce.isShape)
    ce.setSeed(all_shapes, seed)
    ce.setRuleFile(all_shapes, rule_file_path)
    ce.generateModels(all_shapes)
    ce.waitForUIIdle()
    time.sleep(1)
    print('load rules ok')
    
'''
###############-----------------------------> RGB
'''   
def take_rgb_images(dt, sd, start_axis, end_axis, mode = 'RGB', parent_folder='', camera_angle=90):
    print('start')
    start_time = time.time()
    tag='NE_wnd_sd{}'.format(sd) 
    folder_name='{}/{}_all_images_step{}'.format(parent_folder, dt, STEP)  
    print(folder_name)
    if not os.path.exists(ce.toFSPath('images/{}'.format(folder_name))):
        os.makedirs(ce.toFSPath('images/{}'.format(folder_name)))
    
#        shutil.rmtree(ce.toFSPath('images/{}'.format(folder_name)))
    '''# ORGINAL'''
    light_angle= 50
    camera_angle= 90
    light_intensity= 0.8
    loop_capturer_dynamic_attributes(start_axis=start_axis, end_axis=end_axis,
                                 tag=tag, mode=mode, folder_name=folder_name,
                                 light_angle=light_angle, 
                                 camera_angle=camera_angle,
                                 light_intensity=light_intensity)
    print('Duration: {}'.format(time.time()-start_time)) 
    
'''
###############-----------------------------> GT
why for Francisco the color GT and the texture GT not consistent?????????
'''   
def take_gt_images(dt, sd, start_axis, end_axis, mode = 'GT', parent_folder='', camera_angle=90):
    
    print('start')
    start_time = time.time()
    tag='NE_wnd_sd{}'.format(sd) 
    folder_name='{}/{}_all_annos_step{}'.format(parent_folder, dt, STEP)  
    if not os.path.exists(ce.toFSPath('images/{}'.format(folder_name))):
        os.makedirs(ce.toFSPath('images/{}'.format(folder_name)))
#        print('remove')
#        shutil.rmtree(ce.toFSPath('images/{}'.format(folder_name)))
#    print('removed')
    '''# ORGINAL'''
    camera_angle= 90
    loop_capturer_dynamic_attributes(start_axis=start_axis, end_axis=end_axis,
                                 tag=tag, mode=mode, folder_name=folder_name, camera_angle=camera_angle)
    print('Duration: {}'.format(time.time()-start_time)) 
    
if __name__ == '__main__':
    '''
    shoot each location with a combination of randomized parameters in a range
    eg:
    adjust_list = ['la', 'ca', 'li'], # list of parameters to be randomized
    light_angle=45,  camera_angle=80, light_intensity=0.8,  # centers of the range
    dynamic_range={'ca': 10, 'la': 15, 'li': 0.3} # the width of the range

    This set of parameters means shoot an image
     where camera angle is a random number in [70, 90],
     light angle is a random number in [30, 60],
     light intensity is a random number in [0.5, 1]

    '''
    
    display_type = ['color'] #, 'mixed'
    rgb_rule_file = ['rules/yx_wind_turbine_color-bh_edited.cga'] #
    gt_rule_file = ['rules/yx_wind_turbine_labeling_color-bh_edited.cga'] #
    '''
    start_axis=(80 + STEP//2, 48 + STEP//2)
    end_axis=(640 - STEP//2, 608 - STEP//2)
    '''
    start_axis=(-304, -304)
    end_axis=(305, 305)
    ite_num = 191 # 45
    
    
    '''rgb + gt'''
    '''
    seed = 0
    random.seed(seed)
    for dt in display_type:
        for sd in range(ite_num):
            print(sd)'''
    
    ''' rgb'''
    rule_files = rgb_rule_file
    seed = 3
    random.seed(seed)
    
    for dt in display_type:
        for sd in range(ite_num):
            print(sd)
            #print(rule_files[display_type.index(dt)])
            #print(display_type.index(dt))
            #load_rule_file(sd, rule_files[display_type.index(dt)])
            random_rule = 'rules/yx_wind_turbine_color-bh_edited_bin{}.cga'.format(random.randint(0,19))
            print(random_rule)
            load_rule_file(sd, random_rule)
            #rule = 'rules/yx_wind_turbine_labeling_color-bh_edited.cga'
            #print(rule)
            #load_rule_file(sd, rule)
            parent_folder = 'synthetic_wind_turbine_images'
            print(parent_folder)
            # rgb
            take_rgb_images(dt, sd, start_axis, end_axis, parent_folder=parent_folder)
 
    print("DONE!")
    
#===============================================================================
#    ''' gt'''
#    rule_files = gt_rule_file
#    seed = 3
#    random.seed(seed)
#    for dt in display_type:
#        for sd in range(ite_num):
#            #print(sd)
#            #print(rule_files[display_type.index(dt)])
#            #load_rule_file(sd, rule_files[display_type.index(dt)])
#            random_rule = 'rules/yx_wind_turbine_labeling_color-bh_edited_bin{}.cga'.format(random.randint(0,19))
#            print(random_rule)
#            load_rule_file(sd, random_rule)
#            parent_folder = 'synthetic_wind_turbine_images'
#            print(parent_folder)
#            #gt      
#            take_gt_images(dt, sd, start_axis, end_axis, parent_folder=parent_folder)
#             
#===============================================================================

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
import csv
# get a CityEngine instance
ce = CE()
TileSize=608
Resolution = 1
#TileSize=8824
STEP = Resolution * TileSize

def get_turbine_scales(file_path):
    turbine_scales = []
    with open(ce.toFSPath(file_path)) as csvfile:
        csvreader = csv.reader(csvfile)
        for i, row in enumerate(csvreader):
            if i == 0:
                continue
            turbine_scales.append(float(row[0]))

    return turbine_scales

def dynamic_attributes(adjust_list, params, dynamic_range, mode):
    '''
    adjust_list: a list of strings
    params: a dictionary has the form
        {'p90deg', prob_camera_90_deg: float between 0~1,
        'ce', camera_elevation_angle: number between 0~90,
        'ca', camera_azimuth_angle: number between 0~360,
        'le', light_elevation_angle: number between 0~90,
        'la', light_azimuth_angle: number between 0~360,
        'li', light_instensity: float between 0~1,
        'ai', ambient_intensity: float between 0~1,
        'sa', shadow_attenuation: float between 0~1,}
    dynamic_range: a dictionary has the form
        {'ce': int, 'ca': int, 'la': int, 'li': int, 'ai': int, 'sa': int}
        The value  will vary in range of [sv-dv, sv+dv]
    '''
    prob_camera_90_deg = params['p90deg']
    camera_elevation_angle = params['ce']
    camera_azimuth_angle = params['ca']
    light_elevation_angle = params['le']
    light_azimuth_angle = params['la']
    light_intensity = params['li']
    ambient_intensity = params['ai']
    shadow_attenuation = params['sa']
    lightSettings = ce.getLighting()

    assert ('ce' in adjust_list) or ('ca' in adjust_list) or ('la' in adjust_list) or ('la' in adjust_list) \
        or ('li' in adjust_list) or ('ai' in adjust_list) or ('sa' in adjust_list), "Please select an attribute to augment"

    # calculate camera angles
    if random.uniform(0, 1) < prob_camera_90_deg:
        camera_elevation_angle = '-90'
        camera_azimuth_angle = '-90'
    else:
        if 'ce' in adjust_list:
            camera_elevation_angle = camera_elevation_angle + random.randint(-dynamic_range['ce'], dynamic_range['ce'])
            camera_elevation_angle = '-' + str(camera_elevation_angle)
        if 'ca' in adjust_list:
            camera_azimuth_angle = camera_azimuth_angle + random.randint(-dynamic_range['ca'], dynamic_range['ca'])
            camera_azimuth_angle = '-' + str(camera_azimuth_angle)
    
    # adjust lighting
    if 'le' in adjust_list:
        light_elevation_angle = light_elevation_angle + random.randint(-dynamic_range['le'], dynamic_range['le'])
        lightSettings.setSolarElevationAngle(light_elevation_angle)
    if 'la' in adjust_list:
        light_azimuth_angle = light_azimuth_angle + random.randint(-dynamic_range['la'], dynamic_range['la'])
        lightSettings.setSolarAzimuthAngle(light_azimuth_angle)
    if 'li' in adjust_list:
        light_intensity = min(1, light_intensity + 0.1 * random.randint(-int(10*dynamic_range['li']), int(10*dynamic_range['li'])))
        lightSettings.setSolarIntensity(light_intensity)
    if 'ai' in adjust_list:
#        ambient_intensity = min(1, ambient_intensity + 0.1 * random.randint(-int(10*dynamic_range['ai']), int(10*dynamic_range['ai'])))
        lightSettings.setAmbientIntensity(ambient_intensity)
    if 'sa' in adjust_list:
#        shadow_attenuation = min(1,  + 0.1 * random.randint(-int(10*dynamic_range['sa']), int(10*dynamic_range['sa'])))
        lightSettings.setShadowAttenuation(shadow_attenuation)

    ce.setLighting(lightSettings)

    return (camera_elevation_angle, camera_azimuth_angle)

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
    d = tile_width * resolution #pixel width of tile * resolution in m/pixel
    return str(d / (2*math.tan(FOV/2)))

'''
camera angle position offset helper functions
'''
def calculate_camera_pos_scale(elevation_angle):
    elevation_angle_int = abs(int(elevation_angle))
    max_elevation = 90.0
    min_elevation = 60.0
    scale_at_min_elevation = 0.70
    return (elevation_angle_int-min_elevation) / (max_elevation-min_elevation) * 1.0 \
        + (max_elevation-elevation_angle_int) / (max_elevation-min_elevation) * scale_at_min_elevation

def adjust_camera_i(i, elevation_angle, height, scale):
    elevation_angle_int = abs(int(elevation_angle))
    # increased offset due to parallax
    max_elevation = 90.0
    min_elevation = 60.0
    offset_at_min_elevation = 30.0
    offset = int((elevation_angle_int-min_elevation) / (max_elevation-min_elevation) * 0 \
        + (max_elevation-elevation_angle_int) / (max_elevation-min_elevation) * offset_at_min_elevation)

    
    return int(scale * i) - int(float(height)/math.tan(math.radians(elevation_angle_int))) - offset

def adjust_camera_j(j, scale):
    return scale * j

'''
master function
'''
def importFbxCamera(fbxfile, axis, angles, height):
    elevation_angle, azimuth_angle = angles
    scale = calculate_camera_pos_scale(elevation_angle)
    new_i = adjust_camera_i(axis[0], elevation_angle, height, scale)
    new_j = adjust_camera_j(axis[1], scale)
    data = parseFbxCam(fbxfile)

    if(data[0] and data[1]) :
        data[0][0] = str(new_i)
        data[0][1] = height
        data[0][2] = str(new_j)
        data[1][0] = elevation_angle
        data[1][1] = azimuth_angle
        v = setCamData(data)
#        print "Camera set to "+str(data)
        return v
    else:
        print("No camera data found in file "+str(fbxfile))

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
                                     adjust_list = ['ce', 'ca', 'la', 'li', 'ai', 'sa'],
                                     params={'p90deg': 0.5, 'ce': 75, 'ca': 90, 'le': 50, 'la': 90, 'li': 1.0,'ai': 1.0, 'sa': 0.4},
                                     dynamic_range={'ce':15, 'ca': 0.0, 'le': 0, 'la': 270, 'li': 0.0, 'ai': 0.0, 'sa': 0.0},
                                     mode='RGB', folder_name='test'):

    counter = 0
    # print('Start Shooting!')
    camfile = ce.toFSPath("data/camera.fbx") 
#    height = setCamHeight(tile_width=TileSize)
    height = 2500
    # print("height: {}".format(height))
    camera_angles = dynamic_attributes(adjust_list, params, dynamic_range, mode)
    # print("angle: {}".format(camera_angles))
    # print('taking capture of ', start_axis[0], end_axis[0], STEP)
    
    for i in drange(start_axis[0], end_axis[0], STEP): # x
        for j in drange(start_axis[1], end_axis[1], STEP): # z

            view = importFbxCamera(camfile, (i, j), camera_angles, height)
            # print('i, j ', i, j)
            counter += 1
            # print(counter)
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
def load_rule_file(seed, rule_file_path, params=None):
#    ge_models = ce.getObjectsFrom(ce.scene, ce.isModel)
#    ce.cleanupShapes(ge_models)
    all_shapes = ce.getObjectsFrom(ce.scene, ce.isShape)
    ce.setSeed(all_shapes, seed)
    if params:
        for attr, value in params.items():
            ce.setAttribute(all_shapes, attr, value)
    ce.setRuleFile(all_shapes, rule_file_path)
    ce.generateModels(all_shapes)
    ce.waitForUIIdle()
    time.sleep(1)
    # print('load rules ok')
    
'''
###############-----------------------------> RGB
'''   
def take_rgb_images(dt, sd, start_axis, end_axis, mode = 'RGB', parent_folder='', camera_angle=90):
    # print('start')
    start_time = time.time()
    tag='NE_wnd_sd{}'.format(sd) 
    folder_name='{}/{}_all_images_step{}'.format(parent_folder, dt, STEP)  
    if not os.path.exists(os.path.join(ce.toFSPath('images/'), folder_name)):
        os.makedirs(os.path.join(ce.toFSPath('images/'), folder_name))
    
#        shutil.rmtree(ce.toFSPath('images/{}'.format(folder_name)))
    '''# ORGINAL'''
    loop_capturer_dynamic_attributes(start_axis=start_axis, end_axis=end_axis,
                                 tag=tag, mode=mode, folder_name=folder_name,)
    # print('Duration: {}'.format(time.time()-start_time)) 
    
'''
###############-----------------------------> GT
why for Francisco the color GT and the texture GT not consistent?????????
'''   
def take_gt_images(dt, sd, start_axis, end_axis, mode = 'GT', parent_folder='', camera_angle=90):
    
    # print('start')
    start_time = time.time()
    tag='NE_wnd_sd{}'.format(sd) 
    folder_name='{}/{}_all_annos_step{}'.format(parent_folder, dt, STEP)  
    if not os.path.exists(os.path.join(ce.toFSPath('images/'), folder_name)):
        os.makedirs(os.path.join(ce.toFSPath('images/'), folder_name))
#        print('remove')
#        shutil.rmtree(ce.toFSPath('images/{}'.format(folder_name)))
#    print('removed')
    '''# ORGINAL'''
    loop_capturer_dynamic_attributes(start_axis=start_axis, end_axis=end_axis,
                                 tag=tag, mode=mode, folder_name=folder_name)
    # print('Duration: {}'.format(time.time()-start_time)) 
    
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
    print('starting...')
    
    display_type = ['color'] #, 'mixed'
    rgb_rule_file = 'rules/yx_wind_turbine_color-bh_edited.cga'
    gt_rule_file = 'rules/yx_wind_turbine_labeling_color-bh_edited.cga'
    start_axis=(-304, -304)
    end_axis=(305, 305)

    name = 'EM'
    # ite_num = 2 
    ite_num = len(os.listdir(ce.toFSPath('maps/EM')))
    print('Found {} input images'.format(ite_num))

    parent_folder = 'synthetic_wind_turbine_images/mar26_{}'.format(name)
    print('saving outputs to {}'.format(parent_folder))
    
    turbine_sizes = get_turbine_scales('data/scale_bins.csv')
    
    # ''' rgb'''
    rule = rgb_rule_file
    seed = 3
    random.seed(seed)
    
    try:
        for dt in display_type:
            for sd in range(ite_num):
                scale_bin_idx = random.randint(0, len(turbine_sizes)-2)
                print('Image {}, Turbine size bin {}'.format(sd, scale_bin_idx))
                params = {'LenMinModelFW' : turbine_sizes[scale_bin_idx], 
                            'LenMaxModelFW' : turbine_sizes[scale_bin_idx + 1]}
                load_rule_file(sd, rule, params)
                # rgb
                take_rgb_images(dt, sd, start_axis, end_axis, parent_folder=parent_folder)
    except:
        print('Exited')
#   print("DONE!")
    
#===============================================================================
#    ''' gt'''
#    rule_files = gt_rule_file
#    seed = 3
#    random.seed(seed)
#    for dt in display_type:
#        for sd in range(ite_num):  
#            turbine_size_params = {'LenMinModelFW' : 20, 'LenMaxModelFW' : 20}
#            rule = 'rules/yx_wind_turbine_labeling_color-bh_edited.cga'
#            load_rule_file(sd, rule, turbine_size_params)
#            parent_folder = 'synthetic_wind_turbine_images'
#            take_gt_images(dt, sd, start_axis, end_axis, parent_folder=parent_folder)
#             
#===============================================================================

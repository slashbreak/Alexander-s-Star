import pyglet
from pyglet.gl import *
from pyglet.window import key
import random
from math import pi, sin, cos
from euclid import *
import copy
rand = random.random()
PHI = (1.0 + math.sqrt(5.0)) / 2.0

keys = key.KeyStateHandler()
fps_display = pyglet.clock.get_fps()
#newfile = 'tree.png'
newfile = 'tree6.jpg'
tree_stream = open(newfile, 'rb')
tree = pyglet.image.load(newfile, file=tree_stream)
texture = tree.get_texture()
sprite = pyglet.sprite.Sprite(tree)
rotate_sound = [
    pyglet.resource.media('rotate1.wav', streaming=False),
    pyglet.resource.media('rotate2.wav', streaming=False),
    pyglet.resource.media('rotate3.wav', streaming=False),
    pyglet.resource.media('rotate4.wav', streaming=False),
]
try:
    # Try and create a window with multisampling (antialiasing)
    config = Config(sample_buffers=1, samples=4,
                    depth_size=16, double_buffer=True)
    window = pyglet.window.Window(resizable=True, config=config)
except pyglet.window.NoSuchConfigException:
    # Fall back to no multisampling for old hardware
    print ("failed to multisample")
    window = pyglet.window.Window(resizable=True)

# Init camera globals
camera_pos = Vector3(0, 0, 1)
camera_rot = Quaternion()
right   = Vector3(1, 0, 0)
up      = Vector3(0, 1, 0)
forward = Vector3(0, 0, 1)
camera_right   = Vector3(1, 0, 0)
camera_up      = Vector3(0, 1, 0)
camera_forward = Vector3(0, 0, 1)

# Init face index globals
star_draw = True # erm, referenced throughout, but never changed. might have use for gamestates.
auto_rotate = False # screensaver mode?
is_rotating = False # are we currently animating?
rx = ry = rz = 0
star_index = 1 # probably overused throughout the program, but this tell us which set of triangles we are currently on top of/ready to rotate.

theta = 0
rotate_increase_rads = 0.090 # this value is added to theta every tick. 2pi/5 rads is one rotation.

tri_group_original = [
    [[0,4],[3,7],[6,10],[9,13],[12,1]],
    [[7,3],[5,16],[15,57],[59,29],[28,8]],
    [[37,33],[35,49],[48,21],[23,53],[52,38]],
    [[33,37],[36,40],[39,43],[42,31],[30,34]],
    [[49,35],[34,30],[32,46],[45,18],[20,50]],
    [[4,0],[2,19],[18,45],[47,17],[16,5]],
    [[26,56],[55,41],[40,36],[38,52],[51,24]],
    [[56,26],[25,11],[10,6],[8,28],[27,54]],
    [[41,55],[54,27],[29,59],[58,44],[43,39]],
    [[17,47],[46,32],[31,42],[44,58],[57,15]],
    [[13,9],[11,25],[24,51],[53,23],[22,14]],
    [[19,2],[1,12],[14,22],[21,48],[50,20]]
]

#possible issues with rotation stack -- trying to change star_index while rotating will cause bugs
#because star_index is used throughout as a guide for where to draw AND update. consider refactoring.
rotation_stack = [] # add pairs of form [starindex,direction]
tri_group = copy.deepcopy(tri_group_original)
# CYCLE TRIANGLE LIST INDEX ---------------------
def rotate_triangle(triangleList, direction):
    if direction == 0: #anti clockwise
        triangleList.insert(0,triangleList.pop())
    elif direction == 1: # clockwise
        triangleList.append(triangleList[0])
        triangleList.pop(0)
    else:
        print ("bad direction")
    return triangleList
# ===============================================
def star(x):
    global star_index # index of iso_verts, for section highlighting
    star_index += x
    if star_index < 0:
        star_index = len(iso_verts)-1
    elif star_index > len(iso_verts)-1:
        star_index = 0

#we will compare by colour value only, so equality will occur when we 
#switch between modes where shuffled triangles are now the same colour    
def is_solved():
    return face_color == new_face_color
   
@window.event
def on_key_press(symbol, modifiers):
    global star_index 
    global star_draw
    global auto_rotate
    global rx, ry, rz
    global angle
    global rotation_stack
    # GAME COLOUR MODE SELECT------------------------------------------
    if symbol == key._1:
        color_1()
        new_face_color = copy.deepcopy(face_color)
        startemp = star_index
        for i in range(len(iso_verts)):
            star_index = i
            update_tri()
        star_index = startemp
        
    if symbol == key._2:
        color_6()
        new_face_color = copy.deepcopy(face_color)
        startemp = star_index
        for i in range(len(iso_verts)):
            star_index = i
            update_tri()
        star_index = startemp

    if symbol == key._3:
        color_12()
        new_face_color = copy.deepcopy(face_color)
        startemp = star_index
        for i in range(len(iso_verts)):
            star_index = i
            update_tri()
        star_index = startemp
    # ================================================================
        
    if symbol == key._0: 
        auto_rotate = True
    if symbol == key._9:
       # rx = 0
        auto_rotate = False
    # ROTATE animation ------------------------------
    global is_rotating
    if symbol == key.B:
        is_rotating = True
    if symbol == key.N:
        is_rotating = False
    # ================================================
        
    # Q and E change the star index ------------------------------------   
    if symbol == key.Q:
        if not is_rotating:
            star(-1)
        print (star_index)
    if symbol == key.E:
        if not is_rotating:
            star(1)
        print (star_index)
    # ===================================================================
    # PIECE ROTATION -------------------------------------------------
    # C and Z rotate around the star index   
    if symbol == key.C:
        if not is_rotating:
            is_rotating = True
            rotation_stack.append([star_index,1])
            
            rotate_sound[int(random.randrange(4))].play()
            #print is_solved()
    if symbol == key.Z:
        if not is_rotating:
            is_rotating = True
            rotation_stack.append([star_index,0])
            #tri_group[star_index] = rotate_triangle(tri_group[star_index], 0)
            #update_tri()
            rotate_sound[int(random.randrange(4))].play()
            #print is_solved()
    # ==================================================================
        
@window.event
def on_key_release(symbol, modifiers):
    pass
  
def update(dt):
    global rx 
    global ry 
    global rz
    global camera_pos
    global camera_rot
    global camera_right
    global camera_up
    global camera_forward
    global theta
    global rotation_stack
    global rotate_increase_rads
    # zoom
    if keys[key.S]:
        #print ("s")
        camera_dir = camera_forward
        camera_dir = camera_dir.normalized()
        camera_pos -= camera_dir
        
    if keys[key.W]:
        camera_dir = camera_forward
        camera_dir = camera_dir.normalized()
        camera_pos += camera_dir

    # rotate Alex
    if keys[key.LEFT]:
        q = Quaternion.new_rotate_axis(-.05, camera_up)
        camera_rot = q * camera_rot
    if keys[key.RIGHT]:
        q = Quaternion.new_rotate_axis( .05, camera_up)
        camera_rot = q * camera_rot
    if keys[key.UP]:
        q = Quaternion.new_rotate_axis(-.05, camera_right)
        camera_rot = q * camera_rot
    if keys[key.DOWN]:
        q = Quaternion.new_rotate_axis( .05, camera_right)
        camera_rot = q * camera_rot
    if keys[key.A]:
        q = Quaternion.new_rotate_axis( .05, camera_forward)
        camera_rot = q * camera_rot
    if keys[key.D]:
        q = Quaternion.new_rotate_axis(-.05, camera_forward)
        camera_rot = q * camera_rot
    #handle the rotate keys being pressed, but account for direction in the draw method
    #remember that a _positive theta_ will rotate anticlockwise
    global is_rotating
    if is_rotating:
        theta = theta + rotate_increase_rads
    #stop rotation after we reach a 1/5 turn 
    if theta > (2*pi/5):
        theta = 0
        tempPair = rotation_stack.pop()
        tri_group[tempPair[0]] = rotate_triangle(tri_group[tempPair[0]], tempPair[1])
        update_tri()
        is_rotating = False
    rx += .05
    ry += .05
    rz += .05
    rx %= 360
    ry %= 360
    rz %= 360
#pyglet.clock.set_fps_limit(60)
pyglet.clock.schedule(update)
#pyglet.clock.schedule_interval_soft(update, 1.0/60.0)
      
@window.event
def on_resize(width,height):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(95.,float(window.width)/window.height, .1, 100.)
    glMatrixMode(GL_MODELVIEW)
    return pyglet.event.EVENT_HANDLED
    
@window.event
def on_show():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_CULL_FACE)
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluPerspective(95.0,float(window.width)/window.height*0.5, 0.1, 100.0)
    return pyglet.event.EVENT_HANDLED

#start with an icosohedron
verts = [
    [-1.0, PHI, 0], #0
    [1.0, PHI, 0],  #1
    [-1.0, -PHI, 0],#2
    [1.0, -PHI, 0], #3
    [0, -1.0, PHI], #4
    [0, 1.0, PHI],  #5
    [0, -1.0, -PHI],#6
    [0, 1.0, -PHI], #7
    [PHI, 0, -1.0], #8
    [PHI, 0, 1.0],  #9
    [-PHI, 0, -1.0],#10
    [-PHI, 0, 1.0]  #11
] 
iso_verts = copy.deepcopy(verts)
iso_index = [    
    [0, 11, 5],
    [0, 5, 1],
    [0, 1, 7],
    [0, 7, 10],
    [0, 10, 11],

    [1, 5, 9],
    [5, 11, 4],
    [11, 10, 2],
    [10, 7, 6],
    [7, 1, 8],

    [3, 9, 4],
    [3, 4, 2],
    [3, 2, 6],
    [3, 6, 8],
    [3, 8, 9],

    [4, 9, 5],
    [2, 4, 11],
    [6, 2, 10],
    [8, 6, 7],
    [9, 8, 1]    
]

index_len = len(iso_index)
vert_len = len(verts)
new_index = []
face_normals = []*60

#split isocohedron into great dodecahedron
for i in iso_index:
    v1 = [ verts[i[0]][0], verts[i[0]][1], verts[i[0]][2] ]
    v2 = [ verts[i[1]][0], verts[i[1]][1], verts[i[1]][2] ]
    v3 = [ verts[i[2]][0], verts[i[2]][1], verts[i[2]][2] ]
    
    #create new vert in the centre of the face, *0.75 for indentation
    new_vert = [
        ( (v1[0] + v2[0] + v3[0]) / 3.0 * 0.75),
        ( (v1[1] + v2[1] + v3[1]) / 3.0 * 0.75),
        ( (v1[2] + v2[2] + v3[2]) / 3.0 * 0.75)
    ]
    # add new vert to list, increase vert index length
    verts.append(new_vert)
    vert_len += 1
    i_new = vert_len-1
 
    # add new indices to a new array
    new_index.append((i[0], i_new, i[2]))
    new_index.append((i[0], i[1], i_new))
    new_index.append((i_new, i[1], i[2]))
   
# face colours
#red = [1.0, 0.0, 0.0]
blue = [0.04, 0.02, 0.80]
#green = [0.0, 0.4, 0.2]
white = [1, 1, 1]
yellow = [0.59, 0.59, 0.09]
#magenta = [1.0, 0.0, 1.0]
dark_green = [0.05,0.2,0.1]
dark_red = [0.55,0.0,0.0]
#purple = [0.2,0.0,0.4]
#cyan = [0.6,0.8,0.9]
orange = [0.79, 0.39, 0.1]
#pink = [1.0,0.8,1.0]
#black = [0,0,0]

# mild 6 colour test
#blue = [0.24, 0.2, 0.45]
#dark_green = [0.347,0.347,0.187]
#dark_red = [0.62, 0.61, 0.42]
white = [1.0, 1.0, 1.0]
orange = [0.76, 0.4, 0.1]
#yellow = [0.547, 0.849, 0.51]

red = [1.0, 0.1, 0.2]
magenta = [1.0, 0.2, 0.6]
purple = [0.2,0.0,0.4]
cyan = [0.6,0.8,0.9]
green = [0.0, 0.4, 0.2]
pink = [1.0,0.8,1.0]
black = [0,0,0]

#initial face colouring
face_color = [black]*len(new_index)

#region colours
def color_1():
    face_color[25] = white
    face_color[37] = white
    face_color[39] = white
    face_color[53] = white
    face_color[54] = white
    face_color[1] = white
    face_color[3] = white
    face_color[15] = white
    face_color[20] = white
    face_color[46] = white

    face_color[0] = white
    face_color[13] = white
    face_color[18] = white
    face_color[23] = white
    face_color[49] = white
    face_color[28] = white
    face_color[40] = white
    face_color[42] = white
    face_color[56] = white
    face_color[57] = white

    face_color[2] = white
    face_color[5] = white
    face_color[8] = white
    face_color[11] = white
    face_color[14] = white
    face_color[32] = white
    face_color[35] = white
    face_color[38] = white
    face_color[41] = white
    face_color[44] = white

    face_color[4] = white
    face_color[6] = white
    face_color[17] = white
    face_color[27] = white
    face_color[58] = white
    face_color[22] = white
    face_color[34] = white
    face_color[36] = white
    face_color[50] = white
    face_color[51] = white

    face_color[7] = white
    face_color[9] = white
    face_color[24] = white
    face_color[29] = white
    face_color[55] = white
    face_color[19] = white
    face_color[31] = white
    face_color[33] = white
    face_color[47] = white
    face_color[48] = white

    face_color[16] = dark_green
    face_color[30] = dark_green
    face_color[43] = dark_green
    face_color[45] = dark_green
    face_color[59] = dark_green
    face_color[10] = white
    face_color[12] = white
    face_color[21] = white
    face_color[26] = white
    face_color[52] = white
    
def color_12():
    face_color[25] = red
    face_color[37] = red
    face_color[39] = red
    face_color[53] = red
    face_color[54] = red
    face_color[1] = blue
    face_color[3] = blue
    face_color[15] = blue
    face_color[20] = blue
    face_color[46] = blue

    face_color[0] = white
    face_color[13] = white
    face_color[18] = white
    face_color[23] = white
    face_color[49] = white
    face_color[28] = pink
    face_color[40] = pink
    face_color[42] = pink
    face_color[56] = pink
    face_color[57] = pink

    face_color[2] = orange
    face_color[5] = orange
    face_color[8] = orange
    face_color[11] = orange
    face_color[14] = orange
    face_color[10] = dark_green
    face_color[12] = dark_green
    face_color[21] = dark_green
    face_color[26] = dark_green
    face_color[52] = dark_green

    face_color[4] = yellow
    face_color[6] = yellow
    face_color[17] = yellow
    face_color[27] = yellow
    face_color[58] = yellow
    face_color[22] = cyan
    face_color[34] = cyan
    face_color[36] = cyan
    face_color[50] = cyan
    face_color[51] = cyan

    face_color[7] = magenta
    face_color[9] = magenta
    face_color[24] = magenta
    face_color[29] = magenta
    face_color[55] = magenta
    face_color[19] = purple
    face_color[31] = purple
    face_color[33] = purple
    face_color[47] = purple
    face_color[48] = purple

    face_color[16] = dark_red
    face_color[30] = dark_red
    face_color[43] = dark_red
    face_color[45] = dark_red
    face_color[59] = dark_red
    face_color[32] = green
    face_color[35] = green
    face_color[38] = green
    face_color[41] = green
    face_color[44] = green

def color_6():
    face_color[25] = blue
    face_color[37] = blue
    face_color[39] = blue
    face_color[53] = blue
    face_color[54] = blue
    face_color[1] = blue
    face_color[3] = blue
    face_color[15] = blue
    face_color[20] = blue
    face_color[46] = blue

    face_color[0] = white
    face_color[13] = white
    face_color[18] = white
    face_color[23] = white
    face_color[49] = white
    face_color[28] = white
    face_color[40] = white
    face_color[42] = white
    face_color[56] = white
    face_color[57] = white

    face_color[2] = orange
    face_color[5] = orange
    face_color[8] = orange
    face_color[11] = orange
    face_color[14] = orange
    face_color[32] = orange
    face_color[35] = orange
    face_color[38] = orange
    face_color[41] = orange
    face_color[44] = orange

    face_color[4] = yellow
    face_color[6] = yellow
    face_color[17] = yellow
    face_color[27] = yellow
    face_color[58] = yellow
    face_color[22] = yellow
    face_color[34] = yellow
    face_color[36] = yellow
    face_color[50] = yellow
    face_color[51] = yellow

    face_color[7] = dark_red
    face_color[9] = dark_red
    face_color[24] = dark_red
    face_color[29] = dark_red
    face_color[55] = dark_red
    face_color[19] = dark_red
    face_color[31] = dark_red
    face_color[33] = dark_red
    face_color[47] = dark_red
    face_color[48] = dark_red

    face_color[16] = dark_green
    face_color[30] = dark_green
    face_color[43] = dark_green
    face_color[45] = dark_green
    face_color[59] = dark_green
    face_color[10] = dark_green
    face_color[12] = dark_green
    face_color[21] = dark_green
    face_color[26] = dark_green
    face_color[52] = dark_green
color_6()

new_face_color = copy.deepcopy(face_color)

def update_tri():
    # first update index reference by updating the 5 sets from other indices which match the reverse
    # ie group 1's 0 index should match group 0's 1 index, reversed
    # pairs are hard-coded, so just trust that each index should update 5 other pairs
    if star_index == 0: 
        tri_group[5][0] = tri_group[star_index][0][::-1]
        tri_group[1][0] = tri_group[star_index][1][::-1]
        tri_group[7][2] = tri_group[star_index][2][::-1]
        tri_group[10][0] = tri_group[star_index][3][::-1]
        tri_group[11][0] = tri_group[star_index][4][::-1]
    elif star_index == 1:
        tri_group[0][1] = tri_group[star_index][0][::-1]
        tri_group[5][4] = tri_group[star_index][1][::-1]
        tri_group[9][4] = tri_group[star_index][2][::-1]
        tri_group[8][2] = tri_group[star_index][3][::-1]
        tri_group[7][3] = tri_group[star_index][4][::-1]
    elif star_index == 2:
        tri_group[3][0] = tri_group[star_index][0][::-1]
        tri_group[4][0] = tri_group[star_index][1][::-1]
        tri_group[11][3] = tri_group[star_index][2][::-1]
        tri_group[10][3] = tri_group[star_index][3][::-1]
        tri_group[6][3] = tri_group[star_index][4][::-1]
    elif star_index == 3:
        tri_group[2][0] = tri_group[star_index][0][::-1]
        tri_group[6][2] = tri_group[star_index][1][::-1]
        tri_group[8][4] = tri_group[star_index][2][::-1]
        tri_group[9][2] = tri_group[star_index][3][::-1]
        tri_group[4][1] = tri_group[star_index][4][::-1]
    elif star_index == 4:
        tri_group[2][1] = tri_group[star_index][0][::-1]
        tri_group[3][4] = tri_group[star_index][1][::-1]
        tri_group[9][1] = tri_group[star_index][2][::-1]
        tri_group[5][2] = tri_group[star_index][3][::-1]
        tri_group[11][4] = tri_group[star_index][4][::-1]
    elif star_index == 5:
        tri_group[0][0] = tri_group[star_index][0][::-1]
        tri_group[11][0] = tri_group[star_index][1][::-1]
        tri_group[4][3] = tri_group[star_index][2][::-1]
        tri_group[9][0] = tri_group[star_index][3][::-1]
        tri_group[1][1] = tri_group[star_index][4][::-1]
    elif star_index == 6:
        tri_group[7][0] = tri_group[star_index][0][::-1]
        tri_group[8][0] = tri_group[star_index][1][::-1]
        tri_group[3][1] = tri_group[star_index][2][::-1]
        tri_group[2][4] = tri_group[star_index][3][::-1]
        tri_group[10][2] = tri_group[star_index][4][::-1]
    elif star_index == 7:
        tri_group[6][0] = tri_group[star_index][0][::-1]
        tri_group[10][1] = tri_group[star_index][1][::-1]
        tri_group[0][2] = tri_group[star_index][2][::-1]
        tri_group[1][4] = tri_group[star_index][3][::-1]
        tri_group[8][1] = tri_group[star_index][4][::-1]
    elif star_index == 8:
        tri_group[6][1] = tri_group[star_index][0][::-1]
        tri_group[7][4] = tri_group[star_index][1][::-1]
        tri_group[1][3] = tri_group[star_index][2][::-1]
        tri_group[9][3] = tri_group[star_index][3][::-1]
        tri_group[3][2] = tri_group[star_index][4][::-1]
    elif star_index == 9:
        tri_group[5][3] = tri_group[star_index][0][::-1]
        tri_group[4][2] = tri_group[star_index][1][::-1]
        tri_group[3][3] = tri_group[star_index][2][::-1]
        tri_group[8][3] = tri_group[star_index][3][::-1]
        tri_group[1][2] = tri_group[star_index][4][::-1]
    elif star_index == 10:
        tri_group[0][3] = tri_group[star_index][0][::-1]
        tri_group[7][1] = tri_group[star_index][1][::-1]
        tri_group[6][4] = tri_group[star_index][2][::-1]
        tri_group[2][3] = tri_group[star_index][3][::-1]
        tri_group[11][2] = tri_group[star_index][4][::-1]
    elif star_index == 11:
        tri_group[5][1] = tri_group[star_index][0][::-1]
        tri_group[0][4] = tri_group[star_index][1][::-1]
        tri_group[10][4] = tri_group[star_index][2][::-1]
        tri_group[2][2] = tri_group[star_index][3][::-1]
        tri_group[4][4] = tri_group[star_index][4][::-1]
    else:
        print ("Couldn't update index triangles")
   
    # update each index's face colour with respect to the current position of each triangle pair
    new_face_color[tri_group_original[star_index][0][0]] = face_color[tri_group[star_index][0][0]]
    new_face_color[tri_group_original[star_index][0][1]] = face_color[tri_group[star_index][0][1]]   
    new_face_color[tri_group_original[star_index][1][0]] = face_color[tri_group[star_index][1][0]]
    new_face_color[tri_group_original[star_index][1][1]] = face_color[tri_group[star_index][1][1]] 
    new_face_color[tri_group_original[star_index][2][0]] = face_color[tri_group[star_index][2][0]]
    new_face_color[tri_group_original[star_index][2][1]] = face_color[tri_group[star_index][2][1]] 
    new_face_color[tri_group_original[star_index][3][0]] = face_color[tri_group[star_index][3][0]]
    new_face_color[tri_group_original[star_index][3][1]] = face_color[tri_group[star_index][3][1]]
    new_face_color[tri_group_original[star_index][4][0]] = face_color[tri_group[star_index][4][0]]
    new_face_color[tri_group_original[star_index][4][1]] = face_color[tri_group[star_index][4][1]]        
        
def calculate_normal(i):
    v1 = Vector3(verts[i[0]][0], verts[i[0]][1], verts[i[0]][2])
    v2 = Vector3(verts[i[1]][0], verts[i[1]][1], verts[i[1]][2])
    v3 = Vector3(verts[i[2]][0], verts[i[2]][1], verts[i[2]][2])
    u = v2 - v1
    v = v3 - v1
    n = u.cross(v)
    n = n.normalize()
    return n
    
@window.event
def on_draw():
    global p2aa, p2bb, p2cc
    window.clear()
    
    #temporary bgcolor for solved/unsolved state
    if is_solved():
        glClearColor(0.85,0.9,0.8,1)
    else:
        glClearColor(.9,.5,.5,1)
        
    glClearColor(1,1,1,1)    
    glEnable(GL_LIGHTING)    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)  
    to_ortho()
    #glTranslatef(10,10,0)
    #fps_display.draw()
    #sprite.draw()
    from_ortho()
    glMatrixMode(GL_PROJECTION)
    
    glLoadIdentity()
    gluPerspective(10.0,float(window.width)/window.height, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    
    glShadeModel(GL_SMOOTH)
    
    glEnable( GL_BLEND )
    
    glEnable(GL_COLOR_MATERIAL)
    glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA )
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    #glFrontFace( GL_CCW )
    # Hints
    
    
    
    glEnable(GL_LIGHT0) 
    glEnable(GL_LIGHT1) 
    def vec(*args):
        return (GLfloat * len(args))(*args)

    glLightfv(GL_LIGHT0, GL_POSITION, vec(0, 0, -5, 1))
    glLightfv(GL_LIGHT0, GL_AMBIENT, vec(.1,.1,.1,1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, vec(.9, .9, .9, 1))
    #glLightfv(GL_LIGHT0, GL_SPECULAR, vec(.8, .8, .6, 1))

    
    #glLightfv(GL_LIGHT1, GL_POSITION, vec(-5, 0, -5, 1))
    #glLightfv(GL_LIGHT1, GL_DIFFUSE, vec(.4, .4, .8, 1))
    #glLightfv(GL_LIGHT1, GL_AMBIENT, vec(.1,.1,.1,1))
    #glLightfv(GL_LIGHT1, GL_SPECULAR, vec(.1, .1, .6, 1))

    #glDisable(GL_COLOR_MATERIAL)
    #glMaterialfv(GL_FRONT, GL_AMBIENT, vec(.2, .2, 0.2, 1)) 
    #glMaterialfv(GL_FRONT, GL_DIFFUSE, vec(.3, .3, 0.3, 1)) 
    glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, vec(.2,.2,.2,1))
    glMaterialfv(GL_FRONT, GL_SPECULAR, vec(.14,.14,.24,1))
    glMaterialf(GL_FRONT, GL_SHININESS, 10)
    #glLoadIdentity()
    camera()
    #glEnable(GL_BLEND)
    
    for j, i in enumerate(new_index):        

    

        #BEGIN fill faces --------------------------------------------------------------
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glEnable( GL_POLYGON_OFFSET_FILL );     
        glPolygonOffset( 1, 1 )
        #from point import Vector3
        #add this if around glBegin/End to only draw the selected face
        glEnable(GL_TEXTURE_2D);
        glBindTexture(texture.target, texture.id)
        if is_rotating:
            global rotation_stack, theta
            if not star_index in i:
            #if not (i[0] == star_index or i[1] == star_index or i[2] == star_index):
                glBegin(GL_TRIANGLES)
                glColor4f(new_face_color[j][0], new_face_color[j][1], new_face_color[j][2], 1.0)
                normal = calculate_normal(i)
                glNormal3f(normal.x, normal.y, normal.z)
                
                glTexCoord2f(0.0, 0.0);
                glVertex3f(verts[i[0]][0], verts[i[0]][1], verts[i[0]][2])
                glTexCoord2f(1, 0.0);
                glVertex3f(verts[i[1]][0], verts[i[1]][1], verts[i[1]][2])
                glTexCoord2f(1.0, 1.0);
                glVertex3f(verts[i[2]][0], verts[i[2]][1], verts[i[2]][2])
                glEnd()
            else:
                #now we rotate the remaining verts
                
                p2 = Vector3(verts[star_index][0], verts[star_index][1], verts[star_index][2])
                p1 = Vector3(0,0,0)
                p0a = Vector3(verts[i[0]][0], verts[i[0]][1], verts[i[0]][2])
                p0b = Vector3(verts[i[1]][0], verts[i[1]][1], verts[i[1]][2])
                p0c = Vector3(verts[i[2]][0], verts[i[2]][1], verts[i[2]][2])
                
                if rotation_stack[0][1] == 1:
                    #print rotation_stack[0][1]
                    thetanew = -theta
                else:
                    thetanew = theta
                
                p2aa = Vector3Rotate3D(p1, p2, p0a, thetanew)
                p2bb = Vector3Rotate3D(p1, p2, p0b, thetanew)
                p2cc = Vector3Rotate3D(p1, p2, p0c, thetanew)
                glBegin(GL_TRIANGLES)
                glColor4f(new_face_color[j][0], new_face_color[j][1], new_face_color[j][2], 1.0)
                # normalize half-rotated verts by themselves, because our main function doesn't work with it
                v1 = p2aa
                v2 = p2bb
                v3 = p2cc
                u = v2 - v1
                v = v3 - v1
                n = u.cross(v).normalize()
                
                normal = n
                glNormal3f(normal.x, normal.y, normal.z)
                glTexCoord2f(0.0, 0.0);
                glVertex3f(p2aa.x, p2aa.y, p2aa.z)
                glTexCoord2f(1, 0);
                glVertex3f(p2bb.x, p2bb.y, p2bb.z)
                glTexCoord2f(1, 1.0);
                glVertex3f(p2cc.x, p2cc.y, p2cc.z)
                glEnd()
                
        else:
            glBegin(GL_TRIANGLES)
            glColor4f(new_face_color[j][0], new_face_color[j][1], new_face_color[j][2], 1.0)
            normal = calculate_normal(i)
            glNormal3f(normal.x, normal.y, normal.z)
            glTexCoord2f(0.0, 0.0);
            glVertex3f(verts[i[0]][0], verts[i[0]][1], verts[i[0]][2])
            glTexCoord2f(1.0, 0);
            glVertex3f(verts[i[1]][0], verts[i[1]][1], verts[i[1]][2])
            glTexCoord2f(1, 1.0);
            glVertex3f(verts[i[2]][0], verts[i[2]][1], verts[i[2]][2])
            glEnd()
        
        #END fill faces -------------------------------------------------------------------
        #glDisable( GL_POLYGON_OFFSET_FILL )
        glDisable(GL_TEXTURE_2D);
        
        #BEGIN current star indicator ------------------------------------------------------
        glDisable(GL_LIGHTING)
                # wireframe -----------------------------------------------------------------
        glLineWidth(2.4)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        glEnable(GL_LINE_SMOOTH)
        glPolygonMode(GL_FRONT, GL_LINE)
        glEnable( GL_POLYGON_OFFSET_FILL )    
        
        #glPolygonOffset( 1, 1 )
        if star_draw:
            glBegin(GL_TRIANGLES)
            # draw active triangles to rotate
            if star_draw:
                if star_index in i:
                    
                    glColor4f(0, 0, 0, 1)
                    #glColor4f(1, 0, 1, 1)
                else:
                    glColor4f(0, 0, 0, 1.0)
            else:
                glColor4f(0 ,0, 0, 1.0)
            if not (star_index in i and is_rotating):
                glVertex3f(verts[i[0]][0], verts[i[0]][1], verts[i[0]][2])
                glVertex3f(verts[i[1]][0], verts[i[1]][1], verts[i[1]][2])
                glVertex3f(verts[i[2]][0], verts[i[2]][1], verts[i[2]][2])
            else:
                glVertex3f(p2aa.x, p2aa.y, p2aa.z)
                glVertex3f(p2bb.x, p2bb.y, p2bb.z)
                glVertex3f(p2cc.x, p2cc.y, p2cc.z)
            glEnd()
        #glDisable( GL_POLYGON_OFFSET_FILL )
        #END wireframe -----------------------------------------------------------------
        
        
        
        if star_draw:
            if star_index in i:
                #glDisable(GL_CULL_FACE)
                #glDisable(GL_DEPTH_TEST)
                glPointSize(20.0)
                #glEnable( GL_POINT_SMOOTH );
                #glEnable( GL_BLEND );
                #glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA );
                #glPolygonMode(GL_FRONT_AND_BACK, GL_POINT)
                glBegin(GL_POINTS)
                glColor4f(1,1,1, 1.0)
                
                glVertex3f(verts[star_index][0]*1.2, verts[star_index][1]*1.2, verts[star_index][2]*1.2)
                glEnd()
                
                glPointSize(30.0)
                glBegin(GL_POINTS)
                glColor4f(1,0,0, 1)
                
                glVertex3f(verts[star_index][0]*1.2, verts[star_index][1]*1.2, verts[star_index][2]*1.2)
                glEnd()
        glEnable(GL_LIGHTING)
        #END current star indicator -----------------------------------------------------------
    glDisable(GL_LIGHTING)
def to_ortho():
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, window.width, 0 , window.height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def from_ortho():
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    #glLoadIdentity()
def camera():
    angle, axis = camera_rot.get_angle_axis()
    
    glTranslatef(0, 0, -camera_pos.z - 20)
    if not auto_rotate:
        glRotatef(angle*180/pi, axis.x, axis.y, axis.z)
    else:
        glRotatef(rx*18/pi, axis.x, axis.y, axis.z)    # translate screen to camera position
        
"""
    Return a point rotated about an arbitrary axis in 3D.
    Positive angles are counter-clockwise looking down the axis toward the origin.
    The coordinate system is assumed to be right-hand.
    Arguments: 'axis point 1', 'axis point 2', 'point to be rotated', 'angle of rotation (in radians)' >> 'new point'
    Revision History:
        Version 1.01 (11/11/06) - Revised function code
        Version 1.02 (11/16/06) - Rewrote Vector3Rotate3D function

    Reference 'Rotate A Vector3 About An Arbitrary Axis (3D)' - Paul Bourke        
"""
def Vector3Rotate3D(p1, p2, p0, theta):
    
    from math import cos, sin, sqrt

    # Translate so axis is at origin    
    p = p0 - p1
    # Initialize point q
    q = Vector3(0.0,0.0,0.0)
    N = p2 - p1
    Nm = sqrt(N.x**2 + N.y**2 + N.z**2)
    
    # Rotation axis unit vector
    n = Vector3(N.x/Nm, N.y/Nm, N.z/Nm)

    # Matrix common factors     
    c = cos(theta)
    t = (1 - cos(theta))
    s = sin(theta)
    X = n.x
    Y = n.y
    Z = n.z

    # Matrix 'M'
    d11 = t*X**2 + c
    d12 = t*X*Y - s*Z
    d13 = t*X*Z + s*Y
    d21 = t*X*Y + s*Z
    d22 = t*Y**2 + c
    d23 = t*Y*Z - s*X
    d31 = t*X*Z - s*Y
    d32 = t*Y*Z + s*X
    d33 = t*Z**2 + c

    #            |p.x|
    # Matrix 'M'*|p.y|
    #            |p.z|
    q.x = d11*p.x + d12*p.y + d13*p.z
    q.y = d21*p.x + d22*p.y + d23*p.z
    q.z = d31*p.x + d32*p.y + d33*p.z

    # Translate axis and rotated point back to original location    
    return q + p1
    
    
window.push_handlers(keys)

pyglet.app.run()

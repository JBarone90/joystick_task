from psychopy import core
from psychopy import visual
from psychopy import monitors
from psychopy import gui
from psychopy import event
from psychopy import clock
from psychopy.hardware import joystick
import psychopy.tools.coordinatetools as ct
import numpy as np
import pandas as pd 
import random as rnd
import os
from math import radians

# MEG triggers
try:
    from pypixxlib.propixx import PROPixxCTRL
    pxctrl = PROPixxCTRL()
    px_out = pxctrl.dout
except ImportError:
    class dummy:
        def setBitValue(self, value=0, bit_mask=0xFF):
            pass

        def updateRegisterCache(self):
            pass
    pxctrl = dummy()
    px_out = dummy()

def trigger(bit, t):
    """
    triggers ProPixxControl
    returns trigger time, start and end of the function
    """
    start = core.getTime()
    wait = core.StaticPeriod()
    px_out.setBitValue(value=bit, bit_mask=0xFF)
    pxctrl.updateRegisterCache()
    wait.start(t)
    trig = core.getTime()
    wait.complete()
    px_out.setBitValue(value=0, bit_mask=0xFF)
    pxctrl.updateRegisterCache()
    end = core.getTime()
    return (trig, start, end)
""" 
Subj directories
""" 
# prompt
exp_info = {
    "ID": 0,
    "session": 1
}

prompt = gui.DlgFromDict(
    dictionary =exp_info, 
    title      ="Beta Burst Stop-Signal Task"
)

subject = exp_info["ID"]
session = exp_info["session"]
subj_ID = str(subject).zfill(4)

#CHANGE ME - Hard coded
subj_dir      = os.path.join("/Users/jacopobarone/Desktop/VS_code/psychopy/data/stop_signal_task/{}".format(subj_ID))
#output_dir    = "~\Desktop\joy_outputs" #saving dir 

if not os.path.exists(subj_dir):
    os.makedirs(subj_dir)
else:
    pass

data_filename = "ses{}_{}.csv".format(
    session,
    subj_ID,
)

joy_dir = os.path.join(subj_dir, data_filename[:-4])

if not os.path.exists(joy_dir):
    os.makedirs(joy_dir)
else:
    myDlg = gui.Dlg(title="This folder already exists")
    myDlg.addText('Risk of overwriting data! If you wish to continue press OK')
    ok_data = myDlg.show()  # show dialog 
    if myDlg.OK: #If OK continue
        pass
    else: #quit session
        print('User cancelled')
        core.quit()
""" 
Exp Info
""" 
#exp settings
Ntrial          = 310
stop_trial      = 100 
target_angle    = 45 
hidden_radius   = 10 
target_origin   = [0,0]
starting_radius = 1
scaling         = 12
fix_time        = .750
ready_time      = 1.5
go_time         = .750
ssd             = .2 #stop-signal delay
post_go_time    = 1.25 
ITI_bounds      = (.5, .75)
#initialize the random number generator
rnd.seed() 
#list of target postions in radians
angle_list      = [ radians(target_angle * i)  for i in np.arange(5) ] * int(Ntrial/5)
rnd.shuffle(angle_list) 

#list of GO-Stop trials
go_list = [1]*(Ntrial-stop_trial) + [0]*stop_trial
rnd.shuffle(go_list)

# data logging settings
columns = [
    "ID",
    "trial",
    "fix_dur",
    "ready_dur",
    "go_dur",
    "post_go_dur",
    "ITI_dur",
    "SSD",
    "target_angle",
    "GO/Stop",
    "start_mov",
    "full_mov"
]

data_dict = {i: [] for i in columns}

""" 
Exp windows and cues
""" 
#monitor settings
x230 = (34, 60, (1680, 1050)) #my mac
# x230 = (54, 60, (1920, 1080)) #cog labs
width, dist, res = x230 

mon = monitors.Monitor("default")
mon.setWidth(width)
mon.setDistance(dist)
mon.setSizePix(res)

exp_black   = "#000000"
exp_gray    = "#848484"

win = visual.Window(size=res,
                    color=exp_black,
                    fullscr=True,
                    allowGUI=False,
                    winType="pyglet",
                    units="deg",
                    monitor=mon)

#framerate info
framerate = win.getActualFrameRate(
    nIdentical=10,
    nMaxFrames=120,
    nWarmUpFrames=10,
    threshold=1
)
framerate_r = np.round(framerate)

#hardware settings
joystick.backend='pyglet'
joy = joystick.Joystick(0)

#blank sreen
blank = visual.TextStim(
    win,
    text=" ",
    opacity=0.0
)

#text & cues
text_stim = visual.TextStim(
    win,
    text="",
    color=exp_gray,
    pos = (-7,0),
    alignHoriz= 'left',
    height= 1.4
)

r = .6 #cues radius

target = visual.Circle(
    win, 
    r,
    edges=40,
    fillColor=None,
    lineColor="white",
)

cursor = visual.Circle(
    win, 
    r,
    edges=40,
    fillColor="white",
    lineColor="white",
)

"""
Exp starts here
""" 
#instruction
instructions = ['Press space bar to start']
for text in instructions:
    text_stim.text = text
    text_stim.draw()
    win.flip()
    event.waitKeys(
        keyList=["space"], 
        modifiers=False, 
        timeStamped=False
    )

blank.draw()
win.flip()

core.wait(5)

#start clock 
exp_clock = clock.MonotonicClock()
exp_start = exp_clock.getTime()

for trial in np.arange(Ntrial):

    if event.getKeys(keyList=['q'], timeStamped=False):
        break
         
    target.draw()
    win.flip()

    #don't start any trial unless joy pos is central    
    while True:

        x, y                    = joy.getX(), -joy.getY() 
        x                      *= scaling
        y                      *= scaling
        theta, radius           = ct.cart2pol(x, y, units="rad")

        if radius >= starting_radius: 
            text_stim.text      = "Release the joysitic"
            text_stim.pos       = (-6,0) 
            text_stim.height    = 1.5
            text_stim.draw()
            win.flip()
        else:
            break

    #empty list for storing data
    x_trial         = []
    y_trial         = []
    t_trial         = []
    #reset movement info
    start_mov       = 0 
    full_mov        = 0 

    #fixation - rest
    target.fillColor = None
    target.pos       = target_origin
    exp_fix_onset    = exp_clock.getTime()
    for frameN in np.arange(int(framerate_r * fix_time)):
    
        x, y             = joy.getX(), -joy.getY()
        x_trial.append(x)
        y_trial.append(y)
        t_trial.append(exp_clock.getTime()) 
        
        x               *= scaling
        y               *= scaling
        theta, radius    = ct.cart2pol(x, y, units="rad")

        cursor.pos       = ct.pol2cart(theta, radius, units="rad")
        
        target.draw()
        win.flip()

    #ready cue    
    exp_ready_onset = exp_clock.getTime()
    for frameN in np.arange(int(framerate_r * ready_time)):
        
        x, y             = joy.getX(), -joy.getY()
        x_trial.append(x)
        y_trial.append(y)
        t_trial.append(exp_clock.getTime()) 
        
        x               *= scaling
        y               *= scaling
        theta, radius    = ct.cart2pol(x, y, units="rad")

        cursor.pos       = ct.pol2cart(theta, radius, units="rad")
        
        cursor.draw()
        win.flip()

    #GO cue
    target.fillColor = 'green' 
    target.lineColor = 'green' 
    target.pos = ct.pol2cart(angle_list[trial], hidden_radius, units="rad")
    exp_go_onset = exp_clock.getTime()
    for frameN in np.arange(int(framerate_r * go_time)): #750ms
        
        x, y             = joy.getX(), -joy.getY()
        x_trial.append(x)
        y_trial.append(y)
        t_trial.append(exp_clock.getTime())

        x               *= scaling
        y               *= scaling
        theta, radius    = ct.cart2pol(x, y, units="rad")

        cursor.pos       = ct.pol2cart(theta, radius, units="rad")

        #stop-signal delay here 
        if frameN == int(framerate_r * ssd) and not go_list[trial]:

            target.fillColor = 'red' 
            target.lineColor = 'red' 

        target.draw()

        if radius < starting_radius:
            cursor.draw()
        elif radius < hidden_radius * .9:                
            start_mov = 1
        else:
            cursor.draw()
            full_mov = 1        
 
        win.flip()
    
    #post-GO cue
    target.fillColor = None
    target.lineColor = 'white'
    target.pos       = target_origin
    exp_post_go_onset = exp_clock.getTime()
    for frameN in np.arange(int(framerate_r * post_go_time)): 
        
        x, y             = joy.getX(), -joy.getY()
        x_trial.append(x)
        y_trial.append(y)
        t_trial.append(exp_clock.getTime())          

        x               *= scaling
        y               *= scaling
        theta, radius    = ct.cart2pol(x, y, units="rad")

        cursor.pos       = ct.pol2cart(theta, radius, units="rad")
        
        target.draw()
        win.flip()

    #ITI
    exp_iti_onset = exp_clock.getTime()
    ITI = core.StaticPeriod(screenHz=framerate_r)
    ITI_time = np.random.uniform(low=ITI_bounds[0], high=ITI_bounds[1])

    target.draw()
    win.flip()

    ITI.start(ITI_time)
    #operations during ITI
    data_dict["ID"].append(subj_ID)
    data_dict["trial"].append(trial)
    data_dict["fix_dur"].append(exp_ready_onset - exp_fix_onset)
    data_dict["ready_dur"].append(exp_go_onset - exp_ready_onset)
    data_dict["go_dur"].append(exp_post_go_onset - exp_go_onset)
    data_dict["post_go_dur"].append(exp_iti_onset - exp_post_go_onset)
    data_dict["ITI_dur"].append(ITI_time)
    data_dict["target_angle"].append(angle_list[trial])
    data_dict["SSD"].append(ssd)
    data_dict["GO/Stop"].append(go_list[trial])
    data_dict["start_mov"].append(start_mov)
    data_dict["full_mov"].append(full_mov)
    #save dataframe
    data_DF = pd.DataFrame(data_dict)
    data_DF.to_csv(
        os.path.join(joy_dir, data_filename)
    ) 
    #save joy output 
    joystick_output =  np.vstack(
        [np.array(x_trial), np.array(y_trial), np.array(t_trial)]
        )
    joy_filename = "ses{}_{}_trial{}.npy".format(
        session,
        subj_ID,
        str(trial).zfill(4),
    )
    np.save(
        os.path.join(joy_dir,joy_filename), 
        joystick_output
    )
    #increase or reduce ssd
    if not go_list[trial]:
        if full_mov: #failed to stop make it easier
            ssd -= .05
        else: #make it harder
            ssd += .05
    #end of ITI
    ITI.complete()

#quit session
win.close()
core.quit()

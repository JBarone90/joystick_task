import json
import os
import random as rnd
from enum import Enum
from math import radians

import numpy as np
import pandas as pd
import psychopy.tools.coordinatetools as ct
from psychopy import clock, core, event, gui, monitors, visual
from psychopy.hardware import joystick

# Define constants
NO_PERTURBATION_TRIAL = 80
ADAPTATION_PHASE_START = 80
ADAPTATION_PHASE_END = 230
PERTURBATION_ANGLE = radians(60)


class ExperimentPhases(Enum):
    NO_PERTURBATION = 1
    ADAPTATION = 2
    AFTER_EFFECT = 3


class ExperimentSetup:
    """Handles the initial setup of the experiment.

    This includes loading settings, prompting for subject ID and session,
    setting up directories, initializing the window, monitor, joystick,
    and visual stimuli, and creating an experiment clock.
    """

    def __init__(self, config_path="config/exp_settings.json"):
        """Initializes the setup by loading settings and initializing necessary components."""
        self.settings = self.load_settings(config_path)
        self.subject_id, self.session = self.prompt_subject_session()
        self.subj_dir, self.joy_dir, self.data_filename = self.setup_directories()
        self.win = self.setup_window_and_monitor()
        self.framerate_r = self.get_framerate()
        self.joy = self.init_joystick()
        self.target, self.cursor = self.init_visual_stimuli()
        self.exp_clock = clock.MonotonicClock()
        self.text_stim = visual.TextStim(
            self.win,
            text="",
            color="#848484",
            pos=(-7, 0),
            alignHoriz="left",
            height=1.4,
        )

    @staticmethod
    def load_settings(filepath):
        """Load settings from a json file."""
        with open(filepath) as f:
            return json.load(f)

    @staticmethod
    def prompt_subject_session():
        """Prompt the user for subject ID and session number."""
        exp_info = {"ID": 0, "session": 1}
        prompt = gui.DlgFromDict(
            dictionary=exp_info, title="Beta Burst Adaptation Task"
        )
        subject = exp_info["ID"]
        session = exp_info["session"]
        subj_id = str(subject).zfill(4)
        return subj_id, session

    def setup_directories(self):
        """Setup directories for subject data, joystick data, and experiment data."""
        subj_dir = os.path.join(
            "your_project_path",
            self.subject_id,
        )
        try:
            os.makedirs(subj_dir)
        except OSError:
            print("Caution! Existing directory")
            pass
        data_filename = f"ses{self.session}_{self.subject_id}.csv"
        joy_dir = os.path.join(subj_dir, os.path.splitext(data_filename)[0])
        # More robust directory creation with exception handling for existing directories
        try:
            os.makedirs(joy_dir)
        except OSError:
            myDlg = gui.Dlg(title="This folder already exists")
            myDlg.addText("Risk of overwriting data! If you wish to continue press OK")
            myDlg.show()  # show dialog
            if myDlg.OK:  # If OK continue
                pass
            else:  # quit session
                print("User cancelled")
                core.quit()
        return subj_dir, joy_dir, data_filename

    def setup_window_and_monitor(self):
        """Setup the window and monitor based on the settings loaded from the configuration file."""
        width, dist, res = self.settings["monitor_settings"]
        monitor = monitors.Monitor("default")
        monitor.setWidth(width)
        monitor.setDistance(dist)
        monitor.setSizePix(res)
        window = visual.Window(
            size=res,
            color="#000000",
            fullscr=True,
            allowGUI=False,
            winType="pyglet",
            units="deg",
            monitor=monitor,
        )
        return window

    def get_framerate(self):
        """Get the actual framerate of the window."""
        framerate = self.win.getActualFrameRate(
            nIdentical=10, nMaxFrames=120, nWarmUpFrames=10, threshold=1
        )
        return np.round(framerate)

    @staticmethod
    def init_joystick():
        """Initialize the joystick for input."""
        joystick.backend = "pyglet"
        return joystick.Joystick(0)

    def init_visual_stimuli(self):
        """Initialize the visual stimuli used in the experiment."""
        target = visual.Circle(
            self.win, 0.6, edges=40, fillColor=None, lineColor="white"
        )
        cursor = visual.Circle(
            self.win, 0.6, edges=40, fillColor="white", lineColor="white"
        )
        return target, cursor


class ExperimentRunner:
    """Manages the running of the experiment.

    This class is responsible for generating the sequence of target angles,
    determining the current phase of the experiment based on the trial number,
    running the experiment, executing individual trials, and saving the data.
    """

    def __init__(self, setup):
        """Initializes the runner with the given setup.

        Args:
            setup (ExperimentSetup): The setup object containing experiment settings.
        """
        self.setup = setup
        self.data = []
        self.joystick_data = []
        self.angle_list = self.generate_angle_list()
        rnd.shuffle(self.angle_list)  # Shuffle the angles for random presentation

    def generate_angle_list(self):
        """Generates a list of target angles for the experiment.

        Returns:
            list: A list of target angles in radians.
        """
        # Repeat target angles for each of the 5 directions, repeated for the number of trials divided by 5
        return [
            radians(self.setup.settings["target_angle"] * i) for i in np.arange(5)
        ] * int(self.setup.settings["n_trial"] / 5)

    def determine_experiment_phase(self, trial):
        """Determines the current phase of the experiment based on the trial number.

        Args:
            trial (int): The current trial number.

        Returns:
            ExperimentPhases: The current phase of the experiment.
        """
        if trial < NO_PERTURBATION_TRIAL:
            return ExperimentPhases.NO_PERTURBATION
        elif ADAPTATION_PHASE_START <= trial <= ADAPTATION_PHASE_END:
            return ExperimentPhases.ADAPTATION
        else:
            return ExperimentPhases.AFTER_EFFECT

    def run(self):
        """Runs the experiment from start to finish, managing each trial and handling user input."""
        blank = visual.TextStim(self.setup.win, text=" ", opacity=0.0)
        instructions = ["Press space bar to start"]
        for text in instructions:
            self.setup.text_stim.text = text
            self.setup.text_stim.draw()
            self.setup.win.flip()
            event.waitKeys(keyList=["space"], modifiers=False, timeStamped=False)

        blank.draw()
        self.setup.win.flip()
        core.wait(5)
        exp_start = self.setup.exp_clock.getTime()

        # Loop through each trial, checking for quit signal, and executing the trial
        for trial in np.arange(self.setup.settings["n_trial"]):
            if event.getKeys(keyList=["q"], timeStamped=False):
                break

            current_phase = self.determine_experiment_phase(trial)

            if current_phase == ExperimentPhases.NO_PERTURBATION:
                perturbation = 0.0
            elif current_phase == ExperimentPhases.ADAPTATION:
                perturbation = PERTURBATION_ANGLE
            else:  # ExperimentPhases.AFTER_EFFECT
                perturbation = 0.0

            self.execute_trial(trial, perturbation)

        self.setup.win.close()
        core.quit()

    def execute_trial(self, trial, perturbation):
        """Executes a single trial of the experiment, managing each phase and collecting data.

        Args:
            trial (int): The trial number.
            perturbation (float): The angle of perturbation in radians.
        """
        # empty list for storing data
        x_trial = []
        y_trial = []
        t_trial = []

        # reset movement info
        start_mov = 0
        full_mov = 0

        self.setup.target.draw()
        self.setup.win.flip()

        # don't start any trial unless joy pos is central
        while True:
            x, y = self.setup.joy.getX(), -self.setup.joy.getY()
            x *= self.setup.settings["scaling"]
            y *= self.setup.settings["scaling"]
            theta, radius = ct.cart2pol(x, y, units="rad")

            if radius >= self.setup.settings["starting_radius"]:
                self.setup.text_stim.text = "Release the joysitic"
                self.setup.text_stim.pos = (-6, 0)
                self.setup.text_stim.height = 1.5
                self.setup.text_stim.draw()
                self.setup.win.flip()

            else:
                break
        # Run each phase and collect joystick data
        fixation_properties = {
            "fillColor": None,
            "pos": self.setup.settings["target_origin"],
        }
        for prop, value in fixation_properties.items():
            setattr(self.setup.target, prop, value)
        exp_fix_onset, x_tmp, y_tmp, t_tmp = self.run_phase(
            self.setup.settings["fixation_time"], perturbation, "fixation"
        )
        x_trial.extend(x_tmp)
        y_trial.extend(y_tmp)
        t_trial.extend(t_tmp)

        exp_ready_onset, x_tmp, y_tmp, t_tmp = self.run_phase(
            self.setup.settings["ready_time"], perturbation, "ready"
        )
        x_trial.extend(x_tmp)
        y_trial.extend(y_tmp)
        t_trial.extend(t_tmp)

        go_properties = {
            "fillColor": "green",
            "lineColor": "green",
            "pos": ct.pol2cart(
                self.setup.angle_list[trial],
                self.setup.settings["hidden_radius"],
                units="rad",
            ),
        }
        for prop, value in go_properties.items():
            setattr(self.setup.target, prop, value)
        exp_go_onset, x_tmp, y_tmp, t_tmp, tmp_start, tmp_full = self.run_phase(
            self.setup.settings["go_time"], perturbation, "go", True
        )
        x_trial.extend(x_tmp)
        y_trial.extend(y_tmp)
        t_trial.extend(t_tmp)
        start_mov += tmp_start
        full_mov += tmp_full

        post_go_properties = {
            "fillColor": None,
            "lineColor": "white",
            "pos": self.setup.settings["target_origin"],
        }
        for prop, value in post_go_properties.items():
            setattr(self.setup.target, prop, value)
        exp_post_go_onset, x_tmp, y_tmp, t_tmp = self.run_phase(
            self.setup.settings["post_go_time"], perturbation, "post_go"
        )
        x_trial.extend(x_tmp)
        y_trial.extend(y_tmp)
        t_trial.extend(t_tmp)

        # ITI
        exp_iti_onset, ITI_time = self.run_ITI()

        # Save data
        self.save_trial_data(
            trial,
            exp_fix_onset,
            exp_ready_onset,
            exp_go_onset,
            exp_post_go_onset,
            exp_iti_onset,
            ITI_time,
            perturbation,
            start_mov,
            full_mov,
        )
        self.save_joystick_data(x_trial, y_trial, t_trial)
        self.save_experiment_data(trial)

    def run_phase(self, duration, perturbation, phase_name, go_phase=False):
        """Runs a single phase of a trial and collects joystick data.

        Args:
            duration (float): Duration of the phase.
            perturbation (float): The angle of perturbation.
            phase_name (str): Name of the phase for logging purposes.
            go_phase (bool): Whether this is the go phase.

        Returns:
            tuple: onset time and joystick data.
        """
        x_tmp, y_tmp, t_tmp = [], [], []
        tmp_start, tmp_full = 0, 0

        exp_phase_onset = self.setup.exp_clock.getTime()

        for frame_n in np.arange(int(self.setup.framerate_r * duration)):
            x, y = self.setup.joy.getX(), -self.setup.joy.getY()
            x_tmp.append(x)
            y_tmp.append(y)
            t_tmp.append(self.setup.exp_clock.getTime())

            x *= self.setup.settings["scaling"]
            y *= self.setup.settings["scaling"]
            theta, radius = ct.cart2pol(x, y, units="rad")
            theta += perturbation

            self.setup.cursor.pos = ct.pol2cart(theta, radius, units="rad")

            if go_phase:
                if radius < self.setup.settings["starting_radius"]:
                    self.setup.cursor.draw()
                elif radius < self.setup.settings["hidden_radius"] * 0.9:
                    tmp_start = 1
                else:
                    self.setup.cursor.draw()
                    tmp_full = 1

            if phase_name == "ready":
                self.setup.cursor.draw()
            else:
                self.setup.target.draw()

            self.setup.win.flip()

        return exp_phase_onset, x_tmp, y_tmp, t_tmp, tmp_start, tmp_full

    def run_ITI(self):
        """Runs the Inter-Trial Interval (ITI) phase.

        Returns:
            tuple: onset time and ITI duration.
        """
        ITI = core.StaticPeriod(screenHz=self.setup.framerate_r)
        ITI_time = np.random.uniform(
            low=self.setup.settings["ITI"][0], high=self.setup.settings["ITI"][1]
        )

        self.setup.target.draw()
        self.setup.win.flip()

        ITI.start(ITI_time)

        exp_iti_onset = self.setup.exp_clock.getTime()

        ITI.complete()

        return exp_iti_onset, ITI_time

    def save_trial_data(
        self,
        trial,
        exp_fix_onset,
        exp_ready_onset,
        exp_go_onset,
        exp_post_go_onset,
        exp_iti_onset,
        ITI_time,
        perturbation,
        start_mov,
        full_mov,
    ):
        data_dict = {
            "ID": self.setup.subject_id,
            "trial": trial,
            "fix_dur": exp_ready_onset - exp_fix_onset,
            "ready_dur": exp_go_onset - exp_ready_onset,
            "go_dur": exp_post_go_onset - exp_go_onset,
            "post_go_dur": exp_iti_onset - exp_post_go_onset,
            "ITI_dur": ITI_time,
            "target_angle": self.setup.angle_list[trial],
            "cursor_displacement": perturbation,
            "start_mov": start_mov,
            "full_mov": full_mov,
        }
        self.data.append(data_dict)

    def save_joystick_data(self, x_trial, y_trial, t_trial):
        # save joy output
        self.joystick_data = np.vstack(
            [np.array(x_trial), np.array(y_trial), np.array(t_trial)]
        )

    def save_experiment_data(self, trial):
        data_DF = pd.DataFrame(self.data)
        data_DF.to_csv(os.path.join(self.setup.joy_dir, self.setup.data_filename))
        joy_filename = "ses{}_{}_trial{}.npy".format(
            self.setup.session,
            self.setup.subject_id,
            str(trial).zfill(4),
        )
        np.save(os.path.join(self.setup.joy_dir, joy_filename), self.joystick_data)


def main():
    # initialize the random number generator
    rnd.seed()

    setup = ExperimentSetup()
    runner = ExperimentRunner(setup)
    runner.run()


if __name__ == "__main__":
    main()

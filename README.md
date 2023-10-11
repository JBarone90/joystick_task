# Joystick Adaptation Experiment

This project implements a joystick adaptation experiment using the PsychoPy library. Participants are instructed to perform specific tasks using a joystick, and the software captures and analyses their responses over a series of trials.

## Project Structure

The project consists of two main Python classes contained in the script `adaptation_main.py`:

1. `ExperimentSetup`: Handles the initial setup of the experiment including loading settings, initializing the PsychoPy window, joystick, and visual stimuli.
2. `ExperimentRunner`: Manages the running of the experiment including generating the sequence of target angles, determining the experiment phase based on trial number, executing individual trials, and saving the data.

The experiment settings are loaded from a JSON file `config/exp_settings.json`.

## Configuration

You can modify the experiment settings by editing the `config/exp_settings.json` file. Here you can change parameters such as the number of trials, target angles, and timing settings.

## Running the Experiment

1. Clone the repository to your local machine.
2. Navigate to the project directory.
3. Run the `adaptation_main.py` script:

## Data Output

The experiment data is saved to the directory specified in the `ExperimentSetup` class under the method `setup_directories`. By default, data is saved to `/your_path/subject_id`, with the joystick data saved in a subdirectory.

- Trial data is saved to a CSV file named `ses<session>_<subject_id>.csv`.
- Joystick data is saved to a NumPy file named `ses<session>_<subject_id>_trial<trial_number>.npy`.

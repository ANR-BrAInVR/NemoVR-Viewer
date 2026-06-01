---
title: Usage
---

This page explains how to use NemoVR-Viewer after the installation has been completed.

The viewer allows interactive visualization of tracking experiments, synchronized videos and DeepLabCut inference results.

---

# 1. Open a terminal

Before launching the viewer, open a terminal.

Open:

```text
Anaconda Prompt
```

or:

```text
PowerShell
```

---

# 2. Move into the project folder

Navigate to the folder where NemoVR-Viewer was downloaded.

Example on Windows:

```bash
cd "C:\Users\YOUR_USERNAME\Desktop\NemoVR-Viewer"
```

---

# 3. Activate the Conda environment

The Conda environment must be activated before launching the viewer.

Run:

```bash
conda activate DLC-live3
```

If the activation is successful, the terminal should display:

```text
(DLC-live3)
```

at the beginning of the command line.

---

# 4. Launch the viewer

Start the graphical interface with:

```bash
python Viewer.py
```

The NemoVR-Viewer window should now open.

---

# 5. Select the tracking log file

The first step inside the GUI is to select the tracking log file.

Click:

```text
Select resLog file
```

A file explorer window will open.

Navigate to your tracking results folder and select the `.tsv` tracking log file.

This file contains the information required to load:

* experiments
* subjects
* trials
* associated tracking files

---

# 6. Select a subject

Once the tracking log file has been loaded, the available subjects will appear in the `Subject` dropdown menu.

Select the subject you want to visualize.

The available subjects depend on the selected experiment.

---

# 7. Select a trial

After selecting a subject, available trials will appear in the `Trial` dropdown menu.

Choose the trial you want to load.

The viewer will automatically search for the corresponding:

* videos
* DLC files
* tracking results
* 3D reconstruction files

---

# 8. Configure visualization settings

Before starting playback, you can configure several visualization options directly from the GUI.

---

## View mode

Available modes:

* `2D videos`
* `3D plots`

The 2D mode displays synchronized videos with overlays.

The 3D mode displays reconstructed trajectories in 3D space.

---

## Show DLC

Displays DeepLabCut inferred body markers.

Useful for validating pose estimation quality.

---

## Show Track

Displays tracking trajectories and movement history.

---

## Trail size (frames)

Controls how many previous frames remain visible as trajectory trails.

Higher values create longer visible movement traces.

---

## Play speed

Controls playback speed.

Available speeds:

* x1/8
* x1/4
* x1/2
* x1
* x2
* x4
* x8

---

## Save video output

If enabled, the viewer exports visualization videos with overlays.

This option must be enabled BEFORE starting playback.

---

# 9. Start playback

Click:

```text
Start player
```

The viewer will load the selected files and initialize playback.

Depending on the file size and number of cameras, loading may take a few seconds.

---

# 10. Control playback

Once playback has started, use:

```text
Play / Pause
```

to start or pause the visualization.

---

# 11. Playback controls

Several navigation tools are available.

---

## Frame slider

The slider allows direct navigation through the recording.

You can move instantly to any frame.

---

## Frame navigation buttons

Available controls:

* `-10` → jump backward 10 frames
* `-1` → jump backward 1 frame
* `+1` → jump forward 1 frame
* `+10` → jump forward 10 frames

---

## Timeline information

The viewer displays:

* current frame
* elapsed time
* total recording duration
* total number of frames

---

# 12. Stop playback

To stop the current visualization session, click:

```text
Stop player
```

This closes the active viewers and releases loaded resources.

---

# 13. Video export

When:

```text
Save video output
```

is enabled, exported videos may contain:

* synchronized overlays
* DLC markers
* tracking trajectories
* trajectory trails
* 3D visualizations

Generated videos are saved automatically in the configured results directory.

---

# 14. Typical workflow

A standard usage workflow is:

1. Open a terminal
2. Activate the environment
3. Launch the viewer
4. Select the `.tsv` tracking log
5. Select a subject
6. Select a trial
7. Configure visualization options
8. Start playback
9. Analyze trajectories and videos


---

## Expected Results Structure

The viewer expects tracking-generated files organized as follows:

```text
Results/
└── EXPERIMENT_ID/
    └── SUBJECT_ID/
        ├── Trial_cam0.mp4
        ├── Trial_cam1.mp4
        ├── Trial_DLC2D.npy
        ├── Trial_DLC3D.npy
        └── ...
```
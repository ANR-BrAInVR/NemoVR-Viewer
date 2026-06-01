# NemoVR-Viewer

NemoVR-Viewer is a graphical application designed to visualize fish tracking experiments.

It allows synchronized playback of multi-camera recordings together with 2D/3D tracking data and DeepLabCut pose estimation results.

![Viewer](docs/assets/viewer_2dvideo.png)

*Example of synchronized multi-camera visualization of clownfish tracking with DeepLabCut markers and trajectory overlays.*

---

## Features

* Multi-camera synchronized playback
* DeepLabCut overlay visualization
* 2D and 3D tracking visualization
* Trajectory trails
* Playback speed control
* Video export
* Interactive GUI

---

## Requirements

NemoVR-Viewer uses a Conda environment.

We recommend installing Anaconda (https://www.anaconda.com/download)

Create the environment with:

```bash
conda create --name DLC-live3 -c conda-forge python=3.12 numpy matplotlib pyqt opencv
```

Activate the environment:

```bash
conda activate DLC-live3
```

Detailed installation instructions are available in the documentation.

## Configure results path

Before launching the viewer, open:

```text
Settings.txt
```

and configure:

```text
resultsDir
```

Example:

```text
resultsDir    'C:/Users/Desktop/Results'
```

---

## Launch the viewer

```bash
python Viewer.py
```

---

## Documentation

Full documentation:

https://anr-brainvr.github.io/NemoVR-Viewer/

GitHub repository:

https://github.com/ANR-BrAInVR/NemoVR-Viewer


---

## Credits

NemoVR-Viewer was developed within the BrAInVR project.

Scientific coordination and experimental framework:

* Manuel Vidal
* Institut de Neurosciences de la Timone (INT)

Funding:

* French National Research Agency (ANR)

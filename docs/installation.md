---
title: Installation
---

This page explains how to install NemoVR-Viewer step by step on a computer.

These installation steps only need to be completed once during the initial setup of the viewer.

After the installation is complete, launching the application only requires activating the environment and running the viewer.

The goal is to help users who may not be familiar with Python, terminals or programming environments.

---

# 1. Install Miniconda

NemoVR-Viewer uses a Python environment managed with **Conda**.

Conda allows the project to install all required dependencies automatically and avoids conflicts with other Python installations on your computer.

We recommend installing **Miniconda**, which provides a lightweight Conda installation and all required environment management tools.

Users already working with Anaconda can use it as well.

Download Miniconda here:

* Windows/Linux installer:

```text
https://docs.conda.io/en/latest/miniconda.html
```

Install Miniconda using the default installation settings.


---

# 2. Open a terminal

You will now create the Python environment required for the viewer.

## On Windows

Open:

```text
Anaconda Prompt
```

or:

```text
PowerShell
```

---

## On Linux

Open a standard terminal.

---

# 3. Clone the repository

The NemoVR-Viewer project files must now be downloaded to your computer.

Choose a location where you would like to store the project folder.

For example, you may want to place the project on your Desktop.

The following steps will download the complete NemoVR-Viewer project into the selected folder.

---

## Open a terminal in your chosen location

### Example on Windows

If you want to place the project on your Desktop, run:

```bash
cd "C:\Users\YOUR_USERNAME\Desktop"
```

Replace:

```text
YOUR_USERNAME
```

with your own Windows username.

Example:

```bash
cd "C:\Users\johnsmith\Desktop"
```

---

## Example on Linux

```bash
cd ~/Desktop
```

---

## Clone the repository

Run:

```bash
git clone https://github.com/ANR-BrAInVR/NemoVR-Viewer.git
```

This command downloads the complete NemoVR-Viewer project from GitHub to your computer.

All project files will automatically be copied into the selected folder.

A new folder named:

```text
NemoVR-Viewer
```

will automatically be created.

## Move into the project folder

Run:

```bash
cd NemoVR-Viewer
```

Your terminal is now located inside the project directory.

# 4. Create the Conda environment (ONE TIME ONLY)

This step only needs to be completed once after downloading the project.

The following command creates an isolated Python environment containing all libraries required by the NemoVR ecosystem.

The same environment can be reused for several NemoVR components, including:

* viewer
* tracking
* post-processing
* rendering tools

Before creating the environment, it is recommended to verify that an environment named:

```text id="m9t3el"
DLC-live3
```

does not already exist on your computer.

You can list existing Conda environments with:

```bash id="6k7r1n"
conda env list
```

If an environment named `DLC-live3` already exists, you can reuse it directly.

Otherwise, create the environment with:

```bash id="9nn2u4"
conda create --name DLC-live3 -c conda-forge python=3.12 numpy matplotlib pyqt opencv
```

During installation, Conda may ask:

```text id="vcw4pn"
Proceed ([y]/n)?
```

Type:

```text id="qzj3bw"
y
```

and press Enter.

The installation may take several minutes depending on your internet connection and computer performance.

# 5. Activate the environment

Each time you want to use NemoVR-Viewer, the Conda environment must first be activated.

Run:

```bash
conda activate DLC-live3
```

Once activated, your terminal should display:

```text
(DLC-live3)
```

at the beginning of the command line.

Keep this terminal window open, as it will later be used to launch the viewer.

# 6. Configure the results directory

Before launching the viewer, you must configure the location of your tracking results.

At this stage, you are no longer working in the terminal.

Instead, open the project folder on your computer using the file explorer.

Locate the file:

```text
Settings.txt
```

And open it by double-clicking on it.

The file can be edited with the default text editor installed on your computer.

---

Inside the file, locate the following line:

```text
resultsDir
```

Modify it to point to your results folder.

Example:

```text
resultsDir    'C:/Users/Desktop/Results'
```

Use the full absolute path to your tracking results directory.

Save the file once the modification is complete.

# 7. Launch the viewer

After configuring `Settings.txt`, return to the terminal window used previously.

Before launching the viewer, verify that the Conda environment is still activated.

The terminal should display:

```text
(DLC-live3)
```

at the beginning of the command line.

If the environment is no longer active, run:

```bash
conda activate DLC-live3
```

Then launch the viewer with:

```bash
python Viewer.py
```

The NemoVR-Viewer graphical interface should now open.

# 8. Next steps

Once the viewer is running, detailed instructions for using the graphical interface are available in the `Usage` documentation page.

The usage guide explains how to:

* select tracking files
* choose subjects and trials
* configure visualization options
* control playback
* export videos
* navigate through recordings

See:

```text id="qpn3ga"
Usage
```

# 9. Expected results structure

The viewer expects tracking-generated files organized according to the NemoVR project architecture.

Detailed information about:

* expected folder organization
* tracking-generated files
* video naming conventions
* DLC and reconstruction files

is available in the `Usage` documentation page.

# 10. Troubleshooting

## Conda command not found

If the terminal says:

```text
conda: command not found
```

restart your terminal after installing Miniconda.

---

## Viewer does not open

Make sure the environment is activated:

```text
(DLC-live3)
```

should appear in the terminal.

---

## Missing result files

Verify that:

* `resultsDir` is correctly configured
* tracking files exist
* the folder structure matches the expected format

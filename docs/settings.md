# Settings

The NemoVR-Viewer behavior can be configured using the:

```text
Settings.txt
```

file located in the project directory.

Most parameters already have working default values and usually do not need to be modified.

However, advanced users may customize the viewer behavior, display configuration and playback options.

---

# Parameters Available in the GUI

The following settings are directly accessible from the graphical interface.

These values can also be modified manually inside `Settings.txt`.

---

# View mode

Controls the visualization mode used by the viewer.

## Available values

| Value | Description                 |
| ----- | --------------------------- |
| `2`   | 2D synchronized videos      |
| `3`   | 3D trajectory visualization |

## Default value

```text
2
```

## GUI label

```text
View mode
```

---

# Show DLC

Enables or disables DeepLabCut marker visualization.

When enabled, tracked body keypoints are displayed directly on the videos.

## Available values

| Value   | Description         |
| ------- | ------------------- |
| `True`  | Display DLC markers |
| `False` | Hide DLC markers    |

## Default value

```text
True
```

## GUI label

```text
Show DLC
```

---

# Show Track

Displays animal tracking trajectories.

Useful for visualizing movement history and locomotion patterns.

## Available values

| Value   | Description                   |
| ------- | ----------------------------- |
| `True`  | Display tracking trajectories |
| `False` | Hide trajectories             |

## Default value

```text
True
```

## GUI label

```text
Show Track
```

---

# Trail size (frames)

Defines how many previous frames remain visible as trajectory trails.

Higher values create longer movement traces.

## Example

| Value | Effect                  |
| ----- | ----------------------- |
| `5`   | Short trail             |
| `20`  | Medium trail            |
| `60`  | Long trajectory history |

## Default value

```text
20
```

## GUI label

```text
Trail size (frames)
```

---

# Playback speed

Controls playback speed during visualization.

## Available values

* `0.125`
* `0.25`
* `0.5`
* `1`
* `2`
* `4`
* `8`

## Default value

```text
1
```

## GUI label

```text
Play speed
```

---

# Save video output

Exports visualization videos with overlays.

Generated videos may include:

* DLC markers
* trajectories
* synchronized playback
* 3D rendering

## Available values

| Value   | Description          |
| ------- | -------------------- |
| `True`  | Save exported videos |
| `False` | Disable export       |

## Default value

```text
False
```

## GUI label

```text
Save video output
```

---

# Use cyclop

Uses inferred cyclop positions instead of raw tracking detections.

This option may improve trajectory smoothness depending on the dataset.

## Available values

| Value   | Description          |
| ------- | -------------------- |
| `True`  | Use cyclop inference |
| `False` | Use raw detections   |

## Default value

```text
False
```

## GUI label

```text
Use cyclop
```

---

# Additional Settings

The following parameters are available only inside `Settings.txt`.

---

# resultsDir

Defines the location of the tracking results directory.

## Example

```text
resultsDir    'C:/Users/Desktop/Results'
```

## Description

The viewer searches this folder to load:

* videos
* DLC inference files
* tracking results
* 3D reconstructions

---

# speciesName

Defines the species configuration used by the viewer.

Species-specific DLC configurations and visualization settings may depend on this value.

## Examples

```text
'Clownfish'
'Surgeonfish'
'Aruanus'
'Damselfish'
'Cod'
```

---

# camList

Defines which cameras are loaded.

## Example

```text
[0,1]
```

## Description

The viewer will search for corresponding files such as:

```text
Trial_cam0.mp4
Trial_cam1.mp4
```

---

# cropSize

Defines the displayed crop size around tracked animals.

## Example

```text
(500,500)
```

## Description

Larger values display a wider region around the animal.

Smaller values focus more closely on the tracked subject.

---

# xMonitWin

Defines the horizontal screen position where video windows open.

Useful for multi-monitor setups.

## Example

```text
xMonitWin = 1920
```

---

# Notes

## Default values

Most settings already contain recommended default values.

For most users, only:

```text
resultsDir
```

needs to be modified.

---

## GUI synchronization

Settings modified through the GUI are reflected internally during runtime.

Some advanced parameters remain accessible only through `Settings.txt`.

---

## Recommended workflow

Typical workflow:

1. Configure `resultsDir`
2. Launch the viewer
3. Select visualization settings from the GUI
4. Start playback

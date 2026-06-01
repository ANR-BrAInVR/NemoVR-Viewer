---

## title: Settings

The NemoVR-Viewer behavior can be configured using the:

```text
Settings.txt
```

file located in the project directory.

Most parameters already have working default values and usually do not need to be modified.

For most users, only the results directory must be changed before launching the viewer.

---

# Main Settings Table

The table below follows the order used in `Settings.txt`.

Some parameters are available directly in the graphical interface. In that case, the value in `Settings.txt` defines the default value loaded when the viewer starts.

Parameters marked as **Advanced setting** are only edited manually in `Settings.txt`.

| Parameter     |                Default value | GUI access            | Description                                                                                                                                                                                                                                       |
| ------------- | ---------------------------: | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `speciesName` |                `'Clownfish'` | Advanced setting      | Defines the species configuration used by the viewer. Species-specific DLC marker names and visualization settings may depend on this value. Supported examples include `'Clownfish'`, `'Surgeonfish'`, `'Aruanus'`, `'Damselfish'`, and `'Cod'`. |
| `resultsDir`  | `'C:/Users/Desktop/Results'` | Advanced setting      | Defines the folder where tracking results are stored. The viewer uses this path to find videos, tracking files, DLC inference files and 3D reconstruction files. This is usually the first parameter to configure.                                |
| `viewMode`    |                          `2` | `View mode`           | Defines the default visualization mode. `2` displays synchronized 2D videos with overlays. `3` displays reconstructed 3D trajectories.                                                                                                            |
| `showDLC`     |                       `True` | `Show DLC`            | Enables DeepLabCut marker visualization. When enabled, inferred body keypoints are displayed directly on the videos or plots.                                                                                                                     |
| `showTrack`   |                       `True` | `Show Track`          | Displays animal tracking positions and trajectories. Useful for inspecting movement history and tracking quality.                                                                                                                                 |
| `trailFrames` |                         `20` | `Trail size (frames)` | Defines how many previous frames remain visible as trajectory trails. Lower values show short trails; higher values show longer movement histories.                                                                                               |
| `useCyclop`   |                      `False` | `Use cyclop`          | Uses inferred cyclop positions instead of raw tracking detections. This may improve trajectory smoothness depending on the dataset.                                                                                                               |
| `saveVideos`  |                      `False` | `Save video output`   | Enables export of visualization videos with overlays, markers or 3D rendering. This should be enabled before starting playback.                                                                                                                   |
| `speed`       |                          `1` | `Play speed`          | Defines the default playback speed. Available values are usually `0.125`, `0.25`, `0.5`, `1`, `2`, `4`, and `8`.                                                                                                                                  |
| `camList`     |                     `[0, 1]` | Advanced setting      | Defines which cameras are loaded by the viewer. For example, `[0, 1]` loads files such as `Trial_cam0.mp4` and `Trial_cam1.mp4`.                                                                                                                  |
| `cropSize`    |                 `(500, 500)` | Advanced setting      | Defines the displayed region of interest size in pixels. Larger values display a wider area around the animal, while smaller values focus more closely on the tracked subject.                                                                    |
| `xMonitWin`   |             depends on setup | Advanced setting      | Defines the horizontal screen position where video windows open. Useful for multi-monitor setups.                                                                                                                                                 |

---

# Parameters Available in the GUI

The following parameters can be changed directly from the viewer interface.

When modified in `Settings.txt`, they define the default values loaded at startup.

| GUI label             | Related parameter | Available values                           |
| --------------------- | ----------------- | ------------------------------------------ |
| `View mode`           | `viewMode`        | `2D videos`, `3D plots`                    |
| `Show DLC`            | `showDLC`         | `True`, `False`                            |
| `Show Track`          | `showTrack`       | `True`, `False`                            |
| `Trail size (frames)` | `trailFrames`     | integer value                              |
| `Use cyclop`          | `useCyclop`       | `True`, `False`                            |
| `Save video output`   | `saveVideos`      | `True`, `False`                            |
| `Play speed`          | `speed`           | `0.125`, `0.25`, `0.5`, `1`, `2`, `4`, `8` |
| `Slider`              | playback position | controlled directly during playback        |

---

# Advanced Settings

Advanced settings are only modified manually inside `Settings.txt`.

Most users should keep the default values unless they need to adapt the viewer to a specific acquisition setup.

## `resultsDir`

Defines the location of the tracking results directory.

Example:

```text
resultsDir    'C:/Users/Desktop/Results'
```

The viewer searches this folder to load:

* videos
* DLC inference files
* tracking results
* 3D reconstructions

## `speciesName`

Defines the species configuration used by the viewer.

Examples:

```text
'Clownfish'
'Surgeonfish'
'Aruanus'
'Damselfish'
'Cod'
```

## `camList`

Defines which cameras are loaded.

Example:

```text
[0, 1]
```

The viewer will search for corresponding video files such as:

```text
Trial_cam0.mp4
Trial_cam1.mp4
```

## `cropSize`

Defines the displayed crop size around tracked animals.

Example:

```text
(500, 500)
```

## `xMonitWin`

Defines the horizontal screen position where video windows open.

This can be useful when using multiple monitors.

Example:

```text
xMonitWin    1920
```

---

# Recommended Workflow

Typical workflow:

1. Configure `resultsDir`
2. Launch the viewer
3. Select visualization settings from the GUI
4. Start playback

Detailed usage instructions are available in the [Usage](usage.md) documentation page.

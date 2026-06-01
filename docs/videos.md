---
title: Videos
---

This page contains example recordings generated with NemoVR-Viewer.

---

# Example 1 — 2D Tracking Visualization

This example demonstrates:

* synchronized multi-camera playback
* DeepLabCut marker visualization
* tracking trajectories
* real-time playback

<video controls width="100%">
  <source src="assets/recording_2d.mp4" type="video/mp4">
</video>

*Figure 1 — Example of synchronized 2D visualization with DLC overlays.*

---

# Example 2 — 3D Visualization

This example demonstrates:

* 3D trajectory reconstruction
* dynamic trajectory rendering
* multi-animal visualization
* spatial movement analysis

<video controls width="100%">
  <source src="assets/recording_3d.mp4" type="video/mp4">
</video>

*Figure 2 — Example of 3D reconstructed trajectory visualization generated from multi-camera tracking data.*

---

# Adding Your Own Videos

You can add your own recordings to the documentation by placing video files inside:

```text
docs/assets/
```

Then reference them directly in the markdown pages.

---

# Supported Formats

Recommended video formats:

* `.mp4`
* H264 encoded videos

---

# Notes

Video export can be enabled directly from the GUI using:

```text
Save video output
```

Exported videos may include:

* tracking overlays
* DLC markers
* trajectory trails
* synchronized playback
* optional 3D visualization

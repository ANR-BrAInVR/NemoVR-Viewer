# -*- coding: utf-8 -*-
"""
Created on Mon May 11 12:30:45 2022

@authors: Manuel

TODO:
- Plot3D : faire marcher le blitmanager avec projection 3D
+ Plot3D : afficher sur le plot X, Y les points avec gazeDir, velocity (curvature, à faire ?)
+ lorsque la vitesse est x2 x4 ou x8 sauter 2 4 ou 8 frames (sinon on ne respecte pas la vitesse demandée)
+ debugger le slider pour qu'il n'y ait pas de décalage entre video et overlays
+ améliorer le slider pour le temps et frame (à gauche et à droite)
+ possibilité d'avancer/reculer pas à pas (une fois en pause)
+ option sauvegarde des vidéos avec markeurs ou des plots 3D animés (saveVideos dans Settings.txt)
+ Plot3D : projeter sur X, Y uniquement
+ Plot3d : ouvrir avec une taille plus grande pour meilleur visibilité
+ revoir structure multiprocess (uniquement ViewerUI dans un autre process)
+ virer serveur TCP
+ Fusionner les settings
+ Adapter le delay entre chaque iterations pour être en temps réel

"""

import multiprocessing as mp
import threading
import time
import socket
import sys
import os
import re
import csv
import numpy as np
import cv2
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from ctypes import c_wchar_p

# DLC markers variables
keyRadius = 3       # Maximal radius size of the markers for monitoring (when inference p=1)
cyclopRadius = 5    # Maximal radius size of cyclop for monitoring (when inference p=1)
cyclopColor = 0     # Detection or cyclop marker center color (white)

# Settings (communication between processes)
viewMode = mp.Value('B', 2)        # Viewer mode 2:'2D videos' or 3:'3D plots'
showTrack = mp.Value('B', 1)       # Show animal tracking
showDLC = mp.Value('B', 1)         # Show DLC inferred markers
trailFrames = mp.Value('I', 0)     # Number of frames used to create trail (0 for no trail)
useCyclop = mp.Value('B', 1)       # Use 2D detection if True, else DLC inferred cyclop
speed = mp.Value('f', 1)           # Play speed, use values in [0.125, 0.25, 0.5, 1, 2, 4, 8]

# Global control flags (communication between processes)
startPlayer = mp.Value('B', 0)     # Start player when True
stopPlayer = mp.Value('B', 0)      # Stop player when True
quit = mp.Value('B', 0)            # Quits all when True
play = mp.Value('B', 0)            # Play/Pause when True/False
imgIndex = mp.Value('L', 0)        # Current image index
nFrames = mp.Value('L', 0)         # Number of frames in video or results files
framerate = mp.Value('I', 0)       # Framerate of videos or results files
saveVideos = mp.Value('B', 0)      # Save 2D videos with overlay or 3D plots when True
sendPos3D = mp.Value('B', 0)       # Stream 3D pos to rendering
IP = {'Tracking': '192.168.0.2', 'Rendering': '192.168.0.1'}
UDPserverRendering = (IP['Rendering'], 50771)

# Viewer object
class Viewer:
    """Object that reads videos and results files and show it on screen"""

    # Constructor with param initialization
    def __init__(self):
        """Initializes viewer's parameters"""

        # Strings (communication between processes)
        manager = mp.Manager()
        self.expID_M = manager.Value(c_wchar_p, 'MyExp')
        self.subjectID_M = manager.Value(c_wchar_p, 'MySubject')
        self.file_M = manager.Value(c_wchar_p, 'MyFile')

        # Log object
        self.log = Log(logLevel=2, showTime=True)
        self.log.LogText(1, 'Viewer() called')

        # Load settings
        self.LoadSettingsFile('Settings')

        # Load species detection settings
        self.LoadSettingsFile('Color settings - %s' % self.speciesName)

        # Initialize process shared variables
        viewMode.value = self.viewMode
        showTrack.value = self.showTrack
        showDLC.value = self.showDLC
        trailFrames.value = self.trailFrames
        useCyclop.value = self.useCyclop
        speed.value = self.speed
        startPlayer.value = False
        quit.value = False
        saveVideos.value = self.saveVideos
        sendPos3D.value = self.sendPos3D
        if self.expID != '':
            self.expID_M.value = self.expID
            self.resLogFile = os.path.join(self.resultsDir, self.expID, self.expID + '_files.tsv')
            # self.resultsDir + '/' + self.expID + '/' + self.expID + '_files.tsv'

        # Starts GUI
        self.ViewerUIproc = mp.Process(target=self.StartViewerUI)
        self.ViewerUIproc.start()
        self.log.LogText(2, 'Viewer: GUI process started')

        # Start viewer listener
        while not quit.value:

            # Waits for player start
            if startPlayer.value:
                startPlayer.value = False

                if not self.showDLC and not self.showTrack:
                    if saveVideos.value:
                        self.log.LogText(2, 'Viewer: saveVideos=True but no overlay asked (DLC or Track), ignoring.')
                        saveVideos.value = False
                    if viewMode.value == 3:
                        self.log.LogText(2, 'Viewer: viewMode=\'3D plots\' but no overlay asked (DLC or Track), switching to \'2D videos\'.')
                        viewMode.value = 2

                # Start thread corresponding to desired mode
                if viewMode.value == 2:         # 2D videos
                    self.log.LogText(2, 'Viewer: starting VideoPlayer()')
                    self.VideoPlayer()
                elif viewMode.value == 3:       # 3D plots
                    self.log.LogText(2, 'Viewer: starting Plot3DPlayer()')
                    self.Plot3DPlayer()
                else:
                    self.log.LogText(2, 'Viewer: Error, unkown player mode %d, ignoring.' % viewMode.value)
                    return

        self.log.LogText(2, 'Viewer: quit received, quitting')

    def __del__(self):
        """Destructor"""

        self.log.LogText(1, 'Viewer destructor called')

        # Kill ViewerUI if still there
        self.ViewerUIproc.kill()

        # Close openCV windows and plot if any
        cv2.destroyAllWindows()
        plt.close()

        # Give time for processes to end
        time.sleep(0.5)


    def StartViewerUI(self):

        myQtApp = QApplication(sys.argv)
        ViewerUI(self.log, self.resultsDir, self.resLogFile, self.expID_M, self.subjectID_M, self.file_M)
        myQtApp.exec_()


    def VideoPlayer(self):
        """Starts video player with tracking and DLC results"""

        self.log.LogText(1, 'VideoPlayer() called')

        # Set initial control flags
        play.value = False
        playStarted = False
        stopPlayer.value = False

        # Full path with filename basis
        fullNameBasis = '%s/%s/%s/%s' % (self.resultsDir, self.expID_M.value, self.subjectID_M.value, self.file_M.value)

        # Video variables
        camCount = len(self.camList)        # Number of cameras
        videos = [None] * camCount          # Video of each camera
        videoNFrames = [0] * camCount       # Number of frames in each video
        Ymin = [0] * camCount
        Ymax = [0] * camCount
        Xmin = [0] * camCount
        Xmax = [0] * camCount

        # Opens videos
        for camInd in range(camCount):
            camNb = self.camList[camInd]
            videoFilename = fullNameBasis + '_cam%d.mp4' % camNb
            videos[camInd] = cv2.VideoCapture(videoFilename)
            if not videos[camNb].isOpened():
                self.log.LogText(1, 'VideoPlayer: Error opening video file \'%s\', quitting' % videoFilename)
                return -1
            videos[camInd].set(cv2.CAP_PROP_BUFFERSIZE, 1)
            videoNFrames[camInd] = int(videos[camInd].get(cv2.CAP_PROP_FRAME_COUNT))

            # Prepare crop ranges (for MarmoVR these must be red at each frame from 2D results file)
            Xmin[camNb] = self.cropULs[camNb][0]
            Xmax[camNb] = self.cropULs[camNb][0] + self.cropSize[0]
            Ymin[camNb] = self.cropULs[camNb][1]
            Ymax[camNb] = self.cropULs[camNb][1] + self.cropSize[1]

        # Prepares target panel
        imgWidth = int(videos[0].get(cv2.CAP_PROP_FRAME_WIDTH))
        imgHeight = int(videos[0].get(cv2.CAP_PROP_FRAME_HEIGHT))
        resize = self.imgMode == 'full'
        if resize:
            imgMonitDim = [imgHeight // 2, imgWidth // 2, 3]
        else:
            imgMonitDim = [self.cropSize[1], self.cropSize[0], 3]
        if abs(self.rotateCamList[0]) != 0:
            imgMonitDim[0], imgMonitDim[1] = imgMonitDim[1], imgMonitDim[0]         # Swap dimensions (for rotations)
        panelDim = [imgMonitDim[0], imgMonitDim[1]*2, 3]
        imgPanel = np.zeros(panelDim, 'uint8')

        # Load 2D results
        filename = fullNameBasis + self.ext2D + '.npy'
        if not os.path.exists(filename):
            self.log.LogText(1, 'VideoPlayer: Error opening 2D results file \'%s\', quitting' % file.value)
            return -1
        else:
            res2D = np.load(filename)
            # dt2D = res2D.dtype

        # Get framerate and number of frames
        framerate.value = int(videos[0].get(cv2.CAP_PROP_FPS))       # Overrides Settings.txt value
        nFrames.value = min(videoNFrames)
        self.log.LogText(2, 'VideoPlayer: nFrames=%d (at %d fps)' % (nFrames.value, framerate.value))
        imgIndex.value = 0
        fInd = -1
        t0 = time.time_ns()     # Initial time (for playback speed)

        if sendPos3D.value:
            # Loads 3D results (triangulations)
            filename = fullNameBasis + self.ext3D + '.npy'
            if not os.path.exists(filename):
                self.log.LogText(1, 'Plot3DPlayer: Error opening 3D results file \'%s\', quitting' % file.value)
                return -1
            else:
                res3D = np.load(filename)
                # dt3D = res3D.dtype

            # Starts connection with Rendering PC
            UDPServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Main loop
        while True:

            # If not playing yet, waits for play command
            if not playStarted:
                while not play.value:
                    pass

                # Prepare video recording
                if saveVideos.value:
                    videoFilename = fullNameBasis + '_2D videos.mp4'
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    videoOut = cv2.VideoWriter(videoFilename, fourcc, framerate.value, (panelDim[1], panelDim[0]), isColor=True)
                    self.log.LogText(2, ' VideoPlayer: output video writers created')

                # Prepare window
                windowName = 'Images %s' % ('(with DLC)' if showDLC.value else '')
                cv2.namedWindow(windowName, cv2.WINDOW_GUI_NORMAL | cv2.WINDOW_AUTOSIZE)
                cv2.moveWindow(windowName, self.xMonitWin, 0)

                playStarted = True
                self.log.LogText(2, 'VideoPlayer: Play received')

            # Stop player received
            if stopPlayer.value:
                # Close video output recording
                if saveVideos.value:
                    videoOut.release()
                    self.log.LogText(2, 'VideoPlayer: output video writers closed')

                self.log.LogText(2, 'VideoPlayer: stopPlayer received, quitting')
                break

            # Check if paused
            if not play.value and imgIndex.value == fInd:
                continue

            # Check end of file
            if imgIndex.value >= nFrames.value or imgIndex.value >= len(res2D['pos(Cyclop)_cam0']):
                if not saveVideos.value:
                    self.log.LogText(2, 'VideoPlayer: Reached end of video file, looping')
                    imgIndex.value = 0
                else:
                    self.log.LogText(2, 'VideoPlayer: Reached end of video file, quitting')
                    stopPlayer.value = True
                    continue

            # Jump to the desired frame when img index is changed by slider or buttons
            if imgIndex.value != fInd + 1:
                fInd = imgIndex.value
                for camInd in range(camCount):
                    camNb = self.camList[camInd]
                    videos[camNb].set(cv2.CAP_PROP_POS_FRAMES, fInd)
                # time.sleep(0.05)
                self.log.LogText(3, 'VideoPlayer: imgIndex set to %d' % fInd)
            else:
                # Blocks current frame index
                fInd = imgIndex.value

            # Displays videos with 2D data overlayer
            for camInd in range(camCount):
                camNb = self.camList[camInd]

                # Get next image in the desired format
                ret, img = videos[camNb].read()

                if resize:
                    # Get full image and draws crop rectangle
                    img = cv2.rectangle(img, (Xmin[camNb], Ymin[camNb]), (Xmax[camNb], Ymax[camNb]), (255, 255, 255), thickness=2)
                else:
                    # Get cropped image
                    img = np.copy(img[Ymin[camNb]:Ymax[camNb], Xmin[camNb]:Xmax[camNb], :])

                # Adds detected fish position or DLC inferred cyclop
                if showTrack.value:
                    if useCyclop.value:
                        # Draws trail (if trailFrames.value > 1)
                        for fIndTrail in range(max(fInd-trailFrames.value+1, 0), fInd):
                            pPos = res2D['proba(Cyclop)_cam%d' % camNb][fIndTrail]
                            if pPos == -1: continue
                            if resize:
                                xPos, yPos = res2D['pos(Cyclop)_cam%d' % camNb][fIndTrail].astype(int)
                            else:
                                xPos, yPos = res2D['pos(Cyclop)_cam%d' % camNb][fIndTrail].astype(int) - self.cropULs[camNb]
                            cKey = int(255 * (fInd - fIndTrail) / trailFrames.value)
                            rKey = int(keyRadius * 1.12*np.sqrt(pPos)) if self.sizeToProba else int(keyRadius)
                            img = cv2.circle(img, (xPos, yPos), rKey, [cKey] * 3, thickness=cv2.FILLED)

                        self.log.LogText(3, 'VideoPlayer(%d): Draw DLC inferred cyclop (imgIndex=%d)' % (camNb, imgIndex.value))

                        # Draws circle(s) on inferred cyclop position
                        pPos = res2D['proba(Cyclop)_cam%d' % camNb][fInd]
                        if pPos == -1: continue
                        pPos = np.sqrt(pPos)
                        if resize:
                            xPos, yPos = res2D['pos(Cyclop)_cam%d' % camNb][fInd].astype(int)
                        else:
                            xPos, yPos = res2D['pos(Cyclop)_cam%d' % camNb][fInd].astype(int) - self.cropULs[camNb]
                        rKeyExt = int(cyclopRadius * 1.12*np.sqrt(pPos)) if self.sizeToProba else int(cyclopRadius)
                        img = cv2.circle(img, (xPos, yPos), rKeyExt, [255-cyclopColor] * 3, thickness=cv2.FILLED)
                        rKeyInt = int(keyRadius * 1.12*np.sqrt(pPos)) if self.sizeToProba else int(keyRadius)
                        img = cv2.circle(img, (xPos, yPos), rKeyInt, [cyclopColor] * 3, thickness=cv2.FILLED)
                    else:
                        # Draws trail (if trailFrames.value > 1)
                        for fIndTrail in range(max(fInd-trailFrames.value+1, 0), fInd):
                            nFishDetect2D = res2D['nFishDetected_cam%d' % camNb][fIndTrail]
                            for fishIndex in range(nFishDetect2D):
                                if resize:
                                    xPos, yPos = res2D['pos(%d)_cam%d' % (fishIndex, camNb)][fIndTrail].astype(int)
                                else:
                                    xPos, yPos = res2D['pos(%d)_cam%d' % (fishIndex, camNb)][fIndTrail].astype(int) - self.cropULs[camNb]
                                cKey = int(255 * (fInd - fIndTrail) / trailFrames.value)
                                img = cv2.circle(img, (xPos, yPos), int(keyRadius), [cKey] * 3, thickness=cv2.FILLED)

                        nFishDetect2D = res2D['nFishDetected_cam%d' % camNb][fInd]
                        self.log.LogText(3, 'VideoPlayer(%d): Draw %d detected fish position(s)' % (camNb, nFishDetect2D))

                        # Draws circle(s) on detected 2D position(s)
                        for fishIndex in range(nFishDetect2D):
                            if resize:
                                xPos, yPos = res2D['pos(%d)_cam%d' % (fishIndex, camNb)][fInd].astype(int)
                            else:
                                xPos, yPos = res2D['pos(%d)_cam%d' % (fishIndex, camNb)][fInd].astype(int) - self.cropULs[camNb]
                            img = cv2.circle(img, (xPos, yPos), int(cyclopRadius), [255-cyclopColor]*3, thickness=cv2.FILLED)
                            img = cv2.circle(img, (xPos, yPos), int(keyRadius), [cyclopColor]*3, thickness=cv2.FILLED)

                # Adds markers inferred by DLC
                if showDLC.value:
                    self.log.LogText(3, 'VideoPlayer(%d): Draw markers inferred by DLC (imgIndex=%d) ' % (camNb, imgIndex.value))
                    for keyInd, keyName in enumerate(self.keyNames):
                        # Get marker position and proba
                        if resize:
                            xKey, yKey = res2D['pos(%s)_cam%d' % (keyName, camNb)][fInd].astype(int)
                        else:
                            xKey, yKey = res2D['pos(%s)_cam%d' % (keyName, camNb)][fInd].astype(int) - self.cropULs[camNb]
                        rKey = int(keyRadius * 1.12*np.sqrt(res2D['proba(%s)_cam%d' % (keyName, camNb)][fInd])) if self.sizeToProba else int(keyRadius)
                        # Draws circle on inferred markers (size depends on probability)
                        self.log.LogText(4, 'VideoPlayer: On cam%d, marker \'%s\' is drawn at (%d, %d) with r=%d' % (camNb, keyName, xKey, yKey, rKey))
                        img = cv2.circle(img, (xKey, yKey), rKey, self.keyColors[keyInd], thickness=cv2.FILLED)

                # Resize images when full
                if resize:
                    img = cv2.resize(img, (imgWidth // 2, imgHeight // 2))

                # Rotate image to align monitoring with setup
                if self.rotateCamList[camNb] == 90:
                    img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                elif self.rotateCamList[camNb] == -90:
                    img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                elif self.rotateCamList[camNb] == 180:
                    img = cv2.rotate(img, cv2.ROTATE_180)

                # Add infos in camera views
                if useCyclop.value:
                    xText = 10 if camNb == 0 else imgMonitDim[1] - 145
                    sText = '(showing cyclop)'
                    img = cv2.putText(img, sText, (xText, imgMonitDim[0]-10), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=0)
                else:
                    xText = 10 if camNb == 0 else imgMonitDim[1] - 200
                    sText = 'Cam%d ' % camNb + '(%d fish detected)' % nFishDetect2D
                    img = cv2.putText(img, sText, (xText, imgMonitDim[0]-10), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=0)

                # Places updated image in 2-images upper panel (for monitoring)
                imgPanel[:imgMonitDim[0], camNb*imgMonitDim[1]:(camNb+1)*imgMonitDim[1]] = img
                self.log.LogText(4, 'VideoPlayer: imgPanel created for imgIndex %d' % imgIndex.value)

            # Send 3D position to rendering via UDP
            if sendPos3D.value:
                # Send data
                message = '%.3f,%.3f,%.3f' % tuple(res3D['pos(Cyclop)'][fInd])
                UDPServerSocket.sendto(message.encode(), UDPserverRendering)

            # Add performance text to panel
            # sPerf = 'imgIndex=%d/%d  time=%.1f/%.1f' % (fInd, nFrames.value, fInd/framerate.value, nFrames.value/framerate.value)
            # imgPanel = cv2.putText(imgPanel, sPerf, (imgMonitDim[1] - 160, 20), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=0)

            # Waits necessary time for correct speed playback
            t1 = time.time_ns()
            if speed.value >= 1.0:
                tPad = 1.0/framerate.value - float(t1-t0)/1E9                # In seconds
            else:
                tPad = 1.0/speed.value/framerate.value - float(t1-t0)/1E9    # In seconds
            if tPad > 0:
                time.sleep(tPad)
                self.log.LogText(3, 'VideoPlayer: (%d) pad=%.1f ms' % (fInd, 1000*tPad))

            # Shows panel
            cv2.imshow(windowName, imgPanel)
            cv2.waitKey(1)

            # Get new time
            t0 = time.time_ns()

            # Update video output recording
            if saveVideos.value:
                videoOut.write(imgPanel)
                self.log.LogText(3, ' VideoPlayer: output video writers updated')

            # Increments image index if playing
            if play.value:
                if speed.value > 1:
                    imgIndex.value += int(speed.value)
                else:
                    imgIndex.value += 1

        if sendPos3D.value:
            # Closes UDP socket
            UDPServerSocket.close()

        # End nicely
        cv2.destroyAllWindows()


    def Plot3DPlayer(self, plotViews=['-x+y']):     # ['-y-x', '-x+z', '-y+z']
        """Starts 3D plot player with tracking and DLC results (THREAD)"""

        self.log.LogText(1, 'Plot3DPlayer() called')

        # Set initial control flags
        play.value = False
        playStarted = False
        stopPlayer.value = False

        # Full path with filename basis
        fullNameBasis = '%s/%s/%s/%s' % (self.resultsDir, self.expID_M.value, self.subjectID_M.value, self.file_M.value)

        # Builds matplotlib colors for DLC markers
        keyPltColors = {}
        for keyInd, keyName in enumerate(self.keyNames):
            keyPltColors[keyName] = (self.keyColors[keyInd][2]/255, self.keyColors[keyInd][1]/255, self.keyColors[keyInd][0]/255)

        # Loads 3D results (triangulations)
        filename = fullNameBasis + self.ext3D + '.npy'
        if not os.path.exists(filename):
            self.log.LogText(1, 'Plot3DPlayer: Error opening 3D results file \'%s\', quitting' % file.value)
            return -1
        else:
            res3D = np.load(filename)
            # dt3D = res3D.dtype

        # Get number of frames qnd framerate
        nFrames.value = res3D['imgIndex'][-1]
        framerate.value = int(1 / (res3D['time'][1]-res3D['time'][0]))

        self.log.LogText(2, 'Plot3DPlayer: nFrames=%d (at %d fps)' % (nFrames.value, framerate.value))

        # Prepares animated 3D plot
        nPlots = len(plotViews)
        if nPlots == 1:
            fSize = (5, 5)
            spList = [111]
        elif nPlots == 2:
            fSize = (5, 10)
            spList = [121, 122]
        elif nPlots == 3:
            fSize = (10, 10)
            spList = [221, 222, 223]
        elif nPlots == 4:
            fSize = (10, 10)
            spList = [221, 222, 223, 224]
        fig = plt.figure(figsize=fSize)
        ticks = {}
        ticks['x'] = ticks['y'] = list(range(-10, 11, 5))
        ticks['z'] = list(range(0, 16, 5))
        lim = {}
        lim['x'] = lim['y'] = (-11, 11)
        lim['z'] = (-1, 16)
        plt.subplots_adjust(left=0.05, top=0.98, bottom=0.05, right=0.98)
        blitList = []
        scPlots = {}        # Scatter plots (positions and trail)
        qvPlots = {}        # Quiver plots (vectors)
        for pvi, pv in enumerate(plotViews):
            if len(pv) == 6:        # 3D plot
                xs, x, ys, y, zs, z = pv
                ax = fig.add_subplot(spList[pvi], projection='3d')
                scPlots[pv] = ax.scatter(0, 0, 0, c=0, s=0.2, marker='o', animated=True)
                if showTrack.value:
                    qvPlots[pv] = ax.quiver([0, 0, 0], [0, 0, 0], color=['r', 'g'])       # To draw vectors
                ax.set_zlabel(z.upper())
                ax.set_zlim(lim[z])
                ax.set_zticks(ticks[z])
                if zs == '-':
                    ax.invert_zaxis()
            elif len(pv) == 4:      # 2D plot
                xs, x, ys, y = pv
                ax = fig.add_subplot(spList[pvi])
                scPlots[pv] = ax.scatter(0, 0, c=0, s=0.2, marker='o', animated=True)
                if showTrack.value:
                    qvPlots[pv] = ax.quiver([0, 0], [0, 0], color=['k', 'b'])             # To draw vectors
            else:
                self.log.LogText(2, 'Plot3DPlayer: could not interpret plot view pv=\'%s\', ignoring' % pv)
                continue
            ax.set_xlabel(x.upper())
            ax.set_xlim(lim[x])
            ax.set_xticks(ticks[x])
            if xs == '-':
                ax.invert_xaxis()
            ax.set_ylabel(y.upper(), labelpad=(-8 if y == 'y' else 0))
            ax.set_ylim(lim[y])
            ax.set_yticks(ticks[y])
            if ys == '-':
                ax.invert_yaxis()
            ax.grid(linestyle='--', linewidth=0.75)
            blitList.append(scPlots[pv])
            if showTrack.value:
                qvPlots[pv].angles = 'xy'
                qvPlots[pv].scale_units = 'xy'
                qvPlots[pv].scale = 1
                qvPlots[pv].width = 0.004
                qvPlots[pv].headlength = 5
                blitList.append(qvPlots[pv])

        # Set window position
        mngr = plt.get_current_fig_manager()
        _, _, winWidth, winHeight = mngr.window.geometry().getRect()
        mngr.window.setGeometry(350, 10, winHeight, winWidth)

        t0 = time.time_ns()     # Initial time (for playback speed)
        imgIndex.value = 0
        fInd = -1
        pos = {}
        vel = {}
        gazeDir = {}

        if sendPos3D.value:
            # Starts connection with Rendering PC
            UDPServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Main loop
        while True:

            # If not playing yet, waits for play command
            if not playStarted:
                while not play.value: pass

                # Blit manager
                bm = BlitManager(fig.canvas, blitList)
                plt.show(block=False)
                plt.pause(.1)

                # Prepare video recording
                if saveVideos.value:
                    imgWidth, imgHeight = fig.canvas.get_width_height()
                    videoFilename = fullNameBasis + '_3D plots.mp4'
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    videoOut = cv2.VideoWriter(videoFilename, fourcc, framerate.value, (imgWidth, imgHeight), isColor=True)
                    self.log.LogText(2, ' VideoPlayer: output video writers created')

                playStarted = True
                self.log.LogText(2, 'Plot3DPlayer: Play received')

            # Stop player received
            if stopPlayer.value:
                # Close video output recording
                if saveVideos.value:
                    videoOut.release()
                    self.log.LogText(2, 'Plot3DPlayer: output video writers closed')

                self.log.LogText(2, 'Plot3DPlayer: stopPlayer received, quitting')
                break

            # Check if paused
            if not play.value and imgIndex.value == fInd:
                continue

            # Check end of file
            if imgIndex.value >= nFrames.value or imgIndex.value >= len(res3D['pos(Cyclop)']):
                if not saveVideos.value:
                    self.log.LogText(2, 'Plot3DPlayer: Reached end of video file, looping')
                    imgIndex.value = 0
                else:
                    self.log.LogText(2, 'Plot3DPlayer: Reached end of video file, quitting')
                    stopPlayer.value = True
                    continue

            # Jump to the desired frame when img index is changed by slider
            # if imgIndex.value != fInd + 1:
            #     self.log.LogText(2, 'Plot3DPlayer: imgIndex set to %d' % imgIndex.value)

            # Blocks current frame index
            fInd = imgIndex.value

            # Add performance text to panel
            # sPerf = 'imgIndex=%d/%d  time=%.2f/%.2f' % (fInd, nFrames.value, fInd/framerate.value, nFrames.value/framerate.value)

            # Waits necessary time for correct speed playback
            t1 = time.time_ns()
            if speed.value >= 1.0:
                tPad = 1.0/framerate.value - float(t1-t0)/1E9                # In seconds
            else:
                tPad = 1.0/speed.value/framerate.value - float(t1-t0)/1E9    # In seconds
            if tPad > 0:
                time.sleep(tPad)
                self.log.LogText(3, 'Plot3DPlayer: (%d) pad=%.1f ms' % (fInd, 1000*tPad))

            # Get new time
            t0 = time.time_ns()

            # Reset drawing positions
            pos['x'] = []
            pos['y'] = []
            pos['z'] = []
            pos['c'] = []
            pos['r'] = []

            if showTrack.value:
                # Plot triangulated detected position
                posField = 'pos(Cyclop)' if useCyclop.value else 'pos(0)'

                # Draws trail and current (therefore find+1)
                for fIndTrail in range(max(fInd-trailFrames.value+1, 0), fInd+1):
                    xPos, yPos, zPos = res3D[posField][fIndTrail]
                    if xPos == -1 and yPos == -1 and zPos == -1: continue
                    pos['x'].append(xPos)
                    pos['y'].append(yPos)
                    pos['z'].append(zPos)
                    pos['c'].append([(fInd - fIndTrail) / trailFrames.value] * 3)
                    pos['r'].append(1.0*res3D['proba(Cyclop)'][fIndTrail] if useCyclop.value else 1.0)

                # Draws heading and gazeDir vectors
                posInd = len(pos['x']) - 1
                if self.showVelocity:
                    vel['x'], vel['y'], vel['z'] = 0.5 * res3D['vel(Cyclop)'][fInd]
                else:
                    vel['x'], vel['y'], vel['z'] = 0, 0, 0
                if self.showGazeDir:
                    gazeDir['x'], gazeDir['y'], gazeDir['z'] = 2 * res3D['gazeDir'][fInd]
                else:
                    gazeDir['x'], gazeDir['y'], gazeDir['z'] = 0, 0, 0

            if showDLC.value:
                # Plot triangulated inferred DLC markers
                for keyName in self.keyNames:
                    xKey, yKey, zKey = res3D['pos(%s)' % keyName][fInd]
                    if xKey == -1 and yKey == -1 and zKey == -1: continue
                    rKey = 1.0 * res3D['proba(%s)' % keyName][fInd]
                    pos['x'].append(xKey)
                    pos['y'].append(yKey)
                    pos['z'].append(zKey)
                    pos['c'].append(keyPltColors[keyName])
                    pos['r'].append(rKey)

            # Update animation positions
            for pv in plotViews:
                if len(pv) == 6:    # 3D plot
                    _, x, _, y, _, z = pv
                    # scPlots[pv].set_offsets(list(zip(pos[x], pos[y], pos[z])))
                    # scPlots[pv].set_color(pos['c'])
                    # scPlots[pv].set_sizes(pos['r'])
                else:               # 2D plot
                    _, x, _, y = pv
                    scPlots[pv].set_offsets(list(zip(pos[x], pos[y])))
                    scPlots[pv].set_color(pos['c'])
                    scPlots[pv].set_sizes(pos['r'])
                    if showTrack.value:
                        qvPlots[pv].set_offsets([pos[x][posInd], pos[y][posInd]])
                        qvPlots[pv].set_UVC(U=[vel[x], gazeDir[x]], V=[vel[y], gazeDir[y]])
                        # if self.showVelocity:
                        #     qvPlots[pv].set_UVC(U=[vel[x]], V=[vel[y]])
                        # if self.showGazeDir:
                        #     qvPlots[pv].set_UVC(U=[gazeDir[x]], V=[gazeDir[y]])
            bm.update()

            # Update video output recording
            if saveVideos.value:
                # Convert canvas to image and to BGR
                img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
                img = img.reshape(fig.canvas.get_width_height()[::-1] + (3,))
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)      # RGB to BGR

                videoOut.write(img)
                self.log.LogText(3, ' Plot3DPlayer: output video writers updated')

            # Send 3D position to rendering via UDP
            if sendPos3D.value:
                # Send data
                message = '%.3f,%.3f,%.3f' % tuple(res3D['pos(Cyclop)'][fInd])
                UDPServerSocket.sendto(message.encode(), UDPserverRendering)

            # Increments image index if playing
            if play.value:
                if speed.value > 1:
                    imgIndex.value += int(speed.value)
                else:
                    imgIndex.value += 1

        if sendPos3D.value:
            # Closes UDP socket
            UDPServerSocket.close()

        plt.close()


    # Loads settings from file
    def LoadSettingsFile(self, settingsName, storeVariable='self'):
        """Loads specific settings to self or another object's attributes"""

        fname = 'Settings/' + settingsName + '.txt'
        if not os.path.isfile(fname):
            print('Error: could not find \'%s\' file' % settingsName)
            return

        with open(fname, 'r') as fSet:
            settingLines = fSet.readlines()
            for settingLine in settingLines:
                settingArgs = re.split('\t+', settingLine)
                if len(settingArgs) < 2 or settingArgs[0][0] == '#':
                    continue
                exec("{}.{}={}".format(storeVariable, *settingArgs))

        self.log.LogText(2, '"%s" loaded' % settingsName)

        # Updates log level
        self.log.logLevel = self.logLevel


# GUI for tracking
class ViewerUI(QWidget):

    def __init__(self, log, resultsDir, resLogFile, expID_M, subjectID_M, file_M):
        """Constructor"""

        # Log object
        self.log = log
        self.log.LogText(1, 'ViewerUI() called')
        self.resLogFile = resLogFile
        self.resultsDir = resultsDir
        self.expID_M = expID_M
        self.subjectID_M = subjectID_M
        self.file_M = file_M

        super().__init__()

        # Playing speeds dictionary
        self.speedDict = {'x 1/8': 0.125, 'x 1/4': 0.25, 'x 1/2': 0.5, 'x 1': 1, 'x 2': 2, 'x 4': 4, 'x 8': 8}

        # Inits
        self.resLog = None
        self.videoNbFrames = 0
        self.trackbarPos = 0

        # Load section UIs
        prevY = self.ViewerSettingsUI(posX=10, posY=0)
        prevY = self.SelectExperimentFileUI(posX=10, posY=prevY + 15)
        self.ControllerUI(posX=10, posY=prevY + 15)

        # Camera return visual
        # self.panel = QLabel(self)

        # General aspect of the window
        self.setFixedSize(260, 640)
        self.move(10, 10)
        self.setWindowTitle('VR4Nemo results viewer')
        self.show()

        self.log.LogText(1, 'ViewerUI launched')
        time.sleep(1)


    def ViewerSettingsUI(self, posX, posY):

        # Section title
        self.viewerSetLbl = QLabel('Settings', self)
        self.viewerSetLbl.setGeometry(posX, posY, 150, 30)
        self.viewerSetLbl.setStyleSheet("font-weight: bold")
        posY += 40

        # Player mode
        self.viewModeLbl = QLabel('View mode', self)
        self.viewModeLbl.setGeometry(posX + 20, posY, 100, 30)
        self.viewModeCombo = QComboBox(self)
        self.viewModeCombo.setGeometry(posX + 120, posY, 90, 30)
        self.viewModeCombo.addItems(['2D videos', '3D plots'])
        self.viewModeCombo.setEnabled(True)
        self.viewModeCombo.setCurrentIndex(viewMode.value - 2)
        self.viewModeCombo.currentIndexChanged.connect(self.ViewMode)
        posY += 40

        # Show DeepLabCut
        self.showDLCBtn = QPushButton('Show DLC', self)
        self.showDLCBtn.setGeometry(posX, posY, 240, 30)
        self.showDLCBtn.setCheckable(True)
        self.showDLCBtn.setChecked(showDLC.value)
        self.showDLCBtn.clicked.connect(self.ShowDLC)
        posY += 35

        # Show Tracking
        self.showTrackBtn = QPushButton('Show Track', self)
        self.showTrackBtn.setGeometry(posX, posY, 240, 30)
        self.showTrackBtn.setCheckable(True)
        self.showTrackBtn.setChecked(showTrack.value)
        self.showTrackBtn.clicked.connect(self.ShowTrack)
        posY += 35

        # Trail frames
        self.trailLbl = QLabel('Trail size (frames)', self)
        self.trailLbl.setGeometry(posX + 20, posY, 110, 30)
        self.trailSpinbox = QSpinBox(self)
        self.trailSpinbox.setGeometry(posX + 150, posY, 60, 30)
        self.trailSpinbox.setRange(1, 60)
        self.trailSpinbox.setSingleStep(1)
        self.trailSpinbox.setValue(trailFrames.value)
        self.trailSpinbox.setEnabled(showTrack.value)
        self.trailSpinbox.valueChanged.connect(self.TrailSize)
        posY += 35

        # Use cyclop (instead of detected position)
        self.useCyclopChkbox = QCheckBox('Use cyclop', self)
        self.useCyclopChkbox.setGeometry(posX + 10, posY, 110, 30)
        self.useCyclopChkbox.setCheckable(True)
        self.useCyclopChkbox.setChecked(useCyclop.value)
        self.useCyclopChkbox.setEnabled(showTrack.value)
        self.useCyclopChkbox.clicked.connect(self.UseCyclop)

        # Save output videos with overlay or plots 3D
        self.saveVideosChkbox = QCheckBox('Save video output', self)
        self.saveVideosChkbox.setGeometry(posX + 130, posY, 110, 30)
        self.saveVideosChkbox.setCheckable(True)
        self.saveVideosChkbox.setChecked(saveVideos.value)
        self.saveVideosChkbox.setEnabled(True)
        self.saveVideosChkbox.clicked.connect(self.SaveVideos)
        posY += 35

        self.log.LogText(2, 'ViewerUI settings')

        return posY

    def ViewMode(self):

        viewMode.value = 2 if self.viewModeCombo.currentText() == '2D videos' else 3
        self.log.LogText(2, 'ViewerUI: viewMode=%d' % viewMode.value)

    def TrailSize(self):

        trailFrames.value = self.trailSpinbox.value()
        self.log.LogText(2, 'ViewerUI: trailFrames is %d frames' % trailFrames.value)

    def ShowTrack(self):

        showTrack.value = self.showTrackBtn.isChecked()
        self.trailSpinbox.setEnabled(showTrack.value)
        self.useCyclopChkbox.setEnabled(showTrack.value)
        self.log.LogText(2, 'ViewerUI: showTrack %s' % ('checked' if showTrack.value else 'unchecked'))

    def ShowDLC(self):

        showDLC.value = self.showDLCBtn.isChecked()
        self.log.LogText(2, 'ViewerUI: showDLC %s' % ('checked' if showDLC.value else 'unchecked'))

    def UseCyclop(self):

        useCyclop.value = self.useCyclopChkbox.isChecked()
        self.log.LogText(2, 'ViewerUI: useCyclop %s' % ('checked' if useCyclop.value else 'unchecked'))

    def SaveVideos(self):

        saveVideos.value = self.saveVideosChkbox.isChecked()
        self.log.LogText(2, 'ViewerUI: saveVideos %s' % ('checked' if saveVideos.value else 'unchecked'))

    def SelectExperimentFileUI(self, posX, posY):

        # Section title
        self.selectionLbl = QLabel('Trial selection', self)
        self.selectionLbl.setGeometry(posX, posY, 150, 30)
        self.selectionLbl.setStyleSheet("font-weight: bold")
        posY += 40

        # Select results log file
        self.resLogFileBtn = QPushButton('Select resLog file', self)
        self.resLogFileBtn.setGeometry(posX, posY, 240, 30)
        self.resLogFileBtn.setCheckable(False)
        if self.resLogFile == '':
            self.resLogFileBtn.setEnabled(True)
            self.resLogFileBtn.clicked.connect(self.SelectResLogFile)
        posY += 35

        # Select subject
        self.subjLbl = QLabel('Subject', self)
        self.subjLbl.setGeometry(posX + 10, posY, 50, 30)
        self.subjCombo = QComboBox(self)
        self.subjCombo.setGeometry(posX + 70, posY, 170, 30)
        self.subjCombo.setEnabled(False)
        # self.subjCombo.currentIndexChanged.connect(self.SelectSubject)
        posY += 35

        # Select trial
        self.trialLbl = QLabel('Trial', self)
        self.trialLbl.setGeometry(posX + 10, posY, 50, 30)
        self.trialCombo = QComboBox(self)
        self.trialCombo.setGeometry(posX + 70, posY, 170, 30)
        self.trialCombo.setEnabled(False)
        # self.trialCombo.currentIndexChanged.connect(self.SelectTrialFile)
        posY += 35

        if self.resLogFile != '':
            self.resLogFileBtn.setEnabled(False)
            self.LoadResLogFile(self.resLogFile)

        self.log.LogText(2, 'ViewerUI select experiment file')

        return posY

    def SelectResLogFile(self):

        # Opens file selection dialog box
        selectedFile = QFileDialog.getOpenFileName(parent=self, caption='Select results file',
                                                   directory=os.chdir(self.resultsDir),  filter='log file (*.tsv)',)[0]
        # Reset subject and trial combo box
        self.subjCombo.clear()
        self.subjCombo.setEnabled(False)
        self.subjCombo.disconnect()
        self.trialCombo.clear()
        self.trialCombo.setEnabled(False)
        self.trialCombo.disconnect()

        # Set start widgets off
        self.startBtn.setEnabled(False)
        self.speedCombo.setEnabled(False)

        if selectedFile != '':
            self.LoadResLogFile(selectedFile)
            self.log.LogText(2, 'ViewerUI: resLog file selected \'%s\'' % selectedFile)
        else:
            self.subjList = []
            self.subjCombo.clear()
            self.subjCombo.setEnabled(False)
            self.log.LogText(2, 'ViewerUI: No resLog file selected')

    def LoadResLogFile(self, filename):

        # Loads results log file
        with open(filename) as fResLog:
            self.resLog = list(csv.reader(fResLog, delimiter='\t'))[1:]

        # Get list with unique values of subjects
        self.subjList = []
        for res in self.resLog:
            if res[1] in self.subjList: continue
            self.subjList.append(res[1])

        # Places it in subject ID combo box and activates
        self.subjCombo.clear()
        self.subjCombo.addItems(['Select subject'] + self.subjList)
        self.subjCombo.setCurrentIndex(0)
        self.subjCombo.setEnabled(True)
        self.subjCombo.currentIndexChanged.connect(self.SelectSubject)

    def SelectSubject(self):

        # Get selected subject index
        ind = self.subjCombo.currentIndex() - 1         # First is 'Select subject'
        if ind < 0:
            return

        # Get selected subject
        subjID = self.subjList[ind]

        # Get resLog lines where subjects is subjID
        self.resLogSubj = [resLine for resLine in self.resLog if resLine[1] == subjID]

        # Get trial list for that subject
        self.trialList = [resLine[4] for resLine in self.resLogSubj]

        # Places it in trial combo box and activates
        self.trialCombo.clear()
        self.trialCombo.addItems(['Select trial'] + self.trialList)
        self.trialCombo.setCurrentIndex(0)
        self.trialCombo.setEnabled(True)
        self.trialCombo.currentIndexChanged.connect(self.SelectTrialFile)

        # Set start widgets off
        self.startBtn.setEnabled(False)
        self.speedCombo.setEnabled(False)

        self.log.LogText(2, 'ViewerUI: Subject selected \'%s\'' % subjID)

    def SelectTrialFile(self):

        # Get selected trial index
        ind = self.trialCombo.currentIndex() - 1    # First is 'Select trial'
        if ind < 0:
            return

        # And store expID, subjectID and file in the viewer properties
        self.expID_M.value = self.resLogSubj[ind][0]
        self.subjectID_M.value = self.resLogSubj[ind][1]
        self.file_M.value = self.resLogSubj[ind][4]

        # Updates widgets status
        self.startBtn.setEnabled(True)
        self.speedCombo.setEnabled(True)

        self.log.LogText(2, 'ViewerUI: Trial file selected \'%s\'' % file.value)

    def ControllerUI(self, posX, posY):

        # Section title
        self.controllerLbl = QLabel('Controller', self)
        self.controllerLbl.setGeometry(posX, posY, 150, 30)
        self.controllerLbl.setStyleSheet("font-weight: bold")
        posY += 40

        # Starts player
        self.startBtn = QPushButton('Start player', self)
        self.startBtn.setGeometry(posX, posY, 117, 30)
        self.startBtn.setEnabled(False)
        self.startBtn.clicked.connect(self.StartPlayer)

        # Stop button
        self.stopBtn = QPushButton('Stop player', self)
        self.stopBtn.setGeometry(posX + 123, posY, 117, 30)
        self.stopBtn.setEnabled(False)
        self.stopBtn.clicked.connect(self.StopPlayer)
        posY += 45

        # -10 frames button
        self.b10Btn = QPushButton('-10', self)
        self.b10Btn.setGeometry(posX, posY, 30, 30)
        self.b10Btn.setEnabled(False)
        self.b10Btn.clicked.connect(self.B10)
        # -1 frames button
        self.b1Btn = QPushButton('-1', self)
        self.b1Btn.setGeometry(posX + 35, posY, 30, 30)
        self.b1Btn.setEnabled(False)
        self.b1Btn.clicked.connect(self.B1)
        # Play/Pause button
        self.playPauseBtn = QPushButton('Play', self)
        self.playPauseBtn.setGeometry(posX + 70, posY, 100, 30)
        self.playPauseBtn.setCheckable(True)
        self.playPauseBtn.setEnabled(False)
        self.playPauseBtn.clicked.connect(self.PlayPause)
        # -1 frames button
        self.f1Btn = QPushButton('+1', self)
        self.f1Btn.setGeometry(posX + 175, posY, 30, 30)
        self.f1Btn.setEnabled(False)
        self.f1Btn.clicked.connect(self.F1)
        # +10 frames button
        self.f10Btn = QPushButton('+10', self)
        self.f10Btn.setGeometry(posX + 210, posY, 30, 30)
        self.f10Btn.setEnabled(False)
        self.f10Btn.clicked.connect(self.F10)
        posY += 35

        # Play speed
        self.speedLbl = QLabel('Play speed', self)
        self.speedLbl.setGeometry(posX + 50, posY, 80, 30)
        self.speedCombo = QComboBox(self)
        self.speedCombo.addItems(self.speedDict.keys())
        self.speedCombo.setGeometry(posX + 150, posY, 60, 30)
        self.speedCombo.setCurrentIndex(3)
        self.speedCombo.setEnabled(False)
        self.speedCombo.currentIndexChanged.connect(self.SelectSpeed)
        posY += 45

        # Images trackbar
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setFocusPolicy(Qt.NoFocus)
        self.slider.setGeometry(posX, posY, 240, 30)
        self.slider.setEnabled(False)
        self.slider.setVisible(False)
        posY += 30

        self.slider.sliderMoved.connect(self.SliderSetImgIndex)
        self.slider.setValue(0)
        self.sliderLblL = QLabel('', self)
        self.sliderLblL.setGeometry(posX, posY, 55, 30)
        self.sliderLblL.setAlignment(Qt.AlignCenter)
        # self.sliderLblL.setStyleSheet("QLabel { font-weight: bold; }")
        self.sliderLblL.setVisible(False)
        self.sliderLblR = QLabel('', self)
        self.sliderLblR.setGeometry(posX + 185, posY, 55, 30)
        self.sliderLblR.setAlignment(Qt.AlignCenter)
        # self.sliderLblR.setStyleSheet("QLabel { font-weight: bold; }")
        self.sliderLblR.setVisible(False)
        posY += 45

        self.log.LogText(2, 'ViewerUI controller')

        return posY

    def StartPlayer(self):

        # Sends the startPlayer command to the viewer
        startPlayer.value = True

        # Updates widgets status
        self.saveVideosChkbox.setEnabled(False)
        self.resLogFileBtn.setEnabled(False)
        self.subjCombo.setEnabled(False)
        self.trialCombo.setEnabled(False)
        self.startBtn.setEnabled(False)
        self.stopBtn.setEnabled(True)
        self.viewModeCombo.setEnabled(False)
        self.playPauseBtn.setEnabled(True)

        # Slider
        time.sleep(0.05)        # Give time to player to feed nFrames.value
        self.SliderThread = threading.Thread(target=self.SliderUpdateCursor, args=())
        self.sliderLblL.setEnabled(True)
        self.sliderLblR.setEnabled(True)
        self.slider.setEnabled(True)
        if not self.SliderThread.is_alive():
            self.log.LogText(2, 'ViewerUI: Starting slider thread')
            self.SliderThread.start()

        self.log.LogText(2, 'ViewerUI: [Start player] button pressed (player started)')

    def StopPlayer(self):

        # Sends the stop player command to the viewer
        stopPlayer.value = True
        play.value = False
        self.log.LogText(2, 'ViewerUI: Stop button pressed')

        # Updates widgets status
        self.saveVideosChkbox.setEnabled(True)
        self.startBtn.setEnabled(True)
        self.stopBtn.setEnabled(False)
        self.playPauseBtn.setEnabled(False)
        self.playPauseBtn.setChecked(False)
        self.playPauseBtn.setText('Play')
        self.viewModeCombo.setEnabled(True)
        self.resLogFileBtn.setEnabled(True)
        self.subjCombo.setEnabled(True)
        self.trialCombo.setEnabled(True)

        # Update slider widget and thread
        self.slider.setValue(0)
        self.slider.setEnabled(False)
        self.slider.setVisible(False)
        self.sliderLblL.setText('')
        self.sliderLblL.setEnabled(False)
        self.sliderLblL.setVisible(False)
        self.sliderLblR.setText('')
        self.sliderLblR.setEnabled(False)
        self.sliderLblR.setVisible(False)

    def PlayPause(self):

        self.log.LogText(2, 'ViewerUI: [%s] button pressed' % ('Pause' if play.value else 'Play'))

        # Sends the play command to the viewer
        play.value = not play.value

        # Updates widgets status
        self.playPauseBtn.clicked.disconnect()
        self.playPauseBtn.setText('Pause' if play.value else 'Play')
        self.playPauseBtn.setChecked(play.value)
        self.playPauseBtn.clicked.connect(self.PlayPause)
        self.b10Btn.setEnabled(not play.value)
        self.b1Btn.setEnabled(not play.value)
        self.f1Btn.setEnabled(not play.value)
        self.f10Btn.setEnabled(not play.value)

    def B10(self):
        self.log.LogText(2, 'ViewerUI: [-10] button pressed')
        imgIndex.value = max(0, imgIndex.value - 10)

    def B1(self):
        self.log.LogText(2, 'ViewerUI: [-1] button pressed')
        imgIndex.value = max(0, imgIndex.value - 1)

    def F1(self):
        self.log.LogText(2, 'ViewerUI: [+1] button pressed')
        imgIndex.value = min(nFrames.value-1, imgIndex.value + 1)

    def F10(self):
        self.log.LogText(2, 'ViewerUI: [+10] button pressed')
        imgIndex.value = min(nFrames.value-1, imgIndex.value + 10)

    def SelectSpeed(self):

        # Get selected speed and stores it in viewer property
        speedStr = self.speedCombo.currentText()
        speed.value = self.speedDict[speedStr]

        self.log.LogText(2, 'ViewerUI: Speed set to %s' % speedStr)

    def SliderSetImgIndex(self, position):
        imgIndex.value = position
        self.log.LogText(3, 'ViewerUI: Slider set imgIndex to %d' % position)

    def SliderUpdateCursor(self):

        while nFrames.value == 0:   # While player not ready (ie video or results data not loaded)
            continue

        self.log.LogText(1, 'ViewerUI: Slider length is %d' % nFrames.value)
        self.slider.setRange(0, nFrames.value)
        self.slider.setEnabled(True)
        self.slider.setVisible(True)
        self.sliderLblL.setVisible(True)
        self.sliderLblR.setVisible(True)
        imgIndexPrev = -1
        while not stopPlayer.value:
            if nFrames.value != 0 and imgIndexPrev != imgIndex.value:
                self.slider.disconnect()
                self.slider.setValue(imgIndex.value)
                self.slider.sliderMoved.connect(self.SliderSetImgIndex)
                mm, ss = divmod(imgIndex.value/framerate.value, 60)
                labelL = '%02.0f:%05.2f\n(%d)' % (mm, ss, imgIndex.value)
                mm, ss = divmod(nFrames.value/framerate.value, 60)
                labelR = '%02.0f:%05.2f\n(%d)' % (mm, ss, nFrames.value)
                self.sliderLblL.setText(labelL)
                self.sliderLblR.setText(labelR)
                imgIndexPrev = imgIndex.value
                if stopPlayer.value:
                    imgIndex.value = 0
                    self.slider.setValue(0)
                    break

        self.StopPlayer()
        self.log.LogText(2, 'ViewerUI: Quitting SliderUpdateCursor() thread')


    def closeEvent(self, event):

        self.log.LogText(2, 'ViewerUI: Sending stop and quit commands to Viewer')

        # Soft quit
        stopPlayer.value = True
        time.sleep(0.05)
        quit.value = True
        time.sleep(0.05)

        # Quitting Qt application
        QApplication.instance().quit


class Log:
    """Class used to safely log the ongoing of the program (also used for debugging)"""

    def __init__(self, logLevel=int, showTime=True, __output=''):
        """Use output='' for console writing"""

        # self.__lock = threading.Lock()
        self.logLevel = logLevel
        self.showTime = showTime
        if showTime:
            self.startTime = time.time_ns()
        if __output != '':
            self.__outToFile = True
            self.__stdoutCopy = sys.stdout
            sys.stdout = open(__output, 'wb')
        else:
            self.__outToFile = False

    def __del__(self):  # Called when destroying object

        # del self.__lock
        if self.__outToFile:
            sys.stdout.flush()
            sys.stdout = self.__stdoutCopy

    def LogText(self, level, text):

        if self.logLevel >= level:
            # self.__lock.acquire()
            if self.showTime:
                t = float(time.time_ns() - self.startTime) / 1E9
                print('%10.6f\t' % t + '  ' * (level - 1) + text)
            else:
                print('  ' * (level - 1) + text)
            # self.__lock.release()


class BlitManager:
    def __init__(self, canvas, animated_artists=()):
        """
        Parameters
        ----------
        canvas : FigureCanvasAgg
            The canvas to work with, this only works for sub-classes of the Agg
            canvas which have the `~FigureCanvasAgg.copy_from_bbox` and
            `~FigureCanvasAgg.restore_region` methods.

        animated_artists : Iterable[Artist]
            List of the artists to manage
        """
        self.canvas = canvas
        self._bg = None
        self._artists = []

        for a in animated_artists:
            self.add_artist(a)

        # grab the background on every draw
        self.cid = canvas.mpl_connect("draw_event", self.on_draw)

    def on_draw(self, event):
        """Callback to register with 'draw_event'."""
        cv = self.canvas
        if event is not None:
            if event.canvas != cv:
                raise RuntimeError
        self._bg = cv.copy_from_bbox(cv.figure.bbox)
        self._draw_animated()

    def add_artist(self, art):
        """
        Add an artist to be managed.

        Parameters
        ----------
        art : Artist

            The artist to be added.  Will be set to 'animated' (just
            to be safe).  *art* must be in the figure associated with
            the canvas this class is managing.

        """
        if art.figure != self.canvas.figure:
            raise RuntimeError
        art.set_animated(True)
        self._artists.append(art)

    def _draw_animated(self):
        """Draw all of the animated artists."""
        fig = self.canvas.figure
        for a in self._artists:
            fig.draw_artist(a)

    def update(self):
        """Update the screen with animated artists."""
        cv = self.canvas
        fig = cv.figure
        # paranoia in case we missed the draw event,
        if self._bg is None:
            self.on_draw(None)
        else:
            # restore the background
            cv.restore_region(self._bg)
            # draw all of the animated artists
            self._draw_animated()
            # update the GUI state
            cv.blit(fig.bbox)
        # let the GUI event loop process anything it has to do
        cv.flush_events()


# Starts everything (if this is the main process)
if __name__ == '__main__':

    # Move to TrackingMaster.py directory (if not already)
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Start Viewer
    myViewer = Viewer()

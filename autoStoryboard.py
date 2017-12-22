
#用来刷cut的，选择批量视频，会自动检测分段，然后生成中间的截图，会问一行多少张图。根据视频文件命名
#待完善：更好的判断算法
#时间码算出来不对

import scenedetect
import tkinter as tk
from tkinter import filedialog
import numpy as np
import cv2
import os
import sys
import subprocess

root = tk.Tk()
root.withdraw()
filez = filedialog.askopenfilenames(parent=root,title='选择文件')
file_list = list(filez)
detector_list = [scenedetect.detectors.ContentDetector()
]
directory = filedialog.askdirectory(parent=root,title='选择分镜图保存的位置')
print("一行几张图？（建议5）")
cols=int(input())
print("生成的长图的宽度是？（像素1000）")
maxWidth=int(input())
def getTimeCode(frameNo, video_fps,show_msec = True):
    time_msec=(1000.0 * frameNo) / float(video_fps) 
    out_nn, timecode_str = int(time_msec), ''

    base_msec = 1000 * 60 * 60  # 1 hour in ms
    out_HH = out_nn // base_msec
    out_nn -= out_HH * base_msec

    base_msec = 1000 * 60       # 1 minute in ms
    out_MM = out_nn // base_msec
    out_nn -= out_MM * base_msec

    base_msec = 1000            # 1 second in ms
    out_SS = out_nn // base_msec
    out_nn -= out_SS * base_msec

    if show_msec:
        timecode_str = "%02d:%02d:%02d.%02d" % (out_HH, out_MM, out_SS, out_nn)
    else:
        timecode_str = "%02d:%02d:%02d" % (out_HH, out_MM, out_SS)

    return timecode_str 
def combinePics(frame_list,cols,maxWidth): 
    frameNum=len(frame_list)
    mod=frameNum % cols
    height, width = frame_list[0].shape[:2]
    re_width=maxWidth//cols
    r = re_width/width
    re_height=int(height * r)
    dim = (re_width,re_height)
    blank_image = np.zeros((re_height,re_width,3), np.uint8)
    if frameNum>cols: 
        for i in range(0,(frameNum // cols)+1):
            for j in range(i*cols,i*cols+cols):
                if j==i*cols:
                    #first pic of one row
                    row = cv2.resize(frame_list[j], dim, interpolation = cv2.INTER_AREA)       
                else:
                     #if no frame available, add black image
                    if (i==(frameNum // cols) and (j>(frameNum-cols+mod))):
                        vis = np.concatenate((row, blank_image), axis=1)
                    else:
                        img=cv2.resize(frame_list[j], dim, interpolation = cv2.INTER_AREA)
                        vis = np.concatenate((row, img), axis=1)
                    row=vis
            if i==0:
                col=row
            else:
                temp=np.concatenate((col, row), axis=0)
                col=temp
    else:
        for i in range(0,frameNum):
            if i==0:
                row = cv2.resize(frame_list[0], dim, interpolation = cv2.INTER_AREA)
            else:
                  img=cv2.resize(frame_list[i], dim, interpolation = cv2.INTER_AREA)
                  vis = np.concatenate((row, img), axis=1)
                  row=vis
            col=row
    return col
try:
    for path in file_list:
        filename=os.path.splitext(os.path.basename(path))[0]
        print("分析“%s”中……"%filename)
        scene_list = []
        cap = cv2.VideoCapture(path) #video_name is the video being called
        videoHeight=cap.get(4)
        videoWidth=cap.get(3)
        #downscale if video is two large
        if videoWidth>320:
            downscale= int(videoWidth //320)
        else:
            downscale=None
        video_fps, frames_read = scenedetect.detect_scenes_file(path, scene_list, detector_list,downscale_factor=downscale)
        if len(scene_list)==0:
            print("cannot find cuts in file %s" % os.path.basename(path))
            continue
        else:
                # create new list with scene boundaries in milliseconds instead of frame #.
            print("scene lists:")
            print(scene_list)
            frame_list=[]
            for i in range(0,len(scene_list)+1):
                if i==0:
                    first=0
                    last=scene_list[i]
                elif i==(len(scene_list)):
                    fist=scene_list[i-1]
                    last=frames_read
                else:
                    first=scene_list[i-1]
                    last=scene_list[i]
                frame_no=(first+last)//2
                tc=getTimeCode(frame_no,video_fps) 
                cap.set(1,frame_no)
                ret, frame = cap.read() #read frame of the middle of two cuts
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(frame,tc,(10,int(videoHeight)-10), font, 2,(255,255,255),2,cv2.LINE_AA)
                frame_list.append(frame)
            finalPic=combinePics(frame_list,cols,maxWidth)            
            saveDirectory="%s/%s.jpg" %(directory,filename)
            cv2.imencode('.jpg',finalPic)[1].tofile(saveDirectory)
            print("%s 的分镜图保存完毕"%filename)
except Exception as e:
    print(e)


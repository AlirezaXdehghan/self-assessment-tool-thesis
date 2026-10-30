from GazeTracking import gaze_tracking
import cv2
from fer import FER
from collections import Counter

gaze = gaze_tracking.GazeTracking()
emotion_detector = FER()

def process_video(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    visualCues = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        # Process each frame
        visualCues.append(process_frame(frame))
    cap.release()
    return visualCues,int(fps)

def process_frame(frame):
    gaze.refresh(frame)
    if gaze.is_right() or gaze.is_left():
        gazeDirH = "sideways"
    else:
        gazeDirH = "center"
    if gaze.is_upward():
        gazeDirV = "upward"
    elif gaze.is_downward():
        gazeDirV = "downward"
    else:
        gazeDirV = ""
    emotion, _ = emotion_detector.top_emotion(frame)
    return (gazeDirH, gazeDirV, emotion)

def probabilityLC (gazeH,gazeV,emotion):
    PLCsideways, PLCupward, PLCdownward, PLCthinkface = 0.668, 0.8507, 0.615, 0.816
    Csideways, Cupward, Cdownward, Cthinkface, Cstill = 0,0,0,0,0
    if "sad" in emotion or "angry" in emotion:
        Cthinkface = 1
    if "sideways" in gazeH:
        Csideways = 1
    if "upward" in gazeV:
        Cupward = 1
    if "downward" in gazeV:
        Cdownward = 1
    LCP = 1 - (1-PLCupward)**Cupward * (1-PLCdownward)**Cdownward * (1-PLCthinkface)**Cthinkface * (1-PLCsideways)**Csideways
    return LCP

def final_probability(probabilityList):
    return sum(probabilityList)/len(probabilityList)

def face_eval(file):
    allEmotions,fps = process_video(file)
    LCprobs = []
    chunkedEmots = []
    for i in range(0, len(allEmotions), fps*10):
        chunk = allEmotions[i:i + fps*10]
        chunkedEmots.append(chunk)
    for ems in chunkedEmots:
        gazeH_detected, gazeV_detected, emots_detected = [],[],[]
        gazeH = [tup[0] for tup in ems]
        gazeV = [tup[1] for tup in ems]
        emot = [tup[2] for tup in ems]
        gazeH_counts = Counter(gazeH)
        gazeV_counts = Counter(gazeV)
        emots_counts = Counter(emot)
        for element, count in gazeH_counts.items():
            if count > fps*2:
                gazeH_detected.append(element)
        for element, count in gazeV_counts.items():
            if count > fps*2:
                gazeV_detected.append(element)
        for element, count in emots_counts.items():
            if count > fps*2:
                emots_detected.append(element)
        LCprobs.append(probabilityLC(gazeH_detected,gazeV_detected,emots_detected))

    return final_probability(LCprobs)
import cv2
import av
from aiortc import VideoStreamTrack
from picamera2 import Picamera2

class CameraTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.picam2 = Picamera2()
        self.picam2.start()

    async def recv(self):
        frame = self.picam2.capture_array()
        if frame is None:
            # Si frame vide, renvoyer frame noire
            import numpy as np
            frame = np.zeros((480,640,3), dtype=np.uint8)

        # Convertir BGR -> RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        video_frame = av.VideoFrame.from_ndarray(frame, format="rgb24")
        # Assigner pts et time_base simples
        video_frame.pts = None
        video_frame.time_base = None
        return video_frame

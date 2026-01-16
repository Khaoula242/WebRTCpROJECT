import asyncio
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
import cv2
from picamera2 import Picamera2
import numpy as np
import av

pcs = set()

class CameraTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.picam2 = Picamera2()
        self.picam2.start()

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        frame = self.picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        video_frame = av.VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame


async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    pc.addTrack(CameraTrack())

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })


async def index(request):
    return web.FileResponse("index.html")


app = web.Application()
app.router.add_get("/", index)
app.router.add_post("/offer", offer)

web.run_app(app, port=8080)

import asyncio
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
import cv2
from picamera2 import Picamera2
import av

pcs = set()

# ⚡ Track global de la caméra
class CameraTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.picam2 = Picamera2()
        self.picam2.configure(
            self.picam2.create_video_configuration(main={
                "size": (640, 480),
                "format": "RGB888"
            })
        )
        self.picam2.start()

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        frame = self.picam2.capture_array()
        # Picamera2 renvoie déjà RGB
        video_frame = av.VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame

camera_track = CameraTrack()

# ⚡ Endpoint WebRTC
async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pcs.add(pc)

    await pc.setRemoteDescription(offer)

    # Ajouter le track vidéo global
    pc.addTrack(camera_track)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })

# ⚡ Page web
async def index(request):
    return web.FileResponse("index.html")

app = web.Application()
app.router.add_get("/", index)
app.router.add_post("/offer", offer)

web.run_app(app, port=8080)

import asyncio
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from picamera2 import Picamera2
import av

pcs = set()  # Tous les RTCPeerConnection actifs

class CameraTrack(VideoStreamTrack):
    """
    Track global de la caméra CSI du Pi
    """
    def __init__(self):
        super().__init__()
        self.picam2 = Picamera2()
        self.picam2.configure(
            self.picam2.create_video_configuration(main={"size": (640, 480), "format": "RGB888"})
        )
        self.picam2.start()

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        frame = self.picam2.capture_array()
        video_frame = av.VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame

camera_track = CameraTrack()  # Une seule caméra pour tous les clients

# Endpoint WebRTC
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

# Page HTML
async def index(request):
    return web.FileResponse("index.html")

app = web.Application()
app.router.add_get("/", index)
app.router.add_post("/offer", offer)

if __name__ == "__main__":
    web.run_app(app, port=8080)

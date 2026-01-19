import asyncio
from aiohttp import web
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    RTCConfiguration,
    RTCIceServer,
    VideoStreamTrack
)
from picamera2 import Picamera2, MappedArray
import av

pcs = set()

# ================= CAMERA UNIQUE =================
picam2 = Picamera2()
picam2.configure(
    picam2.create_preview_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    )
)
picam2.start()


class CameraTrack(VideoStreamTrack):
    async def recv(self):
        pts, time_base = await self.next_timestamp()

        request = picam2.capture_request()
        with MappedArray(request, "main") as m:
            frame = m.array.copy()
        request.release()

        frame = av.VideoFrame.from_ndarray(frame, format="rgb24")
        frame.pts = pts
        frame.time_base = time_base
        return frame


camera_track = CameraTrack()


# ================= WEBRTC OFFER =================
async def offer(request):
    params = await request.json()

    config = RTCConfiguration(
        iceServers=[RTCIceServer(urls="stun:stun.l.google.com:19302")]
    )

    pc = RTCPeerConnection(config)
    pcs.add(pc)

    # ✅ TRÈS IMPORTANT : ajouter le track AVANT setRemoteDescription
    pc.addTrack(camera_track)

    await pc.setRemoteDescription(
        RTCSessionDescription(
            sdp=params["sdp"],
            type=params["type"]
        )
    )

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })


# ================= HTML =================
async def index(request):
    return web.FileResponse("index.html")


# ================= SERVER =================
app = web.Application()
app.router.add_get("/", index)
app.router.add_post("/offer", offer)

web.run_app(app, port=8080)


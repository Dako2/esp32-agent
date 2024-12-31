# signaling_server.py

import asyncio
import json
import os
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaBlackhole, MediaRelay
import base64
import cv2
import numpy as np
import openai

# Initialize OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")

openai.api_key = OPENAI_API_KEY

# Initialize a global relay and blackhole for media streams
relay = MediaRelay()
blackhole = MediaBlackhole()

pcs = set()

# Custom VideoStreamTrack to process frames
class VideoProcessor(VideoStreamTrack):
    """
    A VideoStreamTrack that processes incoming video frames.
    """
    def __init__(self, track):
        super().__init__()  # don't forget this!
        self.track = relay.subscribe(track)

    async def recv(self):
        frame = await self.track.recv()
        # Convert frame to numpy array
        img = frame.to_ndarray(format="bgr24")
        
        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', img)
        if not ret:
            print("Failed to encode frame.")
            return frame  # Return original frame
        
        # Convert to base64
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')

        # Send to OpenAI for analysis
        analysis = await analyze_image(jpg_as_text)

        # Optionally, you can overlay analysis on the frame or send it back to the client
        # For simplicity, we'll just print it
        print(f"Analysis: {analysis}")

        return frame

async def analyze_image(base64_image: str) -> str:
    """
    Sends the base64-encoded image to OpenAI's API for analysis.
    """
    try:
        # Construct the image data URL using data URI scheme
        image_data_url = f"data:image/jpeg;base64,{base64_image}"

        # Prepare the messages payload
        messages = [
            {
                "role": "user",
                "content": "Analyze the following image.",
                "image": image_data_url  # Hypothetical field; verify with API docs
            }
        ]

        print("Sending image to OpenAI API for analysis...")
        response = openai.ChatCompletion.create(
            model="gpt-4-vision",  # Replace with the correct model name if different
            messages=messages,
            temperature=0.5
        )

        analysis = response['choices'][0]['message']['content']
        return analysis

    except openai.error.OpenAIError as e:
        print(f"OpenAI API error: {e}")
        return "Error analyzing image."
    except Exception as e:
        print(f"Unexpected error: {e}")
        return "Unexpected error during analysis."

async def index(request):
    content = open('index.html', 'r').read()
    return web.Response(content_type='text/html', text=content)

async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params['sdp'], type=params['type'])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print(f"Connection state: {pc.connectionState}")
        if pc.connectionState == "failed" or pc.connectionState == "closed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        print(f"Track {track.kind} received")
        if track.kind == "video":
            # Replace the incoming video track with our processor
            pc.addTrack(VideoProcessor(track))
            print("Video track processed.")

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response({
        'sdp': pc.localDescription.sdp,
        'type': pc.localDescription.type
    })

async def on_shutdown(app):
    # Close all peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

if __name__ == "__main__":
    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_post('/offer', offer)
    app.on_shutdown.append(on_shutdown)
    web.run_app(app, port=8080)

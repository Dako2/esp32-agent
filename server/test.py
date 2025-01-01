import asyncio
from aiortc import RTCPeerConnection
from aiortc.contrib.media import MediaPlayer

async def main():
    pc = RTCPeerConnection()
    
    # Combined input for both video and audio
    player = MediaPlayer(
        "FaceTime HD Camera:MacBook Air Microphone",
        format="avfoundation",
        options={
            # Adjust these as needed based on your device capabilities
            "video_size": "1280x720",
            "framerate": "30.000000",
            "pixel_format": "uyvy422",  # if needed for compatibility
        }
    )
    
    # Add tracks to the PeerConnection
    # The MediaPlayer exposes `player.video` and `player.audio` if both are found
    if player.video:
        pc.addTrack(player.video)
    if player.audio:
        pc.addTrack(player.audio)

    # Create offer
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    print("LOCAL OFFER SDP:\n", pc.localDescription.sdp)

    # Keep running so the media stays open
    await asyncio.sleep(30)
    await pc.close()

if __name__ == "__main__":
    asyncio.run(main())

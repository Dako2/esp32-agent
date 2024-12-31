#!/usr/bin/env python3
import asyncio
import sys
import av
import logging
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer
from aiortc.mediastreams import MediaStreamTrack

# Optional: configure logging (or just use print statements).
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MJPEGVideoTrack(MediaStreamTrack):
    """
    A VideoStreamTrack that pulls frames from an MJPEG HTTP source (e.g. an ESP32-CAM).
    """
    kind = "video"  # required by aiortc

    def __init__(self, mjpeg_url: str):
        super().__init__()  # don't forget to initialize the parent class
        logger.debug(f"Opening MJPEG stream: {mjpeg_url}")

        # Attempt to open the MJPEG URL. If this fails for your camera,
        # remove 'format="mjpeg"' or try an ffmpeg intermediary.
        self.container = av.open(mjpeg_url, format="mjpeg")
        if not self.container or not self.container.streams.video:
            raise ValueError("No valid video stream found at the given MJPEG URL.")
        self.stream = self.container.streams.video[0]

    async def recv(self):
        """
        Grabs the next frame from the MJPEG stream, converts it to an AV VideoFrame,
        and returns it to aiortc for encoding and sending.
        """
        # We must read packets in a loop until we decode a frame.
        frame = None
        while True:
            # Read the next packet from the container.
            try:
                packet = next(self.container.demux(self.stream))
            except StopIteration:
                logger.error("End of MJPEG stream or unable to demux further packets.")
                await asyncio.sleep(1/30)  # Wait a bit before trying again (or return None)
                continue
            except av.AVError as e:
                logger.warning(f"PyAV Error demuxing packet: {e}")
                await asyncio.sleep(1/30)
                continue

            # Decode the packet into frames
            for decoded_frame in self.container.decode(packet):
                if decoded_frame is not None:
                    frame = decoded_frame
                    logger.debug(f"Decoded video frame PTS={frame.pts}, size={frame.width}x{frame.height}")
                    break

            if frame is not None:
                break

        # Convert to a standard pixel format (e.g., 'rgb24')
        new_frame = frame.reformat(format='rgb24')

        # Preserve timestamps for A/V sync (optional)
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base

        return new_frame


async def run_webRTC(mjpeg_url: str):
    """
    Creates a local RTCPeerConnection, attaches the MJPEGVideoTrack and an audio track
    from your default microphone, generates an SDP offer, and waits for your remote SDP answer.
    """
    logger.info("Creating RTCPeerConnection...")
    pc = RTCPeerConnection()

    # 1) Add the MJPEG video track
    video_track = MJPEGVideoTrack(mjpeg_url)
    logger.info("Adding video track to the RTCPeerConnection")
    pc.addTrack(video_track)

    # 2) Add audio track from your default microphone
    #    - On Linux, "default" is typically your default capture device.
    #    - On Windows, you may need to specify something else.
    logger.info("Creating MediaPlayer for default audio input...")
    audio_player = MediaPlayer("default")
    if audio_player.audio:
        logger.info("Adding audio track to the RTCPeerConnection")
        pc.addTrack(audio_player.audio)
    else:
        logger.warning("No audio track found. Check if your system/microphone is accessible.")

    # 3) Create an SDP offer and set it as local description
    logger.info("Creating local SDP offer...")
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    print("\n=== Local SDP Offer ===")
    print(pc.localDescription.sdp)
    print("=======================\n")
    print("Copy all the above SDP offer into your remote WebRTC peer.\n"
          "Then paste that peer's SDP answer below (finish with an empty line).")

    # 4) Wait for the remote SDP answer from stdin
    remote_sdp_lines = []
    while True:
        line = sys.stdin.readline().rstrip("\n")
        if line == "":
            break
        remote_sdp_lines.append(line)

    if not remote_sdp_lines:
        logger.info("No SDP answer provided, shutting down.")
        await pc.close()
        return

    remote_sdp_str = "\n".join(remote_sdp_lines)
    logger.info("Received remote SDP answer from stdin.")
    logger.debug(f"\n{remote_sdp_str}\n")

    answer = RTCSessionDescription(sdp=remote_sdp_str, type="answer")
    await pc.setRemoteDescription(answer)
    logger.info("Remote description set. WebRTC should now attempt to connect.\n")

    # Keep the event loop alive until Ctrl+C or some other condition
    print("Press Ctrl+C to exit...")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, closing RTCPeerConnection.")
    finally:
        await pc.close()
        logger.info("RTCPeerConnection closed, exiting.")


if __name__ == "__main__":
    """
    Usage:
      python mjpeg_webrtc.py http://<esp32_ip>/stream

    1) Run the script
    2) You'll get an SDP offer. Copy it to your remote peer (e.g., a browser),
       create an SDP answer, and paste that back into this script.
    3) If successful, you'll see the WebRTC connection form. The remote peer
       should receive both video (from MJPEG) and audio (from your mic).
    """
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <MJPEG_URL>")
        sys.exit(1)

    mjpeg_url = sys.argv[1]
    logger.info(f"Starting run_webRTC with URL={mjpeg_url}")

    asyncio.run(run_webRTC(mjpeg_url))

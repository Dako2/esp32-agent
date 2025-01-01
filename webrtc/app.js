const startButton = document.getElementById('startButton');
const espVideo = document.getElementById('espVideo');
const remoteVideo = document.getElementById('remoteVideo');

let espStream;
let localPeer;
let remotePeer;

const config = {
  iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
};

startButton.onclick = async () => {
  try {
    // 1. Make sure the ESP32 video is playing before captureStream() is available
    // If user gesture is required, we link it to the button click
    await espVideo.play();  

    // 2. Capture the stream from the video element
    // Note: Some browsers might only allow captureStream() if the user has interacted with the page
    espStream = espVideo.captureStream();
    if (!espStream) {
      alert('Could not capture stream from ESP video element. Check browser compatibility / CORS.');
      return;
    }
    console.log('Captured ESP32 camera stream:', espStream);

    // 3. Create two RTCPeerConnections (localPeer and remotePeer)
    localPeer = new RTCPeerConnection(config);
    remotePeer = new RTCPeerConnection(config);

    // 4. Add tracks from ESP32 stream to localPeer
    espStream.getTracks().forEach(track => {
      localPeer.addTrack(track, espStream);
    });

    // 5. ICE candidate handling: pass localPeer candidates to remotePeer and vice versa
    localPeer.onicecandidate = event => {
      if (event.candidate) {
        remotePeer.addIceCandidate(event.candidate)
          .catch(err => console.error('Error adding remote candidate', err));
      }
    };

    remotePeer.onicecandidate = event => {
      if (event.candidate) {
        localPeer.addIceCandidate(event.candidate)
          .catch(err => console.error('Error adding local candidate', err));
      }
    };

    // 6. When remotePeer gets tracks, display in remoteVideo
    remotePeer.ontrack = event => {
      // Typically event.streams[0] is the combined stream
      remoteVideo.srcObject = event.streams[0];
    };

    // 7. Create an offer from localPeer, setLocalDescription, then setRemoteDescription on remotePeer
    const offer = await localPeer.createOffer();
    await localPeer.setLocalDescription(offer);
    await remotePeer.setRemoteDescription(offer);

    // 8. remotePeer creates an answer, setLocalDescription, then localPeer sets it as remote description
    const answer = await remotePeer.createAnswer();
    await remotePeer.setLocalDescription(answer);
    await localPeer.setRemoteDescription(answer);

    console.log('WebRTC negotiation complete! The ESP32 stream is being looped back.');
  } catch (err) {
    console.error('Error starting WebRTC with ESP32 stream:', err);
    alert('Failed to start WebRTC: ' + err.message);
  }
};

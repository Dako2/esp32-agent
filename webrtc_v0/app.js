const startButton = document.getElementById('startButton');
const localVideo = document.getElementById('localVideo');
const remoteVideo = document.getElementById('remoteVideo');

let localStream;
let localConnection;
let remoteConnection;

const configuration = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' } // Public STUN server
  ]
};

startButton.onclick = async () => {
  startButton.disabled = true;
  
  // 1. Get user media
  try {
    localStream = await navigator.mediaDevices.getUserMedia({ 
      video: true, 
      audio: true 
    });
    localVideo.srcObject = localStream;
  } catch (err) {
    console.error('Error accessing media devices.', err);
    alert('Could not access camera/microphone. Check permissions.');
    return;
  }

  // 2. Create peer connections
  localConnection = new RTCPeerConnection(configuration);
  remoteConnection = new RTCPeerConnection(configuration);

  // 3. Add local stream tracks to the localConnection
  localStream.getTracks().forEach(track => {
    localConnection.addTrack(track, localStream);
  });

  // 4. Set up ICE candidate handlers
  localConnection.onicecandidate = event => {
    if (event.candidate) {
      remoteConnection.addIceCandidate(event.candidate)
        .catch(e => console.error('Error adding remote ICE candidate', e));
    }
  };

  remoteConnection.onicecandidate = event => {
    if (event.candidate) {
      localConnection.addIceCandidate(event.candidate)
        .catch(e => console.error('Error adding local ICE candidate', e));
    }
  };

  // 5. Remote connection ontrack -> show in remoteVideo
  remoteConnection.ontrack = event => {
    // The event.streams[0] contains the combined remote stream
    remoteVideo.srcObject = event.streams[0];
  };

  // 6. Create offer from local connection
  try {
    const offer = await localConnection.createOffer();
    await localConnection.setLocalDescription(offer);
    // 7. Set remoteConnection with local's offer
    await remoteConnection.setRemoteDescription(offer);

    // 8. Create an answer on the remote
    const answer = await remoteConnection.createAnswer();
    await remoteConnection.setLocalDescription(answer);
    // 9. Local sets remote's answer
    await localConnection.setRemoteDescription(answer);
  } catch (err) {
    console.error('Error creating/handling offer/answer', err);
  }
};

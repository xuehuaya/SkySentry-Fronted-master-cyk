<template>
  <div style="width: 100%; height: 100%; display: flex; flex-direction: column; background: #000;">
    <video
      id="srs-video"
      autoplay
      playsinline
      controls
      muted
      style="width: 100%; height: 100%; background: #000;"
    ></video>
  </div>
</template>

<script lang="ts" setup>
import { onMounted } from 'vue'

onMounted(async () => {
  const pc = new RTCPeerConnection()
  const video = document.getElementById('srs-video') as HTMLVideoElement

  pc.ontrack = (event) => {
    video.srcObject = event.streams[0]
  }

  const offer = await pc.createOffer({
    offerToReceiveAudio: true,
    offerToReceiveVideo: true
  })
  await pc.setLocalDescription(offer)

  const res = await fetch('http://127.0.0.1:1985/rtc/v1/play/', {
    method: 'POST',
    body: JSON.stringify({
      api: 'http://127.0.0.1:1985/rtc/v1/play/',
      streamurl: 'webrtc://127.0.0.1/live/test',
      clientip: null,
      sdp: offer.sdp
    })
  })

  const data = await res.json()
  const answer = new RTCSessionDescription({
    type: 'answer',
    sdp: data.sdp
  })
  await pc.setRemoteDescription(answer)
})
</script>

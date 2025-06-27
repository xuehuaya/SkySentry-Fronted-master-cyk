export const CURRENT_CONFIG = {

  // license
  appId: '160173', // You need to go to the development website to apply.
  appKey: '8f24659a9f62a6f6f168053890da880', // You need to go to the development website to apply.
  appLicense: 'epi/XSI7TXC9BX4Ypy/pQnEDKBPMYWSQ9BoY6XRyrZRrFyyw/osgxyk7itkX40ZVFPC5Upy+O6trQszXuPgaNut50xIy8AYTXiUr4tvDnDuuu2VezOo1DGHcS8hI/XyDcjtLHqElfpUosKGcu9eLQFC5aTnDOys3ipIfDLK7k60=', // You need to go to the development website to apply.

  // http
  baseURL: 'http://localhost:6789/', // This url must end with "/". Example: 'http://192.168.1.1:6789/'
  websocketURL: 'ws://localhost:6789/api/v1/ws', // Example: 'ws://192.168.1.1:6789/api/v1/ws'

  // livestreaming
  // RTMP  Note: This IP is the address of the streaming server. If you want to see livestream on web page, you need to convert the RTMP stream to WebRTC stream.
  rtmpURL: 'rtmp://localhost/live/', // Example: 'rtmp://192.168.1.1/live/'
  // GB28181 Note:If you don't know what these parameters mean, you can go to Pilot2 and select the GB28181 page in the cloud platform. Where the parameters same as these parameters.
  gbServerIp: 'Please enter the server ip.',
  gbServerPort: 'Please enter the server port.',
  gbServerId: 'Please enter the server id.',
  gbAgentId: 'Please enter the agent id',
  gbPassword: 'Please enter the agent password',
  gbAgentPort: 'Please enter the local port.',
  gbAgentChannel: 'Please enter the channel.',
  // RTSP
  rtspUserName: 'Please enter the username.',
  rtspPassword: 'Please enter the password.',
  rtspPort: '8554',
  // Agora
  agoraAPPID: 'Please enter the agora app id.',
  agoraToken: 'Please enter the agora temporary token.',
  agoraChannel: 'Please enter the agora channel.',

  // map
  // You can apply on the AMap website.
  amapKey: 'af0ba6265fc1d3e544cbded3af0e0237',

}

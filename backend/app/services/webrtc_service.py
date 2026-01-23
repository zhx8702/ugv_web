"""
WebRTC Service
提供低延迟WebRTC视频流
"""
import asyncio
import logging
import uuid
import time
from typing import Dict, Optional
import cv2
import numpy as np

try:
    from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack, RTCConfiguration, RTCIceServer
    from aiortc.contrib.media import MediaPlayer, MediaRelay
    from av import VideoFrame
    AIORTC_AVAILABLE = True
except ImportError:
    AIORTC_AVAILABLE = False
    logging.warning("aiortc not available - WebRTC functionality disabled")

# ICE 服务器配置
# ZeroTier 虚拟网络下不需要 STUN 服务器，设为空列表使用本地候选
ICE_SERVERS = []

logger = logging.getLogger(__name__)


# 只在 aiortc 可用时定义 VideoTrack 类
if AIORTC_AVAILABLE:
    class VideoTrack(VideoStreamTrack):
        """
        自定义视频轨道
        从video_stream服务获取帧并转换为WebRTC格式
        """

        def __init__(self, video_stream):
            super().__init__()
            self.video_stream = video_stream
            self.counter = 0

        async def recv(self):
            """接收视频帧"""
            pts, time_base = await self.next_timestamp()

            # 从video_stream获取帧（直接读取，不使用缓存）
            try:
                frame = self.video_stream.read_frame()
                if frame is not None:
                    frame = self.video_stream.process_frame(frame)

                if frame is None:
                    # 创建黑屏
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(frame, 'No Camera', (200, 240),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    if self.counter % 30 == 0:
                        logger.warning("WebRTC: No camera frame available")
                elif self.counter % 100 == 0:
                    logger.info(f"WebRTC: Sending frame {self.counter}, shape={frame.shape}")
            except Exception as e:
                logger.error(f"Error capturing frame: {e}")
                frame = np.zeros((480, 640, 3), dtype=np.uint8)

            # 转换为VideoFrame
            # OpenCV使用BGR，需要转换为RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 创建VideoFrame
            video_frame = VideoFrame.from_ndarray(frame_rgb, format='rgb24')
            video_frame.pts = pts
            video_frame.time_base = time_base

            self.counter += 1
            return video_frame


class WebRTCService:
    """
    WebRTC视频流服务

    提供低延迟(<100ms)的实时视频传输
    """

    def __init__(self, video_stream=None):
        """
        初始化WebRTC服务

        Args:
            video_stream: VideoStream服务实例
        """
        self.video_stream = video_stream
        self.peer_connections: Dict[str, RTCPeerConnection] = {}
        self.relay = None

        if not AIORTC_AVAILABLE:
            logger.error("aiortc not installed - WebRTC unavailable")
            self.available = False
            return

        self.available = True
        self.relay = MediaRelay()
        logger.info("WebRTC Service initialized")

    def is_available(self) -> bool:
        """检查WebRTC是否可用"""
        return self.available

    async def handle_offer(self, offer_data: dict) -> dict:
        """
        处理WebRTC offer

        Args:
            offer_data: {'sdp': str, 'type': str}

        Returns:
            {'sdp': str, 'type': str} - Answer数据
        """
        if not self.available:
            raise RuntimeError("WebRTC not available")

        if self.video_stream is None:
            raise RuntimeError("Video stream not set")

        # 创建RTCPeerConnection（带 ICE 服务器配置）
        config = RTCConfiguration(iceServers=ICE_SERVERS)
        pc = RTCPeerConnection(configuration=config)
        pc_id = str(uuid.uuid4())[:8]

        logger.info(f"Creating peer connection: {pc_id}")

        # 存储连接
        self.peer_connections[pc_id] = pc

        # 设置事件处理
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"Connection state: {pc.connectionState}")
            if pc.connectionState == "failed":
                logger.error(f"WebRTC connection failed for {pc_id}")
                await pc.close()
                if pc_id in self.peer_connections:
                    del self.peer_connections[pc_id]
            elif pc.connectionState == "connected":
                logger.info(f"WebRTC connection established for {pc_id}")

        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            logger.info(f"ICE connection state: {pc.iceConnectionState}")

        @pc.on("icegatheringstatechange")
        async def on_icegatheringstatechange():
            logger.info(f"ICE gathering state: {pc.iceGatheringState}")

        @pc.on("track")
        def on_track(track):
            logger.info(f"Track received: {track.kind}")

        # 创建视频轨道
        try:
            video_track = VideoTrack(self.video_stream)
            pc.addTrack(video_track)
            logger.info("Video track added")
        except Exception as e:
            logger.error(f"Error adding video track: {e}")
            raise

        # 处理offer
        try:
            offer = RTCSessionDescription(
                sdp=offer_data["sdp"],
                type=offer_data["type"]
            )

            await pc.setRemoteDescription(offer)
            logger.info("Remote description set")

            # 创建answer
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            logger.info("Local description set")

            return {
                "sdp": pc.localDescription.sdp,
                "type": pc.localDescription.type
            }

        except Exception as e:
            logger.error(f"Error handling offer: {e}")
            await pc.close()
            if pc_id in self.peer_connections:
                del self.peer_connections[pc_id]
            raise

    async def close_all_connections(self):
        """关闭所有连接"""
        logger.info("Closing all WebRTC connections")

        close_tasks = []
        for pc_id, pc in list(self.peer_connections.items()):
            close_tasks.append(pc.close())

        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)

        self.peer_connections.clear()
        logger.info("All connections closed")

    def get_stats(self) -> dict:
        """获取WebRTC统计信息"""
        return {
            'available': self.available,
            'active_connections': len(self.peer_connections),
            'connection_ids': list(self.peer_connections.keys())
        }


# 全局实例
_webrtc_service_instance: Optional[WebRTCService] = None


def get_webrtc_service(video_stream=None) -> WebRTCService:
    """
    获取WebRTC服务单例

    Args:
        video_stream: VideoStream实例

    Returns:
        WebRTCService实例
    """
    global _webrtc_service_instance
    if _webrtc_service_instance is None:
        _webrtc_service_instance = WebRTCService(video_stream)
    elif video_stream is not None:
        _webrtc_service_instance.video_stream = video_stream
    return _webrtc_service_instance

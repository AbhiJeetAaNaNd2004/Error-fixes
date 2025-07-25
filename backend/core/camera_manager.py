import cv2
import threading
import time
import queue
import numpy as np
from typing import Dict, Optional, List
import logging
from contextlib import contextmanager
from db import db_utils

logger = logging.getLogger(__name__)

class CameraStream:
    """Manages a single camera stream independently of face tracking."""
    
    def __init__(self, camera_config: Dict):
        self.config = camera_config
        self.camera_id = camera_config['id']
        self.camera_name = camera_config['camera_name']
        self.stream_url = camera_config['stream_url']
        self.fps = camera_config.get('fps', 30)
        
        # Stream state
        self.is_running = False
        self.cap = None
        self.thread = None
        self.shutdown_event = threading.Event()
        
        # Frame management
        self.latest_frame = None
        self.frame_lock = threading.RLock()
        self.frame_timestamp = 0
        
        # Statistics
        self.frames_captured = 0
        self.start_time = None
        self.last_frame_time = 0
        
    def start(self) -> bool:
        """Start the camera stream."""
        if self.is_running:
            logger.warning(f"Camera {self.camera_id} is already running")
            return False
            
        logger.info(f"Starting camera stream: {self.camera_name} (ID: {self.camera_id})")
        
        self.shutdown_event.clear()
        self.thread = threading.Thread(target=self._stream_worker, daemon=True)
        self.thread.start()
        
        # Wait a moment to see if the stream starts successfully
        time.sleep(0.5)
        return self.is_running
        
    def stop(self) -> bool:
        """Stop the camera stream."""
        if not self.is_running:
            logger.warning(f"Camera {self.camera_id} is not running")
            return False
            
        logger.info(f"Stopping camera stream: {self.camera_name} (ID: {self.camera_id})")
        
        self.shutdown_event.set()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3.0)
            
        self.is_running = False
        return True
        
    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Get the latest frame from the camera."""
        with self.frame_lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
            return None
            
    def get_stream_info(self) -> Dict:
        """Get information about the stream."""
        uptime = time.time() - self.start_time if self.start_time else 0
        actual_fps = self.frames_captured / uptime if uptime > 0 else 0
        
        return {
            'camera_id': self.camera_id,
            'camera_name': self.camera_name,
            'is_running': self.is_running,
            'frames_captured': self.frames_captured,
            'uptime_seconds': uptime,
            'actual_fps': round(actual_fps, 2),
            'configured_fps': self.fps,
            'last_frame_age': time.time() - self.last_frame_time if self.last_frame_time > 0 else None
        }
        
    def _stream_worker(self):
        """Main worker thread for capturing frames."""
        try:
            # Initialize video capture
            if self.stream_url.isdigit():
                stream_source = int(self.stream_url)
            else:
                stream_source = self.stream_url
                
            self.cap = cv2.VideoCapture(stream_source)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open camera stream: {self.stream_url}")
                return
                
            # Configure capture properties
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
            
            # Try to set FPS if supported
            try:
                self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            except Exception as e:
                logger.warning(f"Could not set FPS for camera {self.camera_id}: {e}")
                
            self.is_running = True
            self.start_time = time.time()
            frame_interval = 1.0 / self.fps
            
            logger.info(f"Camera {self.camera_id} stream started successfully")
            
            while not self.shutdown_event.is_set():
                try:
                    current_time = time.time()
                    
                    # Rate limiting
                    if current_time - self.last_frame_time < frame_interval:
                        time.sleep(0.001)  # Small sleep to prevent busy waiting
                        continue
                        
                    ret, frame = self.cap.read()
                    
                    if not ret:
                        logger.warning(f"Failed to read frame from camera {self.camera_id}")
                        time.sleep(0.1)
                        continue
                        
                    # Update frame data
                    with self.frame_lock:
                        self.latest_frame = frame
                        self.frame_timestamp = current_time
                        
                    self.frames_captured += 1
                    self.last_frame_time = current_time
                    
                except Exception as e:
                    if not self.shutdown_event.is_set():
                        logger.error(f"Error in camera {self.camera_id} stream worker: {e}")
                    time.sleep(0.1)
                    
        except Exception as e:
            logger.error(f"Fatal error in camera {self.camera_id} stream worker: {e}")
        finally:
            self._cleanup()
            
    def _cleanup(self):
        """Clean up resources."""
        self.is_running = False
        
        if self.cap:
            try:
                self.cap.release()
            except Exception as e:
                logger.error(f"Error releasing camera {self.camera_id}: {e}")
            finally:
                self.cap = None
                
        logger.info(f"Camera {self.camera_id} stream stopped and cleaned up")


class CameraManager:
    """Manages multiple camera streams independently of face tracking."""
    
    def __init__(self):
        self.streams: Dict[int, CameraStream] = {}
        self.manager_lock = threading.RLock()
        logger.info("CameraManager initialized")
        
    def load_camera_configs(self) -> List[Dict]:
        """Load camera configurations from database."""
        try:
            return db_utils.get_camera_configs()
        except Exception as e:
            logger.error(f"Failed to load camera configs: {e}")
            return []
            
    def initialize_cameras(self) -> bool:
        """Initialize all cameras from database configuration."""
        with self.manager_lock:
            try:
                camera_configs = self.load_camera_configs()
                
                if not camera_configs:
                    logger.warning("No camera configurations found")
                    return False
                    
                for config in camera_configs:
                    camera_id = config['id']
                    if camera_id not in self.streams:
                        self.streams[camera_id] = CameraStream(config)
                        logger.info(f"Initialized camera stream: {config['camera_name']} (ID: {camera_id})")
                        
                logger.info(f"Initialized {len(self.streams)} camera streams")
                return True
                
            except Exception as e:
                logger.error(f"Failed to initialize cameras: {e}")
                return False
                
    def start_camera(self, camera_id: int) -> bool:
        """Start a specific camera stream."""
        with self.manager_lock:
            if camera_id not in self.streams:
                # Try to load the camera config
                camera_configs = self.load_camera_configs()
                config = next((c for c in camera_configs if c['id'] == camera_id), None)
                
                if not config:
                    logger.error(f"Camera {camera_id} not found in configuration")
                    return False
                    
                self.streams[camera_id] = CameraStream(config)
                
            return self.streams[camera_id].start()
            
    def stop_camera(self, camera_id: int) -> bool:
        """Stop a specific camera stream."""
        with self.manager_lock:
            if camera_id not in self.streams:
                logger.warning(f"Camera {camera_id} not found")
                return False
                
            return self.streams[camera_id].stop()
            
    def start_all_cameras(self) -> Dict[int, bool]:
        """Start all configured camera streams."""
        with self.manager_lock:
            if not self.streams:
                self.initialize_cameras()
                
            results = {}
            for camera_id, stream in self.streams.items():
                results[camera_id] = stream.start()
                time.sleep(0.5)  # Stagger starts to avoid resource conflicts
                
            logger.info(f"Started {sum(results.values())} of {len(results)} cameras")
            return results
            
    def stop_all_cameras(self) -> Dict[int, bool]:
        """Stop all camera streams."""
        with self.manager_lock:
            results = {}
            for camera_id, stream in self.streams.items():
                results[camera_id] = stream.stop()
                
            logger.info(f"Stopped {sum(results.values())} of {len(results)} cameras")
            return results
            
    def get_camera_frame(self, camera_id: int) -> Optional[np.ndarray]:
        """Get the latest frame from a specific camera."""
        with self.manager_lock:
            if camera_id not in self.streams:
                return None
            return self.streams[camera_id].get_latest_frame()
            
    def get_camera_status(self, camera_id: int) -> Optional[Dict]:
        """Get status information for a specific camera."""
        with self.manager_lock:
            if camera_id not in self.streams:
                return None
            return self.streams[camera_id].get_stream_info()
            
    def get_all_camera_status(self) -> Dict[int, Dict]:
        """Get status information for all cameras."""
        with self.manager_lock:
            return {
                camera_id: stream.get_stream_info()
                for camera_id, stream in self.streams.items()
            }
            
    def is_camera_running(self, camera_id: int) -> bool:
        """Check if a specific camera is running."""
        with self.manager_lock:
            if camera_id not in self.streams:
                return False
            return self.streams[camera_id].is_running
            
    def get_running_cameras(self) -> List[int]:
        """Get list of currently running camera IDs."""
        with self.manager_lock:
            return [
                camera_id for camera_id, stream in self.streams.items()
                if stream.is_running
            ]
            
    def refresh_camera_configs(self) -> bool:
        """Refresh camera configurations from database."""
        with self.manager_lock:
            try:
                # Stop all cameras first
                self.stop_all_cameras()
                
                # Clear existing streams
                self.streams.clear()
                
                # Reinitialize with fresh configs
                return self.initialize_cameras()
                
            except Exception as e:
                logger.error(f"Failed to refresh camera configs: {e}")
                return False
                
    def shutdown(self):
        """Shutdown all cameras and cleanup."""
        logger.info("Shutting down CameraManager")
        with self.manager_lock:
            self.stop_all_cameras()
            
            # Wait for all threads to finish
            for stream in self.streams.values():
                if stream.thread and stream.thread.is_alive():
                    stream.thread.join(timeout=2.0)
                    
            self.streams.clear()
            
        logger.info("CameraManager shutdown complete")


# Global camera manager instance
_camera_manager = None
_manager_lock = threading.Lock()

def get_camera_manager() -> CameraManager:
    """Get the global camera manager instance."""
    global _camera_manager
    
    with _manager_lock:
        if _camera_manager is None:
            _camera_manager = CameraManager()
            _camera_manager.initialize_cameras()
            
        return _camera_manager

def shutdown_camera_manager():
    """Shutdown the global camera manager."""
    global _camera_manager
    
    with _manager_lock:
        if _camera_manager is not None:
            _camera_manager.shutdown()
            _camera_manager = None
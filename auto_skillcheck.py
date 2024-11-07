from typing import Union
import numpy as np
import cv2
from pynput.keyboard import Controller, KeyCode
from time import sleep
from utility import Utility
import pyautogui
from concurrent.futures import ProcessPoolExecutor

def capture_screen(monitor):
    """Capture the screen based on the monitor dimensions."""
    utility = Utility()
    return cv2.cvtColor(utility.get_sct(monitor), cv2.COLOR_BGR2RGB)

def process_image(img, low_white, high_white, low_red, high_red):
    """Process the image to find white and red areas."""
    # Create binary masks for white and red areas
    white_mask = cv2.inRange(img, low_white, high_white)
    red_mask = cv2.inRange(img, low_red, high_red)

    # Get coordinates of white and red regions
    white_cords = np.argwhere(white_mask != 0)
    red_cords = np.argwhere(red_mask != 0)

    return white_cords, red_cords

def auto_skillcheck(toggle: bool, is_target_active: bool,
                    window_rect: list, sct_monitor: Union[dict, str], keycode: object = KeyCode(0x43), DoctorMode: int = 0, slp: float = 0.0005, HeightWidth: tuple[int, int] = tuple['450', '450'], defSlep: float = 0.0):
    """Auto Skillcheck Function"""

    # Color range for white and red detection
    low_white, high_white = np.array([250, 250, 250]), np.array([255, 255, 255])
    low_red, high_red = np.array([160, 0, 0]), np.array([255, 30, 30])

    monitor = sct_monitor
    last_rect = None
    white_cords_buffer = []

    # Automatically get screen dimensions
    screen_width, screen_height = pyautogui.size()

    # Center of the screen
    center_x = screen_width // 2
    center_y = screen_height // 2

    if DoctorMode == 1:
        capture_height, capture_width = HeightWidth
    elif DoctorMode == 0:
        slp = defSlep
        capture_height = 100
        capture_width = 100

    # Calculate top and left positions
    top = center_y - (capture_height // 2)
    left = center_x - (capture_width // 2)

    with ProcessPoolExecutor() as executor:
        while toggle.value:
            if is_target_active.value:
                # Update monitor only if the window dimensions change
                if (window_rect != last_rect) and (sct_monitor == "default"):
                    monitor = {
                        "top": int(top),
                        "left": int(left),
                        "width": capture_width,
                        "height": capture_height
                    }
                    last_rect = monitor.copy()

                # Capture the screen in a separate process
                future_img = executor.submit(capture_screen, monitor)

                # Process the image without waiting for the result
                img = future_img.result()  # Wait here for the captured image
                future_process = executor.submit(process_image, img, low_white, high_white, low_red, high_red)

                # Update the buffer with white coordinates only if there are any
                white_cords, red_cords = future_process.result()  # Wait here for the processed image results
                if white_cords.size > 0:
                    white_cords_buffer.extend(map(tuple, white_cords))

                # Check for intersections using set operations
                if white_cords_buffer and red_cords.size > 0:
                    red_set = set(map(tuple, red_cords))
                    intersection = red_set.intersection(white_cords_buffer)

                    if intersection:
                        sleep(slp)
                        Controller().tap(keycode)
                        white_cords_buffer.clear()

                # Clear buffer if no red areas are detected
                if red_cords.size == 0:
                    white_cords_buffer.clear()
            else:
                break

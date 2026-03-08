import math
from config import *
from utils import clamp
from pygame.math import Vector2
from car import Car
import random
import pygame
pygame.init()
class AIDriver:
    def __init__(self, car: Car, waypoints):
        self.car = car
        self.waypoints = waypoints
        self.max_speed = AI_MAX_SPEED

    def update(self, dt):
        AI_speed_variable = random.randint(90, 105) / 100
        self.max_speed = AI_MAX_SPEED * AI_speed_variable
        if not self.waypoints: return
        target = Vector2(self.waypoints[self.car.current_waypoint])
        to_target = target - self.car.pos
        dist = to_target.length()
        desired_angle = math.degrees(math.atan2(-to_target.x, -to_target.y))
        angle_diff = (desired_angle - self.car.angle + 180) % 360 - 180
        steer_command = clamp(angle_diff / 45.0, -1.0, 1.0)
        self.car.steer_input = steer_command * 0.98
        align = max(0.0, 1.0 - abs(angle_diff) / 90.0)
        desired_speed = self.max_speed * align
        cur_speed = self.car.speed
        speed_error = desired_speed - cur_speed
        if speed_error > 60:
            target_throttle = clamp(speed_error / self.max_speed, 0.0, 1.0)
            self.car.brake = 0.0
            self.car.throttle += clamp(target_throttle - self.car.throttle, -THROTTLE_RAMP*dt, THROTTLE_RAMP*dt)
            self.car.throttle = clamp(self.car.throttle, 0.0, 1.0)
        elif speed_error < -50:
            self.car.brake = clamp((-speed_error) / self.max_speed, 0.05, 1.0)
            self.car.throttle = 0.0
        else:
            self.car.brake = 0.0
            self.car.throttle = clamp(self.car.throttle - THROTTLE_RAMP*dt*0.6, 0.0, 1.0)
        if dist < AI_LOOKAHEAD:
            self.car.current_waypoint = (self.car.current_waypoint + 1) % len(self.waypoints)

'''
                # Waypoints
                if track_file == "Practice_1.png":
                    wp_norm = [
                        (0.55, 0.80),(0.75,0.75),(0.80,0.70),(0.90,0.45),(0.75,0.30),
                        (0.60,0.20),(0.40,0.22),(0.24,0.32),
                        (0.20,0.55),(0.20,0.70),(0.25, 0.75)
                    ]
                elif track_file == "Track_1.png":
                    wp_norm = [
                        (0.50, 0.89),(0.65,0.89),(0.80,0.87),(0.85,0.85),(0.93,0.80),(0.95,0.70),(0.96,0.40),
                        (0.93,0.25),(0.82,0.11),(0.80,0.14),
                        (0.82,0.25),(0.80,0.27),(0.25,0.26),(0.17,0.30),(0.10,0.40),(0.04,0.45),(0.10,0.55),
                        (0.15,0.70),(0.20,0.89),(0.35,0.89),(0.45,0.88)
                    ]
                waypoints = []
                for nx, ny in wp_norm:
                    wx, wy = int(WORLD_W*nx), int(WORLD_H*ny)
                    snapped = snap_to_road(wx, wy, track_mask, radius=64, step=4)
                    waypoints.append(snapped if snapped else (wx, wy))
                    pygame.draw.circle(track_img, (255,0,0), (int(wx), int(wy)), 12)  # debug draw
'''

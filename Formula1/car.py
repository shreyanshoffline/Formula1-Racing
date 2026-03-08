import math
import pygame
import random
from pygame.math import Vector2
from config import *
import utils
from camera import Camera

class Car(pygame.sprite.Sprite):
    def __init__(self, img, pos, angle_deg=0.0, is_player=False):
        super().__init__()

        # --- Sprite Setup ---
        self.orig_img = pygame.transform.smoothscale(img, CAR_SCALE)
        self.image = self.orig_img
        self.rect = self.image.get_rect(center=pos)

        # --- Movement State ---
        self.pos = Vector2(pos)
        self.velocity = Vector2(0, 0)
        self.angle = angle_deg
        self.wheelbase = WHEELBASE

        # --- Controls / Inputs ---
        self.throttle = 0.0
        self.brake = 0.0
        self.steer_input = 0.0
        self.steer = 0.0
        self.drift = 0.0
        self.rpm = IDLE_RPM
        self.gear = 1
        self.engine_omega = self.rpm * 2 * math.pi / 60
        # --- RPM SYSTEM (visual only, does NOT affect physics) ---
        self.rpm = 900            # current rpm
        self.idle_rpm = 900      # idle rpm
        self.max_rpm = 8000      # redline
        self.current_gear = 1

        # simple gear speed ranges (mph or whatever units you're using)
        self.gear_speed_ranges = {
            1: (0, 25),
            2: (20, 45),
            3: (40, 65),
            4: (60, 90),
            5: (85, 200)
        }

        # --- Gameplay State ---
        self.is_player = is_player
        self.lap = 0
        self.passed_start_line = False
        self.current_waypoint = 0

    # ---------------------------------------------------------
    # Helper vectors
    # ---------------------------------------------------------
    @property
    def speed(self):
        return self.velocity.length()

    def world_forward(self):
        rad = math.radians(self.angle)
        return Vector2(-math.sin(rad), -math.cos(rad))

    def world_right(self):
        f = self.world_forward()
        return Vector2(f.y, -f.x)

    # ---------------------------------------------------------
    # Update car physics
    # ---------------------------------------------------------
    def update(self, dt, track_mask=None):
        # ----------------------------------------------------------------------
        # 1. BASIC ORIENTATION VECTORS
        # ----------------------------------------------------------------------
        heading = self.world_forward()
        right = self.world_right()

        # forward and lateral velocity components (px/s)
        v_f = self.velocity.dot(heading)
        v_l = self.velocity.dot(right)

        # ----------------------------------------------------------------------
        # 2. EARLY OFF-ROAD CHECK (used later for acceleration & penalties)
        # ----------------------------------------------------------------------
        is_offroad = False
        if track_mask:
            try:
                mx, my = int(self.pos.x), int(self.pos.y)
                if 0 <= mx < track_mask.get_width() and 0 <= my < track_mask.get_height():
                    px = track_mask.get_at((mx, my))
                    is_offroad = (px.r + px.g + px.b) <= 700
            except:
                pass

        # ----------------------------------------------------------------------
        # 3. ENGINE POWER CALCULATION (smooth exponential F1 curve)
        # ----------------------------------------------------------------------
        current_kph = utils.pxs_to_kph(abs(v_f))
        engine_factor = math.exp(-0.0025 * current_kph)
        engine_factor = utils.clamp(engine_factor, 0.12, 1.0)
        
        #self.update_engine_rpm(dt)
        #torque_mult = self.get_torque_multiplier()
        #gear_ratio_total = GEAR_RATIOS[self.gear] * FINAL_DRIVE
        #gear_force_mult = gear_ratio_total / GEAR_RATIOS[1]
        # ----------------------------------------------------------------------
        # 4. THROTTLE / BRAKE APPLICATION
        # ----------------------------------------------------------------------
        if self.throttle > 0:
            acc = FORWARD_ACCEL_PX * self.throttle * engine_factor
            if is_offroad:
                acc *= 0.25
            v_f += acc * dt

        if self.brake > 0:
            if v_f > 0:
                v_f -= BRAKE_DECEL_PX * self.brake * dt
            else:
                v_f -= REVERSE_ACCEL_PX * self.brake * dt

        # ----------------------------------------------------------------------
        # 5. PASSIVE DRAG, ROLLING RESISTANCE, AERO DRAG
        # ----------------------------------------------------------------------
        rolling_resist = 0.00023 * v_f * dt
        aero_drag = 0.00000062 * (v_f * abs(v_f)) * dt

        if v_f > 0:
            v_f -= rolling_resist + aero_drag
        elif v_f < 0:
            v_f += rolling_resist - aero_drag

        if self.throttle == 0 and self.brake == 0:
            v_f *= max(0.0, 1.0 - (1.0 - DRAG_FACTOR) * dt * 60.0)
            v_l *= 0.94

        v_f = max(min(v_f, MAX_FORWARD_SPEED), MAX_REVERSE_SPEED)

        # ----------------------------------------------------------------------
        # 6. LATERAL DAMPING (reduces sliding)
        # ----------------------------------------------------------------------
        lateral_damp_strength = utils.clamp(LATERAL_DAMP * dt, 0.0, 0.95)
        is_drifting = self.drift > 0.2

        if is_drifting:
            v_l -= v_l * lateral_damp_strength * 0.35
        else:
            v_l -= v_l * lateral_damp_strength

        grip_limit = max(30.0, TIRE_GRIP_BASE * PIXELS_TO_M * 0.03)
        if abs(v_l) > grip_limit:
            v_l = math.copysign(grip_limit, v_l)

        self.velocity = heading * v_f + right * v_l

        # ----------------------------------------------------------------------
        # 7. STEERING INPUT SMOOTHING
        # ----------------------------------------------------------------------
        self.steer = utils.clamp(
            self.steer + utils.clamp(self.steer_input - self.steer, -STEER_SPEED * dt, STEER_SPEED * dt),
            -1.0, 1.0
        )

        steer_dir = self.steer
        if v_f < -5:
            steer_dir = -steer_dir

        # ----------------------------------------------------------------------
        # 8. SPEED-DEPENDENT STEERING POWER (mph bands)
        # ----------------------------------------------------------------------
        mph = utils.pxs_to_mph(abs(v_f))

        if mph < 1.0:
            turn_strength = 0.0
        elif mph <= 4.0:
            t = (mph - 1.0) / 3.0
            turn_strength = 0 + (0.4 - 0) * t
        elif mph <= 15.0:
            t = (mph - 2.0) / 13.0
            turn_strength = 0.5 + (1.0 - 0.5) * t
        elif mph <= 30.0:
            t = (mph - 10.0) / 20.0
            turn_strength = 1.0 + (1.2 - 1.0) * t
        elif mph <= 50.0:
            t = (mph - 15.0) / 25.0
            turn_strength = 1.0 + (0.8 - 1.0) * t
        elif mph <= 75.0:
            t = (mph - 40.0) / 35.0
            turn_strength = 0.8 + (0.6 - 0.8) * t
        elif mph <= 125.0:
            t = (mph - 75.0) / 50.0
            turn_strength = 0.6 + (0.4 - 0.6) * t
        else:
            turn_strength = 0.25

        turn_strength = utils.clamp(turn_strength, 0.15, 1.7)
        allow_turn = mph > 1.0

        # ----------------------------------------------------------------------
        # 9. APPLY ROTATION (normal or drifting)
        # ----------------------------------------------------------------------
        if allow_turn and is_drifting:
            vel_dir = self.velocity.normalize() if self.velocity.length() > 1 else heading
            slip_angle = heading.cross(vel_dir)
            self.angle += slip_angle * 45.0 * dt
            self.angle += steer_dir * TURN_RATE * turn_strength * 1.7 * dt
        elif allow_turn:
            self.angle += steer_dir * TURN_RATE * turn_strength * dt

        # ----------------------------------------------------------------------
        # 10. CORNERING SPEED PENALTY
        # ----------------------------------------------------------------------
        corner_intensity = abs(self.steer) * abs(v_l)
        corner_pen = utils.clamp(corner_intensity / 800.0, 0.0, 1.0)
        v_f -= v_f * corner_pen * dt * 3.0

        if v_f < MAX_REVERSE_SPEED:
            v_f = MAX_REVERSE_SPEED

        self.velocity = heading * v_f + right * v_l

        # ----------------------------------------------------------------------
        # 11. POSITION UPDATE
        # ----------------------------------------------------------------------
        self.pos += self.velocity * dt

        # ----------------------------------------------------------------------
        # 12. OFF-ROAD PENALTY
        # ----------------------------------------------------------------------
        if track_mask:
            try:
                mx, my = int(self.pos.x), int(self.pos.y)
                if 0 <= mx < track_mask.get_width() and 0 <= my < track_mask.get_height():
                    px = track_mask.get_at((mx, my))
                    on_road = (px.r + px.g + px.b) > 700
                    if not on_road:
                        self.velocity *= 0.96
                        self.steer *= 0.85
            except Exception:
                pass


        # ----------------------------------------------------------------------
        # 13. SPRITE ROTATION UPDATE
        # ----------------------------------------------------------------------
        self.image = pygame.transform.rotozoom(self.orig_img, self.angle, 1.0)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
    
    def update_rpm(self, dt):
        speed = abs(self.speed)

        # determine gear based on speed
        for gear, (min_s, max_s) in self.gear_speed_ranges.items():
            if min_s <= speed <= max_s:
                self.current_gear = gear
                break

        min_s, max_s = self.gear_speed_ranges[self.current_gear]

        # calculate rpm target within gear range
        if max_s - min_s > 0:
            ratio = (speed - min_s) / (max_s - min_s)
        else:
            ratio = 0

        target_rpm = self.idle_rpm + ratio * (self.max_rpm - self.idle_rpm)

        # smooth interpolation (prevents jitter)
        smoothing = 8
        self.rpm += (target_rpm - self.rpm) * smoothing * dt

        # clamp
        if self.rpm < self.idle_rpm:
            self.rpm = self.idle_rpm
        if self.rpm > self.max_rpm:
            self.rpm = self.max_rpm


    def update_engine_rpm(self, dt):

        speed_mps = self.speed * PIXELS_TO_M

        wheel_omega = speed_mps / WHEEL_RADIUS_M

        gear_ratio = GEAR_RATIOS[self.gear] * FINAL_DRIVE

        target_engine_omega = wheel_omega * gear_ratio

        target_rpm = target_engine_omega * 60 / (2 * math.pi)

        # Idle protection
        target_rpm = max(target_rpm, IDLE_RPM)

        # Smooth change using inertia
        rpm_diff = target_rpm - self.rpm

        self.rpm += rpm_diff * dt / ENGINE_INERTIA

        # Rev limiter
        if self.rpm > REV_LIMIT:
            self.rpm = REV_LIMIT - 200

        # Auto shift up
        if self.rpm > UPSHIFT_RPM and self.gear < MAX_GEAR:
            self.gear += 1

        # Auto shift down
        elif self.rpm < DOWNSHIFT_RPM and self.gear > 1:
            self.gear -= 1

    def get_torque_multiplier(self):

        for i in range(len(TORQUE_CURVE) - 1):

            rpm1, torque1 = TORQUE_CURVE[i]
            rpm2, torque2 = TORQUE_CURVE[i+1]

            if rpm1 <= self.rpm <= rpm2:

                t = (self.rpm - rpm1) / (rpm2 - rpm1)
                return torque1 + t * (torque2 - torque1)

        return TORQUE_CURVE[-1][1]
        
    def draw(self, surface, camera: Camera):
        sp = camera.world_to_screen(self.pos)
        r = self.image.get_rect(center=(int(sp.x), int(sp.y)))
        surface.blit(self.image, r)

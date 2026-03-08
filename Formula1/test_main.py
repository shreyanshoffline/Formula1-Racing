"""
Top-Down F1-like Racer (Pygame)

A scalable top-down racing game prototype with physically plausible car movement, AI opponents, lap detection, and a HUD.
See README.md for detailed usage instructions and design notes.
"""
import sys
import os

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

import pygame
from pygame.math import Vector2
from car import Car
from ai import AIDriver
from camera import Camera
from utils import *
from utils import WaypointRecorder
from config import *
from screens import ScreenManager  # <-- remodeled UI manager

# -------- CONFIG --------
FPS = 60
pygame.init()
FONT_PATH = resource_path(os.path.join("fonts", "Orbitron-VariableFont_wght.ttf"))
speed_large_font = pygame.font.Font(FONT_PATH, 48)
speed_unit_large_font = pygame.font.Font(FONT_PATH, 42)
speed_small_font = pygame.font.Font(FONT_PATH, 36)
speed_unit_small_font = pygame.font.Font(FONT_PATH, 30)
hud_font = pygame.font.Font(FONT_PATH, 24)
hud_font_large = pygame.font.Font(FONT_PATH, 36)
recorder = WaypointRecorder()
THROTTLE_RAMP = 0.8
BRAKE_RAMP = 10.0
fastest_lap_global = None

HUD_X = SCREEN_W/28

# -------- MAIN GAME LOOP --------
def main():
    global fastest_lap_global
    SCREEN_W, SCREEN_H = 1400, 800

    screen = pygame.display.set_mode(
        (SCREEN_W, SCREEN_H),
        pygame.RESIZABLE
)
    screen_manager = ScreenManager(SCREEN_W, SCREEN_H)
    camera = Camera(SCREEN_W, SCREEN_H)
    pygame.display.set_caption("F1 Thrill - Scaled Top-Down")
    clock = pygame.time.Clock()
    race_loaded = False
    race_objects = {}
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        # --- EVENT LOOP ---
        events = pygame.event.get()
        for ev in events:
            if ev.type == pygame.QUIT:
                running = False
            screen_manager.handle_events([ev])
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_r and not recorder.recording:
                    recorder.start()
                elif ev.key == pygame.K_t and recorder.recording:
                    recorder.stop()
            if ev.type == pygame.VIDEORESIZE:

                SCREEN_W, SCREEN_H = ev.w, ev.h

                screen = pygame.display.set_mode(
                    (SCREEN_W, SCREEN_H),
                    pygame.RESIZABLE
                )

                # Update ScreenManager
                screen_manager.resize(SCREEN_W, SCREEN_H)

                # Update camera
                # Update camera size when window resizes
                if race_loaded:
                    race_objects["camera"].width = SCREEN_W
                    race_objects["camera"].height = SCREEN_H
                    race_objects["camera"].update
                    race_objects["camera"].resize(SCREEN_W, SCREEN_H)
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
                pygame.quit()
                sys.exit()
        # --- SCREEN LOGIC ---
        if screen_manager.current_screen != "race":
            race_loaded = False

        # --- RACE LOGIC ---
        if screen_manager.current_screen == "race":
            # --- LOAD TRACK AND OBJECTS ---
            if not race_loaded:
                track_file, mask_file = screen_manager.selected_track
                track_img = load_image(track_file)
                track_mask = load_image(mask_file)
                if track_file == "Track_1.png" and mask_file == "Track_1_mask.png":
                    track_img = pygame.transform.smoothscale(track_img, (5000, 5000))
                    track_mask = pygame.transform.smoothscale(track_mask, (5000, 5000))
                if track_file == "Track_2.png" and mask_file == "Track_2_mask.png":
                    track_img = pygame.transform.smoothscale(track_img, (6500, 4000))
                    track_mask = pygame.transform.smoothscale(track_mask, (6500, 4000))
                WORLD_W, WORLD_H = track_img.get_width(), track_img.get_height()
                player_img = pygame.transform.smoothscale(load_image("Mclaren.png"), CAR_SCALE)
                ai_img = pygame.transform.smoothscale(load_image("RedBull.png"), CAR_SCALE)
                speedometer_img = pygame.transform.smoothscale(load_image("Speedometer.png"), (500,300))
                waypoints = None
                player_start = 0.50 * WORLD_W, 0.89 * WORLD_H
                player = Car(player_img, player_start, angle_deg=-90.0, is_player=True)
                ai_car = Car(ai_img, player_start + Vector2(-80, -6), angle_deg=-90.0)
                ai_driver = AIDriver(ai_car, waypoints)
                start_line_x = int(WORLD_W * 0.50)
                start_line_y1 = int(WORLD_H * 0.85)
                start_line_y2 = int(WORLD_H * 0.93)

                start_line = {
                    "x": start_line_x,
                    "y1": start_line_y1,
                    "y2": start_line_y2
                }
                race_objects = {
                    "track_img": track_img,
                    "track_mask": track_mask,
                    "player": player,
                    "ai_car": ai_car,
                    "ai_driver": ai_driver,
                    "camera": camera,
                    "start_line": start_line,
                    "speedometer_img": speedometer_img,
                    "WORLD_W": WORLD_W,
                    "WORLD_H": WORLD_H
                }
                race_loaded = True

            # --- INPUT & PHYSICS ---
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                pygame.quit()
                sys.exit()
            player = race_objects["player"]
            throttle_input = 1.0 if keys[pygame.K_w] or keys[pygame.K_UP] else 0.0
            brake_input = 1.0 if keys[pygame.K_s] or keys[pygame.K_DOWN] else 0.0
            steer_input_raw = 1.0 if keys[pygame.K_a] or keys[pygame.K_LEFT] else -1.0 if keys[pygame.K_d] or keys[pygame.K_RIGHT] else 0.0
            player.drift = 1.0 if keys[pygame.K_LSHIFT] else 0.0
            player.throttle += clamp(throttle_input - player.throttle, -THROTTLE_RAMP*dt, THROTTLE_RAMP*dt)
            player.brake += clamp(brake_input - player.brake, -BRAKE_RAMP*dt, BRAKE_RAMP*dt)
            player.brake = clamp(player.brake, 0.0, 1.0)
            player.steer_input = steer_input_raw
            race_objects["ai_driver"].update(dt)
            player.update(dt, race_objects["track_mask"])
            player.update_rpm(dt)
            race_objects["ai_car"].update(dt, race_objects["track_mask"])
            race_objects["camera"].update(player.pos)
            recorder.update(dt, player.pos)

            # --- LAP TIMER, PENALTY, DETECTION ---
            # Initialize lap/timer/penalty variables
            for var, default in [
                ('lap_times', []),
                ('lap_start_time', None),
                ('fastest_lap', None),
                ('timer_started', False),
                ('last_lap_delta', None),
                ('lap', 1),
                ('prev_pos', player.pos.copy()),
                ('off_track_time', 0.0),
                ('lap_penalty', 0.0),
                ('lap_disqualified', False),
                ('penalty_message', None),
                ('penalty_message_until', 0),
                ('last_penalty_level', 0.0)
            ]:
                if not hasattr(player, var):
                    setattr(player, var, default)

            # Start timer only after first acceleration
            if not player.timer_started and player.throttle > 0:
                player.lap_start_time = pygame.time.get_ticks()
                player.timer_started = True

            # --- PERFECT LAP DETECTION SYSTEM ---
            start_line = race_objects["start_line"]
            # Initialize if missing
            if not hasattr(player, "prev_pos"):
                player.prev_pos = player.pos.copy()

            if not hasattr(player, "lap_cooldown"):
                player.lap_cooldown = 0

            line_x = start_line["x"]
            line_y1 = start_line["y1"]
            line_y2 = start_line["y2"]

            prev = player.prev_pos
            curr = player.pos

            # Check if car crossed the vertical line
            crossed_line = (
                prev.x < line_x and curr.x >= line_x and
                line_y1 <= curr.y <= line_y2
            )

            # Check direction (must be moving right)
            moving_forward = player.velocity.x > 0

            if crossed_line and moving_forward and player.lap_cooldown <= 0:
                now = pygame.time.get_ticks()
                if player.lap_start_time is not None:
                    lap_time = (now - player.lap_start_time) / 1000.0
                    if player.lap > 1:
                        if not player.lap_disqualified:
                            lap_time += player.lap_penalty
                            player.lap_times.append(lap_time)
                            if player.fastest_lap is None or lap_time < player.fastest_lap:
                                player.fastest_lap = lap_time
                            global fastest_lap_global
                            if fastest_lap_global is None or lap_time < fastest_lap_global:
                                fastest_lap_global = lap_time
                            player.last_lap_delta = lap_time - fastest_lap_global
                        else:
                            player.last_lap_delta = None
                    player.lap += 1
                player.lap_start_time = now
                player.lap_penalty = 0
                player.lap_disqualified = False
                player.lap_cooldown = 60  # 1 second cooldown
                player.off_track_time = 0.0  # Reset off-track time at lap end

            # reduce cooldown
            if player.lap_cooldown > 0:
                player.lap_cooldown -= 1


            # store previous position
            player.prev_pos = player.pos.copy()

            # --- OFF-TRACK PENALTY LOGIC ---
            mask = race_objects["track_mask"]
            px, py = int(player.pos.x), int(player.pos.y)
            show_warning = False
            off_track = False
            if 0 <= px < mask.get_width() and 0 <= py < mask.get_height():
                color = mask.get_at((px, py))
                if color[:3] != (255, 255, 255):
                    show_warning = True
                    off_track = True
            player.pos.x = max(0, min(player.pos.x, race_objects["WORLD_W"] - 1))
            player.pos.y = max(0, min(player.pos.y, race_objects["WORLD_H"] - 1))
            # Accumulate off-track time until lap ends
            if off_track:
                player.off_track_time += dt
            # Do NOT reset off_track_time when back on track
            # Reset only when lap ends

            # Penalty logic: apply difference immediately, do not stack
            penalty_level = 0.0
            if player.off_track_time >= 6.0:
                player.lap_disqualified = True
                penalty_level = 6.0
            elif player.off_track_time >= 5.0:
                penalty_level = 4.0
            elif player.off_track_time >= 2.0:
                penalty_level = 2.0
            else:
                penalty_level = 0.0
            now_ticks = pygame.time.get_ticks()
            # Apply penalty difference immediately
            if penalty_level > player.last_penalty_level:
                penalty_diff = penalty_level - player.last_penalty_level
                player.lap_penalty += penalty_diff
                if penalty_level == 2.0:
                    player.penalty_message = "2s Penalty!"
                elif penalty_level == 4.0:
                    player.penalty_message = "4s Penalty!"
                elif penalty_level == 6.0:
                    player.penalty_message = "Lap Disqualified!"
                player.penalty_message_until = now_ticks + 2000
            player.last_penalty_level = penalty_level
            # If penalty level drops, do not subtract from lap_penalty

            # --- DRAWING & HUD ---
            screen.fill((31, 1, 34))
            screen.blit(race_objects["track_img"], camera.world_to_screen((0,0)))
            pygame.draw.line(
                screen,
                (255, 255, 0),
                camera.world_to_screen((start_line["x"], start_line["y1"])),
                camera.world_to_screen((start_line["x"], start_line["y2"])),
                4
            )

            player.draw(screen, camera)
            race_objects["ai_car"].draw(screen, camera)
            speed_kph = pxs_to_kph(player.speed)
            speed_mph = pxs_to_mph(player.speed)
            kph_text = speed_large_font.render(f"{int(speed_kph)}", True, (255,255,255))
            mph_text = speed_small_font.render(f"{int(speed_mph)}", True, (255,255,255))
            kph_units_text = speed_unit_large_font.render("KPH", True, (255,255,255))
            mph_units_text = speed_unit_small_font.render("MPH", True, (255,255,255))
            lap_text = hud_font.render(f"Lap: {player.lap}", True, (255,255,255))
            throttle_text = hud_font.render(f"Throttle: {player.throttle:.2f}", True, (200,200,200))
            brake_text = hud_font.render(f"Brake: {player.brake:.2f}", True, (200,200,200))
            
            KPH_x = SCREEN_W/2 - kph_text.get_width()
            KPH_y = SCREEN_H/3 - race_objects["speedometer_img"].get_height()//2 - kph_text.get_height()//2 - 18
            KPH_units_x = SCREEN_W/2 + kph_units_text.get_width()//5
            KPH_units_y = SCREEN_H/3 - race_objects["speedometer_img"].get_height()//2 - kph_units_text.get_height()//2 - 18
            
            MPH_x = SCREEN_W/2 - mph_text.get_width()
            MPH_y =  KPH_y + kph_text.get_height()
            MPH_units_x = SCREEN_W/2 + mph_units_text.get_width()//4
            MPH_units_y = SCREEN_H/3 - race_objects["speedometer_img"].get_height()//2 - kph_units_text.get_height()//2 + 42

            
            screen.blit(race_objects["speedometer_img"], (SCREEN_W/2 - race_objects["speedometer_img"].get_width()/2, SCREEN_H/3 - race_objects["speedometer_img"].get_height()))
            screen.blit(kph_text, (KPH_x,KPH_y))            
            screen.blit(kph_units_text, (KPH_units_x,KPH_units_y))
            screen.blit(mph_text, (MPH_x, MPH_y))
            screen.blit(mph_units_text, (MPH_units_x, MPH_units_y))
            screen.blit(lap_text, (HUD_X,38))
            screen.blit(throttle_text, (HUD_X,66))
            screen.blit(brake_text, (HUD_X,94))
            # REV SYSTEM
            GEAR_SPEEDS = [0, 40, 80, 130, 180, 230, 280, 340, 400]
            MAX_RPM = 12000
            IDLE_RPM = 1200
            gear = 1
            speed_kph_val = pxs_to_kph(player.speed)
            for g in range(1, len(GEAR_SPEEDS)):
                if speed_kph_val < GEAR_SPEEDS[g]:
                    gear = g
                    break
                else:
                    gear = len(GEAR_SPEEDS) - 1
            gear_min = GEAR_SPEEDS[gear-1]
            gear_max = GEAR_SPEEDS[gear]
            gear_ratio = (speed_kph_val - gear_min) / (gear_max - gear_min) if gear_max - gear_min > 0 else 0
            rpm = int(IDLE_RPM + gear_ratio * (MAX_RPM - IDLE_RPM) + player.throttle * 2000)
            rpm = min(max(rpm, IDLE_RPM), MAX_RPM)
            rpm_text = hud_font.render(f"REV: {rpm} RPM", True, (255,255,255))
            gear_text = hud_font.render(f"GEAR: {gear}", True, (255,255,255))
            screen.blit(rpm_text, (HUD_X, 150))
            screen.blit(gear_text, (HUD_X, 200))
            # LAP TIME HUD
            now = pygame.time.get_ticks()
            if player.lap_disqualified:
                lap_time_text = hud_font.render("Lap Time: Disqualified", True, (255,0,0))
            else:
                running_lap_time = (now - player.lap_start_time) / 1000.0 if player.lap_start_time is not None else 0.0
                lap_time_with_penalty = running_lap_time + player.lap_penalty
                lap_time_text = hud_font.render(f"Lap Time: {lap_time_with_penalty:.2f}s", True, (255,255,255))
            screen.blit(lap_time_text, (HUD_X, 240))
            y_offset = 270
            if fastest_lap_global is not None:
                best_lap_text = hud_font.render(f"Fastest: {fastest_lap_global:.2f}s", True, (255,215,0))
            else:
                best_lap_text = hud_font.render(f"Fastest: N/A", True, (255,215,0))
            screen.blit(best_lap_text, (HUD_X, y_offset))
            y_offset += 30
            if len(player.lap_times) > 0 and fastest_lap_global is not None:
                last_lap = player.lap_times[-1]
                if last_lap is not None:
                    last_lap_text = hud_font.render(f"Last Lap: {last_lap:.2f}s", True, (200,200,255))
                else:
                    last_lap_text = hud_font.render(f"Last Lap: Disqualified", True, (255,0,0))
                screen.blit(last_lap_text, (HUD_X, y_offset))
                y_offset += 30
                if len(player.lap_times) > 1 and last_lap is not None:
                    delta = last_lap - fastest_lap_global
                    if abs(delta) > 0.01:
                        if delta < 0:
                            delta_str = f"–{abs(delta):.2f}s"
                            delta_color = (0, 255, 0)
                        else:
                            delta_str = f"+{abs(delta):.2f}s"
                            delta_color = (255, 0, 0)
                        delta_text = hud_font.render(f"Δ: {delta_str}", True, delta_color)
                        screen.blit(delta_text, (HUD_X, y_offset))
                        y_offset += 30
            # Show penalty/disqualified warning (mutually exclusive)
            disq_font = pygame.font.Font(FONT_PATH, 40)
            if player.lap_disqualified:
                dq_text = disq_font.render("Lap Disqualified", True, (255,0,0))
                screen.blit(dq_text, (SCREEN_W//2 - dq_text.get_width()//2, 3 *SCREEN_H//4 - 50))
            elif player.penalty_message and now < player.penalty_message_until:
                color = (255,100,0) if 'Penalty' in player.penalty_message else (255,0,0)
                msg = hud_font_large.render(player.penalty_message, True, color)
                screen.blit(msg, (SCREEN_W//2 - msg.get_width()//2, 3 * SCREEN_H//4))
            
            off_track_time = hud_font_large.render(f"Off-Track Time: {player.off_track_time:.2f}s", True, (255, 255, 0))
            screen.blit(off_track_time, (SCREEN_W//2 - off_track_time.get_width()//2, 6*SCREEN_H//7))


            # Show off-track warning only once per frame
            if show_warning:
                warning_text = speed_large_font.render("Warning - stay on track", True, (255, 255, 0))
                screen.blit(warning_text, (SCREEN_W//2 - warning_text.get_width()//2, SCREEN_H//4 - warning_text.get_height()//3))

            # MINIMAP
            mm_w, mm_h = 300, 200
            mm = pygame.transform.smoothscale(race_objects["track_img"], (mm_w, mm_h))
            mm_x, mm_y = SCREEN_W - mm_w - 12, 8
            screen.blit(mm, (mm_x, mm_y))
            mini_px = mm_x + int(player.pos.x / race_objects["WORLD_W"] * mm_w)
            mini_py = mm_y + int(player.pos.y / race_objects["WORLD_H"] * mm_h)
            mini_aix = mm_x + int(race_objects["ai_car"].pos.x / race_objects["WORLD_W"] * mm_w)
            mini_aiy = mm_y + int(race_objects["ai_car"].pos.y / race_objects["WORLD_H"] * mm_h)
            pygame.draw.circle(screen, (255,0,0), (mini_aix, mini_aiy), 6)
            pygame.draw.circle(screen, (0,255,0), (mini_px, mini_py), 6)
            screen_manager.draw_race_ui(screen)
            pygame.display.flip()
        else:
            screen_manager.update()
            screen_manager.draw(screen)
            pygame.display.flip()
    pygame.quit()
if __name__ == "__main__":
    main()

# screens.py
import pygame
import os

pygame.init()
pygame.font.init()

ORBITRON_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "fonts",
    "Orbitron-VariableFont_wght.ttf"
)

BASE_W = 1400
BASE_H = 800


class ScreenManager:

    def __init__(self, screen_width=1400, screen_height=800):

        self.screen_w = screen_width
        self.screen_h = screen_height

        self.scale = 1

        self.current_screen = "start"
        self.selected_track = None

        self.bg_color = (0, 0, 52)
        self.button_color = (0, 0, 128)
        self.button_hover = (0, 0, 189)
        self.text_color = (255, 255, 255)
        self.scroll_color = (255, 255, 255)

        self.track_names = [
            "Practice 1",
            "Track 1",
            "Track 2",
            "Track 3",
            "Track 4",
            "Track 5",
            "Track 6",
            "Track 7",
            "Track 8"
        ]

        self.track_files = {
            name: (
                f"{name.replace(' ', '_')}.png",
                f"{name.replace(' ', '_')}_mask.png"
            )
            for name in self.track_names
        }

        self.scroll_offset = 0
        self.dragging_scroll = False

        self.resize(screen_width, screen_height)


    # --------------------------------------------------
    # SCALE CALCULATION
    # --------------------------------------------------

    def calculate_scale(self):

        self.scale = min(
            self.screen_w / BASE_W,
            self.screen_h / BASE_H
        )


    # --------------------------------------------------
    # FONT SYSTEM (LOCKED TO SCALE)
    # --------------------------------------------------

    def update_fonts(self):

        title_size = int(90 * self.scale)
        button_size = int(42 * self.scale)

        title_size = max(title_size, 16)
        button_size = max(button_size, 12)

        self.title_font = pygame.font.Font(
            ORBITRON_PATH,
            title_size
        )

        self.button_font = pygame.font.Font(
            ORBITRON_PATH,
            button_size
        )


    # --------------------------------------------------
    # LAYOUT SYSTEM (LOCKED TO SCALE)
    # --------------------------------------------------

    def update_layouts(self):

        center_x = self.screen_w // 2

        # PLAY BUTTON
        play_w = int(400 * self.scale)
        play_h = int(80 * self.scale)

        self.play_button = pygame.Rect(
            center_x - play_w // 2,
            int(self.screen_h * 0.72),
            play_w,
            play_h
        )

        # TRACK BUTTONS
        button_w = int(700 * self.scale)
        button_h = int(90 * self.scale)

        spacing = int(25 * self.scale)

        start_y = int(150 * self.scale)

        self.track_buttons = []

        for i in range(len(self.track_names)):

            rect = pygame.Rect(
                center_x - button_w // 2,
                start_y + i * (button_h + spacing),
                button_w,
                button_h
            )

            self.track_buttons.append(rect)


        # SCROLL BAR
        bar_w = int(20 * self.scale)
        bar_h = int(500 * self.scale)

        self.scroll_bar_rect = pygame.Rect(
            self.screen_w - bar_w - int(20 * self.scale),
            start_y,
            bar_w,
            bar_h
        )

        self.scroll_thumb_rect = self.scroll_bar_rect.copy()

        self.update_scroll_thumb()


        # BACK BUTTON
        back_w = int(300 * self.scale)
        back_h = int(80 * self.scale)

        self.back_button = pygame.Rect(
            self.screen_w - back_w - int(30 * self.scale),
            self.screen_h - back_h - int(30 * self.scale),
            back_w,
            back_h
        )

        self.race_ui_elements = [

            {
                "rect": self.back_button,
                "text": "Track Select",
                "action": self.goto_map_select
            }

        ]


    # --------------------------------------------------
    # SCROLL SYSTEM
    # --------------------------------------------------

    def update_scroll_thumb(self):

        total_height = self.track_buttons[-1].bottom - self.track_buttons[0].top

        visible_height = int(BASE_H * 0.6 * self.scale)

        if total_height <= visible_height:

            self.scroll_thumb_rect.height = self.scroll_bar_rect.height

        else:

            ratio = visible_height / total_height

            self.scroll_thumb_rect.height = max(
                int(self.scroll_bar_rect.height * ratio),
                int(30 * self.scale)
            )

        max_move = self.scroll_bar_rect.height - self.scroll_thumb_rect.height

        self.scroll_thumb_rect.top = (
            self.scroll_bar_rect.top +
            int(max_move * self.scroll_offset)
        )


    def handle_scroll(self, mouse_y):

        bar = self.scroll_bar_rect

        rel = mouse_y - bar.top

        rel = max(0, min(rel, bar.height))

        self.scroll_offset = rel / bar.height

        total_height = self.track_buttons[-1].bottom - self.track_buttons[0].top

        visible_height = int(BASE_H * 0.6 * self.scale)

        offset_pixels = self.scroll_offset * (total_height - visible_height)

        start_y = int(150 * self.scale)

        for i, rect in enumerate(self.track_buttons):

            rect.y = start_y + i * (rect.height + int(25 * self.scale)) - offset_pixels

        self.update_scroll_thumb()


    # --------------------------------------------------
    # RESIZE (MASTER FUNCTION)
    # --------------------------------------------------

    def resize(self, width, height):

        self.screen_w = width
        self.screen_h = height

        self.calculate_scale()

        self.update_fonts()

        self.update_layouts()


    # --------------------------------------------------
    # EVENTS
    # --------------------------------------------------

    def handle_events(self, events):

        for event in events:

            if event.type == pygame.MOUSEBUTTONDOWN:

                if self.current_screen == "start":

                    if self.play_button.collidepoint(event.pos):

                        self.current_screen = "map_select"


                elif self.current_screen == "map_select":

                    if self.scroll_bar_rect.collidepoint(event.pos):

                        self.dragging_scroll = True

                    for i, rect in enumerate(self.track_buttons):

                        if rect.collidepoint(event.pos):

                            name = self.track_names[i]

                            self.selected_track = self.track_files[name]

                            self.current_screen = "race"


                elif self.current_screen == "race":

                    if self.back_button.collidepoint(event.pos):

                        self.goto_map_select()


            elif event.type == pygame.MOUSEBUTTONUP:

                self.dragging_scroll = False


            elif event.type == pygame.MOUSEMOTION:

                if self.dragging_scroll:

                    self.handle_scroll(event.pos[1])


    # --------------------------------------------------
    # SCREEN CHANGES
    # --------------------------------------------------

    def goto_map_select(self):

        self.current_screen = "map_select"

        self.scroll_offset = 0

        self.update_layouts()


    # --------------------------------------------------
    # DRAWING
    # --------------------------------------------------

    def draw(self, surface):

        surface.fill(self.bg_color)

        if self.current_screen == "start":

            self.draw_start(surface)

        elif self.current_screen == "map_select":

            self.draw_map(surface)

        elif self.current_screen == "race":

            self.draw_race_ui(surface)


    def draw_start(self, surface):

        title = self.title_font.render(
            "Formula 1 Racing",
            True,
            self.text_color
        )

        surface.blit(
            title,
            title.get_rect(center=(self.screen_w//2, int(120*self.scale)))
        )

        mouse = pygame.mouse.get_pos()

        color = self.button_hover if self.play_button.collidepoint(mouse) else self.button_color

        pygame.draw.rect(surface, color, self.play_button)

        text = self.button_font.render("PLAY", True, self.text_color)

        surface.blit(text, text.get_rect(center=self.play_button.center))


    def draw_map(self, surface):

        title = self.title_font.render("Track Select", True, self.text_color)

        surface.blit(
            title,
            title.get_rect(center=(self.screen_w//2, int(100*self.scale)))
        )

        mouse = pygame.mouse.get_pos()

        for i, rect in enumerate(self.track_buttons):

            color = self.button_hover if rect.collidepoint(mouse) else self.button_color

            pygame.draw.rect(surface, color, rect)

            text = self.button_font.render(self.track_names[i], True, self.text_color)

            surface.blit(text, text.get_rect(center=rect.center))

        pygame.draw.rect(surface, (100,100,100), self.scroll_bar_rect)

        pygame.draw.rect(surface, self.scroll_color, self.scroll_thumb_rect)


    def draw_race_ui(self, surface):

        mouse = pygame.mouse.get_pos()

        color = self.button_hover if self.back_button.collidepoint(mouse) else self.button_color

        pygame.draw.rect(surface, color, self.back_button)

        text = self.button_font.render("Track Select", True, self.text_color)

        surface.blit(text, text.get_rect(center=self.back_button.center))
    def update(self):
        # This ensures layouts stay correct if anything changes dynamically
        # Does NOT recreate fonts every frame (avoids lag)
        
        # Only update scroll thumb position
        if self.current_screen == "map_select":
            self.update_scroll_thumb()
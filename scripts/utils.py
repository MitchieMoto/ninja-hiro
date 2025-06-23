import os
import json
import pygame
import random
import math

from scripts.animation import Animation
from scripts.config import COLOR_CODES
from scripts.sparrows import Sparrow

WIDTH = 320
HEIGHT = 240
BASE_IMG_PATH = 'data/images/'

# Load a single image
def load_image(path, scale=None):
    img = pygame.image.load(BASE_IMG_PATH + path).convert_alpha()
    img.set_colorkey((0, 0, 0))
    if scale:
        img = pygame.transform.scale(img, scale)
    return img

# Load multiple images
def load_images(path, scale=None):
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        image = load_image(path + '/' + img_name)
        if scale:
            image = pygame.transform.scale(image, scale)
        images.append(image)
    return images

# Scale images
def scale_images(images, scale):
    if scale == 1.0:
        return images
    return [pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale))) for img in images]

# Scale animations
def scaled_anim(path, scale=1.0, dur=6, loop=True):
    frames = load_images(path)
    if scale != 1.0:
        frames = scale_images(frames, scale)
    return Animation(frames, img_dur=dur, loop=loop)

# Load a specified sound
def load_sound(path, volume=1.0):
    sound = pygame.mixer.Sound(path)
    sound.set_volume(volume)
    return sound

# Render text at specific coords
def render_text(surf, text, font_type, font_size, color, x, y, outline=False):
    if not isinstance(text, str):
        text = str(text)

    if isinstance(font_type, str):
        font = pygame.font.Font(font_type, font_size)
    else:
        font = font_type  # fallback if user passed in a font object

    text_surface = font.render(text, True, color)

    # Adds a black border around the text
    if outline:
        outline_color = (0, 0, 0)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    outline_surf = font.render(text, True, outline_color)
                    surf.blit(outline_surf, (x + dx, y + dy))

    surf.blit(text_surface, (x, y))

# Render centered text
def render_centered_text(screen, text, font_type, font_size, color, y, bold, bold_size=1):
    # Allow both string font names and preloaded pygame Font objects
    if isinstance(font_type, pygame.font.Font):
        font = font_type
    elif isinstance(font_type, str) and font_type.lower().endswith(".ttf"):
        font = pygame.font.Font(font_type, font_size)
    else:
        font = pygame.font.SysFont(font_type, font_size, bold)

    text_surface = font.render(text, False, color)
    text_rect = text_surface.get_rect(center=(screen.get_width() // 2, y))

    # Optional black outline
    outline_color = (0, 0, 0)
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx != 0 or dy != 0:
                outline_surf = font.render(text, True, outline_color)
                outline_rect = outline_surf.get_rect(center=(screen.get_width() // 2 + dx, y + dy))
                screen.blit(outline_surf, outline_rect)

    screen.blit(text_surface, text_rect)

# Pause menu
def pause_menu(self, offset):
    paused = True
    pygame.mixer.music.pause()

    # Pause all dedicated channels
    for channel in self.dedicated_channels.values():
        channel.pause()

    while paused:
        render_centered_text(self.screen, "Paused", self.font_path, 46, COLOR_CODES["Kohaku"], self.screen.get_height() // 3 - 120, True, 2)
        render_centered_text(self.screen, "Esc to Resume", self.font_path, 16, COLOR_CODES["Shironeri"], self.screen.get_height() // 3 - 60, True, 2)
        render_centered_text(self.screen, "Q to Quit to Menu", self.font_path, 16, COLOR_CODES["Shironeri"], self.screen.get_height() // 3 - 30, True, 2)
        render_centered_text(self.screen, "R to Restart Level", self.font_path, 16, COLOR_CODES["Shironeri"], self.screen.get_height() // 3 , True, 2)

        pygame.display.update()
        # Full game close loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"
            if event.type == pygame.KEYDOWN:
                # Unpause logic                
                if event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.unpause()
                    self.dedicated_channels["ambience"].unpause()
                    paused = False
                    self.movement = [False, False]
                # Quit to main menu
                elif event.key == pygame.K_q:
                    return "menu"
                # Restart level
                elif event.key == pygame.K_r:
                    pygame.mixer.music.unpause()
                    self.dedicated_channels["ambience"].unpause()
                    # Clear input
                    self.movement = [False, False] 
                    return "restart"

    # Unpause all dedicated channels
    for channel in self.dedicated_channels.values():
        channel.unpause()

    return True

# Start menu
def start_menu(self, resume_data=None):
    WIDTH, HEIGHT = 320, 240
    menu_sparrows = []
    sparrow_timer = 0
    SPARROW_INTERVAL = random.randint(30, 180)
    background = pygame.image.load(os.path.join("data", "images", "backgrounds/start_screen.png")).convert()
    background = pygame.transform.scale(background, (WIDTH * 3, HEIGHT * 3))
    # Ms between input repeats
    key_repeat_delay = 200  
    last_key_action_time = 0

    # Sort levels by number
    level_files = sorted(
        [f for f in os.listdir("data/maps") if f.endswith(".json") and f.split('.')[0].isdigit()],
        key=lambda f: int(f.split('.')[0])
    )
    level_names = [f.replace(".json", "") for f in level_files]

    # Base start state unless overwritten with save data for initial game boot
    selected_slot = 1
    menu_state = "slot"
    selected_character_index = 0
    selected_level_index = 0
    unlocked = ["Ninja Hiro"]
    max_unlocked_level = 0

    # Handles returns to the main menu from a level
    if resume_data:
        # Use previous states for user save data
        selected_slot = resume_data["slot"]
        self.save_slot = selected_slot
        self.save_data = resume_data["data"]
        # Set menu to select state immediately
        menu_state = "select"

        # Returns the user to their most recent selections in menu before entering a level
        unlocked = self.save_data.get("unlocked_characters", ["Ninja Hiro"])
        saved_char = self.save_data.get("character", "Ninja Hiro")
        saved_level = self.save_data.get("level", 0)
        selected_character_index = unlocked.index(saved_char) if saved_char in unlocked else 0
        selected_level_index = saved_level if 0 <= saved_level < len(level_names) else 0
        max_unlocked_level = self.save_data.get("max_unlocked_level", 0)
        selected_level_index = saved_level

    run = True
    clock=pygame.time.Clock()
    while run:
        self.screen.blit(background, (0, 0))

        # Update menu sparrows
        sparrow_timer += 1
        if sparrow_timer >= SPARROW_INTERVAL:
            # 30% chance when less than 6 sparrows on screen every update
            if len(menu_sparrows) < 6 and random.random() < 0.3: 
                frames = self.assets['sparrows']
                animation = Animation(frames, img_dur=random.randint(6, 10), loop=True)
                sparrow = Sparrow(animation, self.screen.get_size(), speed_range=(0.8, 2.0))
                menu_sparrows.append(sparrow)
            sparrow_timer = 0
            SPARROW_INTERVAL = random.randint(30, 180)

        # Render menu sparrows
        for sparrow in menu_sparrows[:]:
            sparrow.update()
            sparrow.render(game = None, surface = self.screen)
            # Remove them when killed by sparrow logic when off screen
            if sparrow.dead:
                menu_sparrows.remove(sparrow)

        # Render main title
        render_centered_text(self.screen, "Ninja Hiro", self.font_path, 48, COLOR_CODES["Kohaku"], 100, True, 2)

        # Render text for save slot selection
        if menu_state == "slot":
            render_centered_text(self.screen, f"Save Slot: {selected_slot}", self.font_path, 28, COLOR_CODES["Ai"], self.screen.get_height() - 120, True, 2)
            render_centered_text(self.screen, "A / D to choose save | SPACE to continue", self.font_path, 16, COLOR_CODES["Shironeri"], self.screen.get_height() - 40, False, 2)

        # Else render text for character and level selection
        elif menu_state == "select":
            if selected_character_index >= len(unlocked):
                selected_character_index = 0

            selected_character = unlocked[selected_character_index]
            # Level selection clamped to 0 and total number of levels (0 inclusive)
            selected_level_index = max(0, min(selected_level_index, len(level_names) - 1))
            level_name = level_names[selected_level_index]

            # Character Preview Sprite 
            char_data = self.character_data[selected_character]
            sprite_path = char_data["sprite"]
            size = tuple(char_data["size"])
            scale = char_data.get("scale", 1.0)

            # Apply both menu scaling (x6) and per-character scale
            preview_scale = (int(size[0] * 6 * scale), int(size[1] * 6 * scale))
            preview_img = load_image(sprite_path, scale=preview_scale)

            # Show scaled preview character sprite 
            if preview_img:
                preview_rect = preview_img.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 260))
                offset = math.sin(pygame.time.get_ticks() / 300) * 3
                preview_rect.centery += int(offset)
                self.screen.blit(preview_img, preview_rect)

            # Shows options for characetr and level select at the bottom
            render_centered_text(self.screen, f"Character: {self.character_data[selected_character]['name']}", self.font_path, 24, COLOR_CODES["Matcha"], self.screen.get_height() - 140, True, 2)             
            render_centered_text(self.screen, f"Level: {level_name}", self.font_path, 24, COLOR_CODES["Ai"], self.screen.get_height() - 90, True, 2)
            render_centered_text(self.screen, "A / D Level | W / S Character | SPACE to start", self.font_path, 16, COLOR_CODES["Shironeri"], self.screen.get_height() - 40, False)

        keys = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()

        # Handle level and character selection, with hold key functionality
        if menu_state == "select" and current_time - last_key_action_time > key_repeat_delay:
            if keys[pygame.K_d] and selected_level_index < max_unlocked_level:
                selected_level_index += 1
                last_key_action_time = current_time
            elif keys[pygame.K_a] and selected_level_index > 0:
                selected_level_index -= 1
                last_key_action_time = current_time
            elif keys[pygame.K_w]:
                selected_character_index = (selected_character_index + 1) % len(unlocked)
                last_key_action_time = current_time
            elif keys[pygame.K_s]:
                selected_character_index = (selected_character_index - 1) % len(unlocked)
                last_key_action_time = current_time

        pygame.display.update()

        # Handle all other events in main menu
        for event in pygame.event.get():
            # Exit game
            if event.type == pygame.QUIT:
                pygame.quit()
                return "quit"
            # All other keys with no hold key functionality
            if event.type == pygame.KEYDOWN:
                # When at save select                
                if menu_state == "slot":
                    # Cycle through saves
                    if event.key == pygame.K_d:
                        selected_slot = 1 if selected_slot == 3 else selected_slot + 1
                    elif event.key == pygame.K_a:
                        selected_slot = 3 if selected_slot == 1 else selected_slot - 1
                    # Choose save and load relevant data
                    elif event.key == pygame.K_SPACE:
                        self.save_slot = selected_slot
                        self.save_data = self.load_save(selected_slot)
                        unlocked = self.save_data.get("unlocked_characters", ["Ninja Hiro"])
                        saved_char = self.save_data.get("character", "Ninja Hiro")
                        saved_level = self.save_data.get("level", 0)
                        selected_character_index = unlocked.index(saved_char) if saved_char in unlocked else 0
                        selected_level_index = saved_level if 0 <= saved_level < len(level_names) else 0
                        max_unlocked_level = self.save_data.get("max_unlocked_level", 0)
                        menu_state = "select"
                # Else When at level select
                elif menu_state == "select":
                    # Return to save screen
                    if event.key == pygame.K_ESCAPE:
                        menu_state = "slot"
                    # Else load chosen level and character
                    elif event.key == pygame.K_SPACE:
                        self.character_id = unlocked[selected_character_index]
                        self.level = selected_level_index
                        self.save_data["character"] = self.character_id
                        self.save_data["level"] = self.level
                        self.save_game(self.save_slot, self.save_data, self.character_id, self.level)
                        return True
        clock.tick(60)

# Shows a screen with a background and some text, for character unlocks and end screen
def show_message_screen(screen, image_path, font_path, title=None, subtitle=None, character_sprite_data=None, wait_for_key=True):
    bg_image = pygame.image.load(image_path).convert()
    bg_image = pygame.transform.scale(bg_image, screen.get_size())
    screen.blit(bg_image, (0, 0))

    # Render given title and subtitle
    if title:
        render_centered_text(screen, title, font_path, 32, COLOR_CODES["Kohaku"], screen.get_height() // 2 - 60, True)
    if subtitle:
        render_centered_text(screen, subtitle, font_path, 12, COLOR_CODES["Matcha"], screen.get_height() // 2 + 20, False)

    render_centered_text(screen, "ESC to continue", font_path, 18, COLOR_CODES["Shironeri"], screen.get_height() - 60, False)

    # Show character sprite preview if provided
    if character_sprite_data:
        sprite_path = character_sprite_data["sprite"]
        size = tuple(character_sprite_data["size"])
        scale = character_sprite_data.get("scale", 1.0)

        preview_scale = (int(size[0] * 6 * scale), int(size[1] * 6 * scale))
        preview_img = load_image(sprite_path, scale=preview_scale)

        if preview_img:
            rect = preview_img.get_rect(center=(screen.get_width() // 2, screen.get_height() - 260))
            screen.blit(preview_img, rect)
    pygame.display.update()

    # Wait for user to hit ESC to continue
    if wait_for_key:
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    waiting = False

import sys
import os
import math
import random
import pygame
import json

from scripts.utils import  start_menu, show_message_screen
from scripts.game_utils import load_assets, load_sounds, play_music, render_game_ui, setup_tutorials, load_level, create_player, handle_enemies, handle_projectiles, handle_input, handle_pickups, spawn_particles, check_character_unlocks, stop_dedicated_channels
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.config import STAGE_THEMES
from scripts.sparrows import Sparrows

# Ninja Hiro
class Game:
    def __init__(self):
        pygame.init()
        icon = pygame.image.load('data/images/UI/HiroIcon.png')
        pygame.display.set_icon(icon)
        WIDTH = 320
        HEIGHT = 240
        pygame.display.set_caption('Ninja Hiro')
        pygame.mixer.set_num_channels(32)  
        self.screen = pygame.display.set_mode((WIDTH * 3, HEIGHT * 3))
        self.display = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.save_slot = None
        self.save_data = None        
        self.movement = [False, False]
        self.messages = []  
        self.tutorial_shown = {}  
        self.tip_queue = []
        self.font_path = 'data/fonts/PressStart2P-Regular.ttf'
        self.current_music_theme = None
        self.timer = 0
        self.screenshake = 0   
        self.debug_hitboxes = False

        # Assigns tilemap, including tile size for the game
        self.tilemap = Tilemap(self, tile_size=16)
 
        # Read character data
        with open("data/characters.json") as f:
            self.character_data = json.load(f)

        # Visual and sound assets
        self.assets = load_assets()
        self.sfx = load_sounds()
        self.dedicated_channels = {
            "ambience": pygame.mixer.Channel(5),
            "smoke_bomb": pygame.mixer.Channel(6),
            "rain": pygame.mixer.Channel(7),
            "cicada": pygame.mixer.Channel(8),
            "gong": pygame.mixer.Channel(9),
        }

        self.stage_themes = STAGE_THEMES

        # Assigns sparrows and clouds for use on appropriate level theme
        self.Sparrows = Sparrows(self)
        self.clouds = Clouds(self.assets['clouds'], self.screen.get_height(), count=6)

        # Sorted maps for main menu selection
        self.map_files = sorted(os.listdir('data/maps'), key=lambda f: int(f.split('.')[0]))

    # Loads user save data, used for unlocked characters, unlocked levels and best times
    def load_save(self, slot):
        # Create saves folder if non existent
        os.makedirs("data/saves", exist_ok=True)  
        save_path = f"data/saves/save_{slot}.json"
        # If a save is there, read relevant data
        if os.path.exists(save_path):
            with open(save_path, "r") as f:
                data = json.load(f)
                data.setdefault("unlocked_characters", ["Ninja Hiro"])
                data.setdefault("best_times", {})
                data.setdefault("max_unlocked_level", 0)   
                return data
        # Else sets this base save file data
        else:
            return {
                "character": "Ninja Hiro",
                "level": 0,
                "unlocked_characters": ["Ninja Hiro"],
                "best_times": {},
                "max_unlocked_level": 0 
            }

    # Saves user info and certain selections, such as the last played charactrer and level
    def save_game(self, slot, save_data, character_id, level):
        # Ensure max_unlocked_level is the highest level reached
        save_data["max_unlocked_level"] = max(save_data.get("max_unlocked_level", 0), level)
        save_path = f"data/saves/save_{slot}.json"
        # Save the data to the user profile
        with open(save_path, "w") as f:
            json.dump({
                "character": character_id,
                "level": level,
                "unlocked_characters": save_data["unlocked_characters"],
                "best_times": save_data["best_times"],
                "max_unlocked_level": save_data["max_unlocked_level"]
            }, f)

# -------------------------------------------------------------MAIN GAME----------------------------------------------------------------
    def run(self):
        play_music('data/music/menu_theme.wav', volume=0.4)
        self.dedicated_channels["ambience"].play(game.sfx['ambience'], loops=-1)

        # Handles pausing and unpausing
        resume_payload = {"slot": self.save_slot, "data": self.save_data} if hasattr(self, "resume") else None
        # Handle returns to main menu        
        result = start_menu(self, resume_payload)
        if result == "quit":
            return "quit"

        # Retrieve selected character assts
        self.player = create_player(self)
        # Load level
        load_level(self, self.level)
        # Intro Screen on first level and tutorials
        setup_tutorials(self)

        while True:
            self.display.fill((0, 0, 0, 0))
            self.display_2.blit(self.assets['background'], (0, 0))
            self.screenshake = max(0, self.screenshake - 1)
            
            # Goes to next level when all enemies are defeated
            if not len(self.enemies):
                level_key = str(self.current_map_id)
                # Save time if best
                if level_key not in self.save_data["best_times"] or self.timer < self.save_data["best_times"][level_key]:
                    self.save_data["best_times"][level_key] = self.timer
                check_character_unlocks(self)
                self.save_game(self.save_slot, self.save_data, self.character_id, self.level)
                # Transition time .75s
                self.transition += 1
                if self.transition > 45:
                    # Play END screen if all levels complete
                    if self.level >= len(self.map_files) - 1:
                        show_message_screen(self.screen, "data/images/backgrounds/HiroReturn.png", self.font_path, title="Welcome Home!", subtitle="A brief rest after clearing the nearby castle, but a greater evil yet lurks...") # おめでとう！
                        stop_dedicated_channels(self)
                        return "back_to_level_select"
                    # Else go to and unlock next level
                    else:
                        self.level += 1
                        self.save_data["max_unlocked_level"] = max(self.save_data.get("max_unlocked_level", 0), self.level)
                        self.save_data["level"] = self.level
                        
                        self.save_game(self.save_slot, self.save_data, self.character_id, self.level)
                        load_level(self, self.level)
            if self.transition < 0:
                self.transition += 1
            
            # Restart level on death with transition time
            if self.dead:
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    load_level(self, self.level)
                    
            # Set Render Scroll to track the player near the center but at 1/3 from the bottom of the screen
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0] + 24) / 30
            target_y = self.display.get_height() * (2/3)
            self.scroll[1] += (self.player.rect().centery - target_y - self.scroll[1]) / 12
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            # Draw in normal leaf spawner effects
            spawn_particles(self, self.leaf_spawners)
            spawn_particles(self, self.sakura_leaf_spawners)

            # Draw in clouds unless lanterns are specified for the stages
            if self.lanterns:
                self.lanterns.update()
                self.lanterns.render(self.display_2, offset=render_scroll)
            else:
                self.clouds.update()
                self.clouds.render(self.display_2, offset=render_scroll)
            
            # Draw birds if set for the stage
            self.Sparrows.update()
            self.Sparrows.render(self.display_2, offset=render_scroll)

            # Draw rain if active on the stage
            if self.rain:
                self.rain.update()
                self.rain.render(self.display_2, offset=render_scroll)

            # Draw the tilemap
            self.tilemap.render(self.display, offset=render_scroll)

            # Draw in any solid crumble blocks
            for crumble in self.crumble_blocks:
                if crumble.state != "gone":
                    crumble.update()
                    crumble.render(self.display, offset=render_scroll)

            # Draw spikes
            for spikes in self.spikes:
                spikes.update()
                spikes.render(self.display, offset=render_scroll)
      
            # Draw pickups
            for pickup in self.pickups:
                pickup.render(self.display, offset=render_scroll)

            # Handle particles
            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type in ['leaf', 'cherry_blossom']:
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)
    
            # Handle enemies
            handle_enemies(self, render_scroll)
        
            # Handle player
            if not self.dead:
                # Treats solid crumble blocks as solid tiles
                extra_solids = [block for block in self.crumble_blocks if block.state == 'solid']
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0), extra_solids=extra_solids)
                self.player.render(self.display, offset=render_scroll)

            # Handle pickups
            handle_pickups(self)

            # Handle projectiles
            handle_projectiles(self, render_scroll)
            
            # Handle bullet sparks         
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)
                    
            # Border outlines
            display_mask = pygame.mask.from_surface(self.display)
            display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_sillhouette, offset)    
           
            # Main event loop for player interaction
            input_result = handle_input(self, render_scroll)
            if input_result == "back_to_level_select":
                return "back_to_level_select"
            if input_result == "restart":
                continue
                 
            # Draws the transition            
            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))
                
            self.display_2.blit(self.display, (0, 0))

            # Get timer strings
            render_game_ui(self)

            # Draws the screen and screenshake
            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset)
            pygame.display.update()
            self.clock.tick(60)

            # Update timer
            self.timer += 1 / 60  # Advance timer at 60fps

running = True
resume_slot = None

# Run the game unless closed, also handles loading data on return to main
while running:
    game = Game()

    if resume_slot is not None:
        game.save_slot = resume_slot
        game.save_data = game.load_save(resume_slot)
        game.resume = True
    else:
        game.save_slot = 1
        game.save_data = game.load_save(1)

    result = game.run()

    if result == "quit":
        running = False
    elif result == "back_to_level_select":
        resume_slot = game.save_slot
    else:
        resume_slot = None

pygame.quit()
sys.exit()

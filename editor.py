import sys
import os
import json
import pygame

from scripts.utils import load_images
from scripts.tilemap import Tilemap
from scripts.utils import render_centered_text

RENDER_SCALE = 3.0
SAVE_STATE_PATH = "data/editor_state.txt"

class Editor:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('editor')
        self.screen = pygame.display.set_mode((960, 720))
        self.display = pygame.Surface((320, 240))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 12)

        # Retrieves and sorts map files
        self.map_files = sorted(
            [f for f in os.listdir('data/maps') if f.endswith('.json')],
            key=lambda name: int(name.split('.')[0])
        )
        self.map_files = [f'data/maps/{f}' for f in self.map_files]

        # Load last map index from file (or default to 0)
        if os.path.exists(SAVE_STATE_PATH):
            try:
                with open(SAVE_STATE_PATH, "r") as f:
                    self.current_map_index = int(f.read().strip())
            except:
                self.current_map_index = 0
        else:
            self.current_map_index = 0

        # Visual assets
        self.assets = {
            'grass': load_images('tiles/grass'),
            'stone': load_images('tiles/stone'),
            'sand': load_images('tiles/sand'),
            'pagoda': load_images('tiles/pagoda'),
            'cursed_pagoda': load_images('tiles/cursed_pagoda'),
            'platform': load_images('tiles/platform'),  
            'half_tile': load_images('tiles/half_tile'),        
            'small_decor': load_images('tiles/small_decor'),
            'large_decor': load_images('tiles/large_decor'),
            'flora': load_images('tiles/flora'),
            'village_decor': load_images('tiles/village_decor'),            
            'spawners': load_images('tiles/spawners'),
            'pickups': load_images('tiles/pickups', scale=(16, 16)),
            'crumble_blocks': load_images('tiles/crumble_blocks', scale=(16, 16)),  
            'spikes': load_images('tiles/spikes'),
        }
        
        self.movement = [False, False, False, False]        
        self.tilemap = Tilemap(self, tile_size=16)
        
        # Load map data
        try:
            self.tilemap.load(self.map_files[self.current_map_index])
        except FileNotFoundError:
            pass
                    
        self.scroll = [0, 0]
        
        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0
        
        self.clicking = False
        self.right_clicking = False
        self.shift = False       
        self.ongrid = True
        self.flip_x = False
        self.flip_y = False
        self.brush_size = 1

    # Draws minimap in the upper right coorner
    def draw_minimap(self):
        minimap_scale = 0.2  
        width = int(self.display.get_width() * minimap_scale)
        height = int(self.display.get_height() * minimap_scale)

        minimap_surface = pygame.Surface((width, height))
        minimap_surface.fill((10, 10, 10))

        mini_scroll = [s * minimap_scale for s in self.scroll]
        self.tilemap.render(minimap_surface, offset=mini_scroll, scale=minimap_scale)

        self.display.blit(minimap_surface, (self.display.get_width() - width - 2, 2))

    # Allows placement of one to mutiple tiles depending on the size of the brush
    def apply_brush(self, tile_pos):
        for dy in range(self.brush_size):
            for dx in range(self.brush_size):
                px, py = tile_pos[0] + dx, tile_pos[1] + dy
                self.tilemap.tilemap[f"{px};{py}"] = {
                    'type': self.tile_list[self.tile_group],
                    'variant': self.tile_variant,
                    'pos': (px, py),
                    'flip_x': self.flip_x,
                    'flip_y': self.flip_y
                }

    def run(self):
        while True:
            self.display.fill((0, 0, 0))
            
            self.scroll[0] += (self.movement[1] - self.movement[0]) * 3
            self.scroll[1] += (self.movement[3] - self.movement[2]) * 3           
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            self.tilemap.render(self.display, offset = render_scroll)
            
            original_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant]
            # Allows for flipping of the asset horizontally and vertically
            current_tile_img = pygame.transform.flip(original_img, self.flip_x, self.flip_y).copy()

            current_tile_img.set_alpha(100)
            
            mpos = pygame.mouse.get_pos()
            mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)
            
            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size), int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))
            
            # Display the brush overlay of tile(s)
            if self.ongrid:
                for dy in range(self.brush_size):
                    for dx in range(self.brush_size):
                        px = tile_pos[0] + dx
                        py = tile_pos[1] + dy
                        draw_x = px * self.tilemap.tile_size - self.scroll[0]
                        draw_y = py * self.tilemap.tile_size - self.scroll[1]
                        self.display.blit(current_tile_img, (draw_x, draw_y))
            else:
                self.display.blit(current_tile_img, mpos)
            # Use brush on the grid    
            if self.clicking and self.ongrid:
                self.apply_brush(tile_pos)

            if self.right_clicking:
                tile_loc = str(tile_pos[0]) + ';' + str(tile_pos[1])
                # Remove on grid tiles  
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                # Remove off grid tiles
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile['type']][tile['variant']]
                    tile_r = pygame.Rect(tile['pos'][0] - self.scroll[0], tile['pos'][1] - self.scroll[1], tile_img.get_width(), tile_img.get_height())
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)
                    
            self.display.blit(current_tile_img, (5,5))
            
            # Handle user interaction section, beginning with quitting
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                # Add tiles to the grid
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True
                        if not self.ongrid:
                            self.tilemap.offgrid_tiles.append({
                            'type': self.tile_list[self.tile_group],
                            'variant': self.tile_variant,
                            'pos': (mpos[0] + self.scroll[0], mpos[1] + self.scroll[1]),
                            'flip_x': self.flip_x,
                            'flip_y': self.flip_y
                            })
                    # Signals for deletion of the hovered tile
                    if event.button == 3:
                        self.right_clicking = True
                    # Allows holding shift and mousewheel to go through variants of chosen tile type
                    if self.shift:
                        if event.button == 4:
                            self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])
                        if event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])                          
                    # Else mouswheel cycles tile types
                    else:
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                            self.tile_variant = 0
                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)  
                            self.tile_variant = 0          
                # Handle lifting off of the mouse buttons to allow holding them down                  
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False 
                    if event.button == 3:
                        self.right_clicking = False  
                # Handles all other button presses for movement and other features                                                   
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    # Swap on and off grid, save and autotile
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    if event.key == pygame.K_o:
                        self.tilemap.save(self.map_files[self.current_map_index])
                    if event.key == pygame.K_t:
                        self.tilemap.autotile()
                    # For holding shift for mousewheel functionality
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                    # Flips image vertically/horizontally
                    if event.key == pygame.K_f:  
                        self.flip_x = not self.flip_x
                    if event.key == pygame.K_v:  
                        self.flip_y = not self.flip_y
                    # Changes brush size
                    if event.key == pygame.K_EQUALS or event.key == pygame.K_KP_PLUS:
                        self.brush_size += 1
                    if event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                        self.brush_size = max(1, self.brush_size - 1)
                    # Cycles through list of maps
                    if event.key == pygame.K_LEFTBRACKET:
                        self.current_map_index = (self.current_map_index - 1) % len(self.map_files)
                        self.tilemap.load(self.map_files[self.current_map_index])
                        with open(SAVE_STATE_PATH, "w") as f:
                            f.write(str(self.current_map_index))                 
                    if event.key == pygame.K_RIGHTBRACKET:
                        self.current_map_index = (self.current_map_index + 1) % len(self.map_files)
                        self.tilemap.load(self.map_files[self.current_map_index])
                        with open(SAVE_STATE_PATH, "w") as f:
                            f.write(str(self.current_map_index))
                # Handles lifting off of keys to enable holding them down
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False

            # Draw minimap and level number text
            self.draw_minimap()
            map_name = os.path.basename(self.map_files[self.current_map_index])
            render_centered_text(self.display, f"Level: {map_name}", self.font, 12, (255, 255, 255), 6, False)
            
            # Draw screen and update
            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)

Editor().run()
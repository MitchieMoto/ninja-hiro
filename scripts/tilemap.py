import json
import pygame
import math

# Specifies how to autotile specific blocks with 9 tiles, 0 is top left and it continues in a clockwise spiral
AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(-1, 0), (0, -1), (0,1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8,
}

NEIGHBOR_OFFSETS = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]
PHYSICS_TILES = {'grass', 'stone', 'sand', 'pagoda', 'cursed_pagoda'}
PLATFORM_TILES = {'platform'}
HARMFUL_TILES = {'spikes'}
AUTOTILE_TYPES = {'grass', 'stone', 'sand', 'pagoda', 'cursed_pagoda'}

# Maps of 16 x 16 blocks 
class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []
        self.PLATFORM_TILES = {'platform'}

    # Extracts the data from the tilemap, removing certain tiles, such as initial spawners
    def extract(self, id_pairs, keep=False):
        matches = []
        # Handle offgrid tiles (pixel unit position)
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)

        # Handle tilemap tiles (tile map position)
        for loc in list(self.tilemap):
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                matches[-1]['pos'] = [
                    matches[-1]['pos'][0] * self.tile_size,
                    matches[-1]['pos'][1] * self.tile_size
                ]
                if not keep:
                    del self.tilemap[loc]
        return matches
                    
    # Checks tiles for the existence of neighbors around it
    def tiles_around(self, pos):
        tiles = []
        # Retrieve tilemap position from pixel position
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        # Check each direction 
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles
    
    # Checks for platforms around
    def platform_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile['type'] == 'platform':
                rects.append(pygame.Rect(
                    tile['pos'][0] * self.tile_size,
                    tile['pos'][1] * self.tile_size,
                    self.tile_size,
                    self.tile_size
                ))
        return rects

    # Saves the tilemap and offgrid data on 'o' press
    def save(self, path):
        f = open(path, 'w')
        json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size, 'offgrid': self.offgrid_tiles}, f)
        f.close()
        
    # Loads a map
    def load(self, path):
        self.tilemap = {}
        self.offgrid_tiles = []
        try:
            with open(path, 'r') as f:
                map = f.read().strip()
                # Do not read from an empty file, mainly for new map creation
                if not map:
                    return
                # Read map data if it exists
                else:
                    map_data = json.loads(map)
                # Set the tilemap, offgrid tiles and tile size from the map data
                self.tilemap = map_data.get('tilemap', {})
                self.tile_size = map_data.get('tile_size', self.tile_size)
                self.offgrid_tiles = map_data.get('offgrid', [])
        except FileNotFoundError:
            print(f"[Warning] Map file not found: {path}")
        except Exception as e:
            print(f"[Error] Unexpected error loading map '{path}': {e}")

    # Return a tiles map coordinates from their pixel coordinates
    def get_tile_at(self, pos):
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        return self.tilemap.get(tile_loc)

    # Checks if a tile is listed as a phsyics tile
    def solid_check(self, pos):
        tile = self.get_tile_at(pos)
        return tile if tile and tile['type'] in PHYSICS_TILES else None

    # Checks for tiles which interact with entities at all times, or have no specific movement characteristics 
    def physics_rects_around(self, pos, include_spikes=False):
        rects = []
        for tile in self.tiles_around(pos):
            if tile['type'] in PHYSICS_TILES or tile['type'] == 'half_tile' or (include_spikes and tile['type'] in HARMFUL_TILES):
                x = tile['pos'][0] * self.tile_size
                y = tile['pos'][1] * self.tile_size
                rects.append(pygame.Rect(x, y, self.tile_size, self.tile_size))
        return rects

    # Automatically reshuffles certain tile types to form a more cohesive design
    def autotile(self):
        # Check every location in the map
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            # Check each side for a neighbor
            for shift in [(1,0), (-1,0), (0, -1), (0, 1)]:
                check_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                # If a neighbor exists
                if check_loc in self.tilemap:
                    # If it is of the same tile type as the neighbor add that direction
                    if self.tilemap[check_loc]['type'] == tile['type']:
                        neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            # If its an autotile type, reskin the tiles according to their relative positions
            if (tile['type'] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbors]

    # Returns dangerous tiles, currently just spikes
    def is_dangerous_tile(self, pos):
        tile = self.get_tile_at(pos)
        return tile and tile.get('type') == 'spikes'

    # Render the tilemap and offgrid tiles
    def render(self, surf, offset=(0, 0), scale=1.0):
        # Offgrid tiles (pixel-based)
        for tile in self.offgrid_tiles:
            img = self.game.assets[tile['type']][tile['variant']]
            # Vertical and horizontal flips
            if tile.get('flip_x') or tile.get('flip_y'):
                img = pygame.transform.flip(img, tile.get('flip_x', False), tile.get('flip_y', False))
            # Optional scaling
            if scale != 1.0:
                img = pygame.transform.scale(
                    img,
                    (int(img.get_width() * scale), int(img.get_height() * scale))
                )
            surf.blit(img, (tile['pos'][0] * scale - offset[0], tile['pos'][1] * scale - offset[1]))

        # Get number of tiles needed to fill screen and offset coords
        tile_span_x = surf.get_width() / (self.tile_size * scale)
        tile_span_y = surf.get_height() / (self.tile_size * scale)
        start_x = int(math.floor(offset[0] / (self.tile_size * scale)))
        start_y = int(math.floor(offset[1] / (self.tile_size * scale))) 

        # Grid-aligned tiles, renders them as they are needed when moving across the screen        
        for x in range(start_x - 1, int(start_x + tile_span_x) + 2):
            for y in range(start_y - 1, int(start_y + tile_span_y) + 2):
                
                # Checks tiles in range for their images, flipping or scaling as needed
                loc = f"{x};{y}"
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    img = self.game.assets[tile['type']][tile['variant']]
                    if tile.get('flip_x') or tile.get('flip_y'):
                        img = pygame.transform.flip(img, tile.get('flip_x', False), tile.get('flip_y', False))
                    if scale != 1.0:
                        img = pygame.transform.scale(
                            img,
                            (int(img.get_width() * scale), int(img.get_height() * scale))
                        )
                    # Use pixel coords for the actual display image
                    px = tile['pos'][0] * self.tile_size * scale - offset[0]
                    py = tile['pos'][1] * self.tile_size * scale - offset[1]
                    surf.blit(img, (px, py))

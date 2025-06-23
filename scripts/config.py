SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240
FPS = 60
DEFAULT_MUSIC_VOLUME = 0.2
DEFAULT_SFX_VOLUME = 0.3
MAX_RAMEN_DURATION = 15 * FPS

ASSET_PATHS = {
    'tiles': [
        ('grass', 'tiles/grass'),
        ('stone', 'tiles/stone'),
        ('sand', 'tiles/sand'),
        ('pagoda', 'tiles/pagoda'),
        ('cursed_pagoda', 'tiles/cursed_pagoda'),
        ('half_tile', 'tiles/half_tile'),
        ('platform', 'tiles/platform'),        
        ('small_decor', 'tiles/small_decor'),
        ('large_decor', 'tiles/large_decor'),
        ('flora', 'tiles/flora'),
        ('village_decor', 'tiles/village_decor'),
        ('spikes', 'tiles/spikes'),
        ('crumble_blocks', 'tiles/crumble_blocks'),
    ],
    'clouds': 'clouds',
    'lanterns': 'lanterns',
    'birds': {
        'sparrows': 'birds/sparrows',
    },
    'backgrounds': {
        'forest': 'backgrounds/forest.png',
        'forest_night': 'backgrounds/forest_night.png',
        'bamboo_forest': 'backgrounds/bamboo_forest.png',
        'beach': 'backgrounds/beach.png',
        'pagoda_realm': 'backgrounds/pagoda_realm.png',
        'cursed_pagoda_realm': 'backgrounds/cursed_pagoda_realm.png',
        'oni': 'backgrounds/oni.png',
    },
    'weapons': {
        'gun': 'weapons/gun.png',
        'blowgun' : 'weapons/blowgun.png',
        'projectile': 'weapons/projectile.png',
        'player_projectile': 'weapons/player_projectile.png',
        'blowdart' : 'weapons/blowdart.png',
    },
    'icons': {
        'spicy_ramen': 'ui/spicy_ramen.png',
        'sushi_shield': 'ui/sushi_shield.png',
        'smoke_bomb': 'ui/smoke_bomb.png',
        'blowgun': 'ui/blowgun.png',
        'spirit_blessing': 'ui/spirit_blessing.png', 
    },
    'pickups': {
        'ramen': 'pickups/ramen.png',
        'sushi': 'pickups/sushi.png',
        'spirit_blessing': 'pickups/spirit_blessing.png',
    },
    'particles': {
        'leaf': ('particles/leaf', 20),
        'cherry_blossom': ('particles/cherry_blossom', 20),
        'cherry_blossom_dash': ('particles/cherry_blossom_dash', 6),
        'particle': ('particles/particle', 6),
        'cloud_jump': ('particles/cloud_jump', 2),
        'divine_flame': ('particles/divine_flame', 2)
    },
    'enemies': {
        'gunner': {
            'idle': ('entities/enemies/gunner/idle', 6),
            'run': ('entities/enemies/gunner/run', 4)
        },
        'oni': {
            'idle': ('entities/enemies/oni/idle', 12),
            'run': ('entities/enemies/oni/run', 8)
        },
        'yurei': {
            'idle': ('entities/enemies/yurei/idle', 12),
            'run': ('entities/enemies/yurei/run', 8)
        }
    }
}

SFX_PATHS = {
    'jump': ('data/sfx/jump.wav', 0.2),
    'cloud_jump': ('data/sfx/cloud_jump.wav', 0.1),
    'slide_jump': ('data/sfx/slide_jump.wav', 0.2),
    'dash': ('data/sfx/dash.wav', 0.2),
    'slide': ('data/sfx/slide.wav', 0.1),
    'smoke_bomb': ('data/sfx/smoke_bomb.wav', 0.3),
    'hit': ('data/sfx/hit.wav', 0.3),
    'shoot': ('data/sfx/shoot.wav', 0.1),
    'blowgun': ('data/sfx/blowgun.wav', 0.4),
    'ambience': ('data/sfx/ambience.wav', 0.2),
    'cicada': ('data/sfx/cicada.wav', 0.04),    
    'pickup_spicy_ramen': ('data/sfx/spicy_ramen.wav', 0.3),
    'pickup_sushi_shield': ('data/sfx/sushi_shield.wav', 0.3),
    'pickup_spirit_blessing': ('data/sfx/spirit_blessing.wav', 0.3),
    'sushi_shield_shatter': ('data/sfx/sushi_shield_shatter.wav', 0.4),
    'oni_death': ('data/sfx/oni_death.wav', 0.4),
    'yurei_death': ('data/sfx/yurei_death.wav', 0.4),
    'gong': ('data/sfx/gong.wav', 0.2),
    'rain': ('data/sfx/rain.wav', 0.05)  
}

STAGE_THEMES = {
            "forest": {
                "range": range(0, 6),
                "music": "data/music/forest_theme.wav",
                "background":'forest',
                "ambience": True,
                "bird": "sparrows"
            },
            "forest_night": {
                "range": range(6, 11),
                "music": "data/music/forest_night_theme.wav",
                "background":'forest_night',
                "ambience": True,
                "bird": "sparrows",
                "cicada": True,
                "rain": True
            },
            "pagoda_realm": {
                "range": range(11, 21),
                "music": "data/music/pagoda_realm_theme.wav",
                "background":'pagoda_realm',
                "lanterns": True,
                "ambience": True
            },
            "bamboo_forest": {
                "range": range(21, 26),
                "music": "data/music/forest_theme.wav",
                "background":'bamboo_forest',
                "ambience": True,
                "bird": "sparrows",
                "cicada": True,
                "rain": True
            },
            "beach": {
                "range": range(26, 31),
                "music": "data/music/beach_theme.wav",
                "background":'beach',
                "ambience": True,
                "bird": "sparrows",
                "rain": True
            },
            "cursed_pagoda_realm": {
                "range": range(31, 41),
                "music": "data/music/pagoda_realm_theme.wav",
                "background":'cursed_pagoda_realm',
                "lanterns": True
            },
            "oni": {
                "range": range(41, 100),
                "music": "data/music/oni_theme.wav",
                "background":'oni',
                "rain": True
            }
        }

COLOR_CODES = {
    # REDS
    "Akane": (183, 40, 46),  # Deep red
    "Enji": (159, 53, 58),  # Dark red
    "Kurenai": (203, 27, 69),  # Crimson
    "Akabeni": (203, 64, 66),  # Bright red
    "Shinsyu": (171, 59, 58),  # True red
    "Ichigo": (181, 73, 91),  # Strawberry red
    "Imayoh": (208, 90, 110),  # Modern pink
    "Nakabeni": (219, 77, 109),  # Medium crimson
    "Karakurenai": (208, 16, 76),  # Deep crimson
    "Ginsyu": (199, 62, 58),  # Silver vermilion
    "Syojyohi": (232, 48, 21),  # Scarlet

    # PINKS
    "Sakura": (254, 223, 225),  # Pale pink
    "Toki": (238, 169, 169),  # Pinkish hue
    "Taikoh": (248, 195, 205),  # Light pink
    "Ikonzome": (244, 167, 185),  # Light rose pink
    "Momo": (245, 150, 170),  # Peach pink
    "Usubeni": (232, 122, 144),  # Light crimson
    "Cyohtsun": (191, 103, 102),  # Long spring pink
    "Jinzamomi": (235, 122, 119),  # Deep pink
    "Akebono": (241, 148, 131),  # Dawn pink

    # BLUES
    "Mizu": (162, 215, 221),  # Light blue
    "Ai": (22, 94, 131),  # Indigo
    "Kon": (0, 56, 84),  # Deep navy blue
    "Tetsuonando": (47, 79, 89),  # Iron blue-gray
    "Kachi": (27, 47, 59),  # Victory color (dark indigo)
    "Gunjo": (63, 100, 140),  # Ultramarine

    # PURPLES
    "Kikyou": (86, 84, 162),  # Bellflower purple
    "Suoh": (142, 53, 74),  # Dark reddish-purple

    # BROWNS / EARTH TONES
    "Kuwazome": (100, 54, 60),  # Mulberry dye
    "Azuki": (149, 74, 69),  # Azuki bean red
    "Kuriume": (144, 72, 64),  # Chestnut plum
    "Ebicha": (115, 67, 56),  # Shrimp brown
    "Kurotobi": (85, 66, 54),  # Black kite
    "Benitobi": (153, 70, 57),  # Crimson kite
    "Benikaba": (181, 68, 52),  # Crimson birch
    "Mizugaki": (185, 136, 125),  # Water persimmon
    "Sangosyu": (241, 124, 103),  # Coral vermilion
    "Benihiwada": (136, 76, 58),  # Crimson cypress bark
    "Entan": (215, 84, 85),  # Lead red
    "Shikancha": (181, 93, 76),  # Brownish-red tea
    "Hiwada": (133, 72, 54),  # Cypress bark
    "Suohkoh": (169, 99, 96),  # Sappanwood incense
    "Kokiake": (134, 71, 63),  # Deep scarlet

    # OFF-WHITES, GRAYS & BLACKS
    "Kuro": (13, 13, 13),  # Black
    "Shironeri": (243, 243, 243),  # Unbleached silk white
    "Umenezumi": (158, 122, 122),  # Plum mouse gray
    "Sakuranezumi": (177, 150, 147),  # Cherry blossom mouse gray
    "Haizakura": (215, 196, 187),  # Gray cherry blossom

    # GREEN
    "Matcha": (197, 197, 106),  # Green tea

    # YELLOW / ORANGE
    "Kohaku": (202, 122, 44),  # Amber
}

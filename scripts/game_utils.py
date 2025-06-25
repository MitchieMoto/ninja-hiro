import pygame
import math
import random
from scripts.animation import Animation
from scripts.utils import load_image, load_images, load_sound, render_text, render_centered_text, pause_menu, show_message_screen, scaled_anim
from scripts.config import ASSET_PATHS, SFX_PATHS
from scripts.pickups import pickup
from scripts.entities import Gunner, Oni, Yurei
from scripts.particle import Particle
from scripts.spark import Spark
from scripts.lanterns import Lanterns 
from scripts.spikes import Spike
from scripts.weather import RainSystem
from scripts.config import COLOR_CODES
from scripts.crumble_blocks import CrumbleBlock

# Load and group assets
def load_assets():
    assets = {}

    # Tiles and decor
    for key, path in ASSET_PATHS['tiles']:
        assets[key] = load_images(path)

    # Clouds
    assets['clouds'] = load_images(ASSET_PATHS['clouds'])

    # Lanterns
    assets['lanterns'] = load_images(ASSET_PATHS['lanterns'])

    # Birds 
    for bird_type, path in ASSET_PATHS['birds'].items():
        assets[bird_type] = load_images(path)

    # Backgrounds
    for key, path in ASSET_PATHS['backgrounds'].items():
        assets[key] = load_image(path)

    # Weapons
    for key, path in ASSET_PATHS['weapons'].items():
        assets[key] = load_image(path)

    # Icons
    for key, path in ASSET_PATHS['icons'].items():
        assets[f'icon/{key}'] = load_image(path, (32, 32))

    # Pickups
    for key, path in ASSET_PATHS['pickups'].items():
        assets[f'pickup/{key}'] = load_image(path, (16, 16))

    # Particles
    for key, (path, duration) in ASSET_PATHS['particles'].items():
        assets[f'particle/{key}'] = Animation(load_images(path), img_dur=duration, loop=False)

    # Enemies
    for enemy, actions in ASSET_PATHS['enemies'].items():
        for action, (path, dur) in actions.items():
            assets[f'{enemy}/{action}'] = Animation(load_images(path), img_dur=dur)

    return assets

# Load all sfx
def load_sounds():
    return {key: load_sound(path, volume) for key, (path, volume) in SFX_PATHS.items()}

# Plays music
def play_music(path, volume=0.2):
    pygame.mixer.music.stop()
    pygame.mixer.music.load(path)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(-1)

# Displays UI elements to the screen, also handles tips
def render_game_ui(game):
    # Timer strings
    current_time_str = f"Time: {game.timer:.2f}s"
    best_time_val = game.save_data["best_times"].get(str(game.level))
    best_time_str = f"Best: {best_time_val:.2f}s" if best_time_val is not None else "Best: --"
    current_level = str(game.level)
    current_level_str = f"Level:{current_level}"

    # Render timer and level texts
    render_text(game.display_2, best_time_str, game.font_path, 8, COLOR_CODES["Kohaku"], 6, 6, True)
    render_text(game.display_2, current_time_str, game.font_path, 8, COLOR_CODES["Shironeri"], 6, 22, True)
    render_text(game.display_2, current_level_str, game.font_path, 8, COLOR_CODES["Kohaku"], game.display.get_width() - 80, 6, True)

    # Render any player buffs
    draw_player_ui(
        game.display_2,
        game.player,
        game.assets,
        game.font_path,
        game.display_2.get_height()
    )

    # Render any applicble tip messages
    handle_tip_messages(game)
    update_tip_queue(game)

# Fetches stage info for setting the level's theme
def get_stage_theme_data(level, stage_themes):
    # Set levels to have bosses, for potential theme overloads
    oni_levels = {10, 20}
    if level in oni_levels:
        oni_data = stage_themes["oni"]
        return {
            "theme": "oni",
            "music": oni_data["music"],
            "background": oni_data["background"],
            "bird": oni_data.get("bird"),
            "rain": oni_data.get("rain"),   
        }
    # Returns theme info from config
    for theme, data in stage_themes.items():
        if level in data["range"]:
            return {
                "theme": theme,
                "music": data["music"],
                "background": data["background"],
                "ambience": data.get("ambience"),                
                "bird": data.get("bird"),
                "cicada": data.get("cicada"),
                "rain": data.get("rain"),
                "lanterns": data.get("lanterns")     
            }

    # Fallback to forest theme
    forest_data = stage_themes["forest"]
    return {
        "theme": "forest",
        "music": "data/music/level_music.wav",
        "background": forest_data["background"],
        "ambience": data.get("ambience"), 
        "bird": forest_data.get("bird"),
        "rain": forest_data.get("rain")
    }

# Calls all functions to handle level setup
def load_level(game, map_id):
    # Gets theme info
    theme_data = get_stage_theme_data(game.level, game.stage_themes)

    # Set birds per theme (currently just sparrows)
    game.Sparrows.configure(theme_data)

    # Sets rain, default off
    game.rain = None

    # Enable lanterns only for pagoda_realm-themed levels and play gong on level start
    if theme_data.get("lanterns"):
        if theme_data.get("theme") == "cursed_pagoda_realm":
            lantern_images = game.assets.get('lanterns', [])  # change to cursed_lanterns later
        elif theme_data.get("theme") == "pagoda_realm":
            lantern_images = game.assets.get('lanterns', []) 
            game.dedicated_channels["gong"].play(game.sfx['gong'])            
        screen_size = game.display.get_size()
        game.lanterns = Lanterns(lantern_images, screen_size, count=12)
    else:
        game.lanterns = None
        game.dedicated_channels["gong"].stop()

    # Switch music only on theme change
    if game.current_music_theme != theme_data["theme"]:
        stop_dedicated_channels(game)
        play_music(theme_data["music"], volume=0.25)
        game.current_music_theme = theme_data["theme"]

    # Add ambience sfx to most levels
    if theme_data.get("ambience"):
        game.dedicated_channels["ambience"].play(game.sfx['ambience'], loops=-1)
    else:
        game.dedicated_channels["ambience"].stop()

    # Add cicada sfx to certain levels
    if theme_data.get("cicada"):
        game.dedicated_channels["cicada"].play(game.sfx['cicada'], loops=-1)
    else:
        game.dedicated_channels["cicada"].stop()

    # Set background
    background_image = game.assets[theme_data["background"]]
    game.assets['background'] = pygame.transform.scale(
        background_image,
        game.display.get_size()
    )

    # Sets rain on applicable themes
    if theme_data.get("rain"):
        from scripts.weather import RainSystem
        game.rain = RainSystem(game.player)
        game.dedicated_channels["rain"].play(game.sfx['rain'], loops=-1)
    else:
        game.dedicated_channels["rain"].stop()

    # Load tilemap and get level number
    game.tilemap.load(f"data/maps/{game.map_files[map_id]}")
    game.current_map_id = int(game.map_files[map_id].split('.')[0])

    # Loads crumble blocks
    game.crumble_blocks = []
    if 'crumble_blocks' in game.assets:
        for i, image in enumerate(game.assets['crumble_blocks']):
            for tile in game.tilemap.extract([('crumble_blocks', i)]):
                game.crumble_blocks.append(CrumbleBlock(game, tile, image))

    # Set leaf spawns on specific tree types
    game.leaf_spawners = []
    game.sakura_leaf_spawners = []

    # Normal leaves
    for regular_tree in game.tilemap.extract([('flora', 1)], keep=True):
        game.leaf_spawners.append({
            'rect': pygame.Rect(4 + regular_tree['pos'][0], 4 + regular_tree['pos'][1], 23, 13),
            'type': 'leaf'
        })

    # Sakura leaves
    for sakura_tree in game.tilemap.extract([('flora', 2)], keep=True):
        game.sakura_leaf_spawners.append({
            'rect': pygame.Rect(26 + sakura_tree['pos'][0], 10 + sakura_tree['pos'][1], 23, 13),
            'type': 'cherry_blossom'
        })

    # Spawn entities, the player and enemies
    game.enemies = []
    for spawner in game.tilemap.extract([('spawners', 0), ('spawners', 1), ('spawners', 2), ('spawners', 3)]):
        if spawner['variant'] == 0:
            game.player.pos = spawner['pos']
            game.player.reset_effects()
        elif spawner['variant'] == 1:
            game.enemies.append(Gunner(game, spawner['pos'], (8, 15)))
        elif spawner['variant'] == 2:
            game.enemies.append(Oni(game, spawner['pos'], (8, 15)))
        elif spawner['variant'] == 3:
            game.enemies.append(Yurei(game, spawner['pos'], (8, 20)))

    # Spawn pickups
    game.pickups = []
    for pickup_data in game.tilemap.extract([('pickups', 0), ('pickups', 1), ('pickups', 2)]):
        if pickup_data['variant'] == 0:
            pickup_type = 'ramen'
        elif pickup_data['variant'] == 1:
            pickup_type = 'sushi'
        elif pickup_data['variant'] == 2:
            pickup_type = 'spirit_blessing'  
        else:
            continue

        image = game.assets[f'pickup/{pickup_type}']
        game.pickups.append(pickup(game, pickup_data['pos'], pickup_type, image))

    # Load spike tiles
    game.spikes = []
    for tile in game.tilemap.extract([('spikes', 0), ('spikes', 1)], keep = True):
        game.spikes.append(Spike(game, tile))

    # Reset certain level based game states
    game.projectiles = []
    game.particles = []
    game.sparks = []
    game.scroll = [0, 0]
    game.dead = 0
    game.transition = -30
    game.timer = 0
    game.movement = [False, False]

    # Setup tutorials for the level
    game.tutorial_shown = {}
    game.tip_queue = []
    game.messages = []
    game.level_start_time = game.timer  
    setup_tutorials(game)

# Create player settings from character selection
def create_player(game):
    char_info = game.character_data[game.character_id]
    size = tuple(char_info["size"])
    path = char_info["sprite"]
    scale = char_info.get("scale", 1.0)

    base_path = path.replace(".png", "")

    # Load animations using scaled_anim for potential scaling
    game.assets['player/idle'] = scaled_anim(base_path + '/idle', scale, dur=6)
    game.assets['player/run'] = scaled_anim(base_path + '/run', scale, dur=4)
    game.assets['player/jump'] = scaled_anim(base_path + '/jump', scale)
    game.assets['player/slide'] = scaled_anim(base_path + '/slide', scale, dur=6, loop=True)
    game.assets['player/wall_slide'] = scaled_anim(base_path + '/wall_slide', scale)

    # Optional base sprite (first idle frame) for general use
    game.assets['player'] = game.assets['player/idle'].images[0]

    # Return the right player instance
    if game.character_id == "Tengu":
        from scripts.entities import Tengu
        return Tengu(game, (50, 50), size)
    elif game.character_id == "Ninja Hiro":
        from scripts.entities import NinjaHiro
        return NinjaHiro(game, (50, 50), size)
    elif game.character_id == "Ninja Hana":
        from scripts.entities import NinjaHana
        return NinjaHana(game, (50, 50), size)
    elif game.character_id == "Knight":
        from scripts.entities import Knight
        return Knight(game, (50, 50), size)
    else:
        from scripts.entities import NinjaHiro
        return NinjaHiro(game, (50, 50), size)

# Handles all player input
def handle_input(game, render_scroll):
    # For full exit
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        # Handle quit to menu/restart
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                result = pause_menu(game, offset=render_scroll)
                if result == "menu":
                    return "back_to_level_select"
                if result == "restart":
                    load_level(game, game.level)
                    return "restart"
                if not result:
                    pygame.quit()
                    exit()
            # Basic Movement
            if event.key == pygame.K_a:
                game.movement[0] = True
            if event.key == pygame.K_d:
                game.movement[1] = True
            if event.key == pygame.K_w:
                game.player.jump()
            if event.key == pygame.K_s:
                game.player.slide_pressed = True
            # Abilities
            if event.key == pygame.K_LSHIFT:
                game.player.dash()
            if event.key == pygame.K_SPACE:
                if game.player.ability_type == "blowgun":
                    game.player.shoot()
                elif game.player.ability_type == "smoke_bomb":
                    game.player.smoke_bomb()
            # Debug code for hitboxes
            #if event.key == pygame.K_EQUALS:
                #game.debug_hitboxes = not getattr(game, 'debug_hitboxes', False)
        # Handles lifting keys for hold functionality
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                game.movement[0] = False
            if event.key == pygame.K_d:
                game.movement[1] = False
            if event.key == pygame.K_s:
                game.player.slide_pressed = False
    return None

# Handles all projectiles
def handle_projectiles(game, render_scroll):
    # Moves projectiles and increments their timer
    for projectile in game.projectiles.copy():
        projectile["pos"][0] += projectile["vel"][0]
        projectile["pos"][1] += projectile["vel"][1]
        projectile["timer"] += 1

        #  Last 3 seconds at 60 fps
        if projectile["timer"] > 180:
            game.projectiles.remove(projectile)
            continue

        # Checks for wall collisions, if so delete and add sparks
        if game.tilemap.solid_check(projectile["pos"]):
            game.projectiles.remove(projectile)
            for _ in range(4):
                game.sparks.append(Spark(projectile["pos"], random.random() * math.pi * 2, 2 + random.random()))
            continue

        # Handle player projectiles
        if projectile["source"] == "player":
            # On enemy collision
            for enemy in game.enemies[:]:
                if enemy.rect().collidepoint(projectile["pos"]):
                    damage = projectile.get("damage", 1)
                    # Delegate to the enemy's take_damage method
                    killed = hasattr(enemy, 'take_damage') and enemy.take_damage(damage)
                    # Remove enemy if killed, always remove projectile
                    if killed:
                        game.enemies.remove(enemy)
                    game.projectiles.remove(projectile)
                    break

        # Handle enemy projectiles while not dashing
        elif projectile["source"] == "enemy" and abs(game.player.dashing) < 50:
            # On player collision
            if game.player.rect().collidepoint(projectile["pos"]):
            # Ignore if under smoke_bomb effects                
                if game.player.smoke_active_timer > 0 and projectile['source'] == 'enemy':
                    continue  
                # Consume shield if available
                if game.player.has_sushi_shield:
                    game.player.has_sushi_shield = False
                    game.sfx.get('sushi_shield_shatter', game.sfx['hit']).play()
                # Else die and play death animation and effects
                else:
                    game.player.die()
                # Remove the projectile
                game.projectiles.remove(projectile)

        # Acquire sprite assets for projectiles
        sprite_name = projectile.get("sprite", "projectile")
        sprite = game.assets.get(sprite_name)

        # Flip if necessary 
        if sprite:
            if projectile.get("flip", False):
                sprite = pygame.transform.flip(sprite, True, False)
            # Display projectiles
            game.display.blit(sprite, (
                projectile["pos"][0] - sprite.get_width() // 2 - render_scroll[0],
                projectile["pos"][1] - sprite.get_height() // 2 - render_scroll[1]
            ))

# Handles updating, rendering and tracking whether enemies are alive. Also calls draw for certain enemy health bars.
def handle_enemies(game, render_scroll):
    for enemy in game.enemies.copy():
        kill = enemy.update(game.tilemap, (0, 0))
        if kill:
            game.enemies.remove(enemy)
            continue
        enemy.render(game.display, offset=render_scroll)
        # Draw Oni health bars
        if isinstance(enemy, Oni):
            draw_health_bar(game.display_2, enemy, enemy.health, max_health=5, offset=render_scroll)

# Handles pickup removal, as well as messages about them
def handle_pickups(game):
    for pickup in game.pickups[:]:
        collected = pickup.update()
        if collected:
            if pickup.type == 'ramen' and game.level == 3 and not game.tutorial_shown.get(3, False):
                show_tip(game, "Spicy Ramen lets you dash more often!")
                game.tutorial_shown[3] = True

            if pickup.type == 'sushi' and game.level == 5 and not game.tutorial_shown.get(5, False):
                show_tip(game, "Sushi Shield blocks one hit of damage!")
                game.tutorial_shown[5] = True

            if pickup.type == 'spirit_blessing' and game.level == 15 and not game.tutorial_shown.get(15, False):
                show_tip(game, "You can exercise a spirit!")
                game.tutorial_shown[15] = True

            game.pickups.remove(pickup)

# Handles crumble blocks
def handle_crumble_blocks(game, render_scroll):
    for block in game.crumble_blocks:
        block.update()
        block.render(game.display, offset=render_scroll)

# Spawns particles, mainly for trees
def spawn_particles(game, spawners):
    for spawner in spawners:
        rect = spawner['rect']
        if random.random() * 49999 < rect.width * rect.height:
            pos = (
                rect.x + random.random() * rect.width,
                rect.y + random.random() * rect.height
            )
            game.particles.append(Particle(game, spawner['type'], pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))

# Actually draws any given health bars
def draw_health_bar(surf, entity, current_health, max_health, offset=(0, 0), height=4, bg_color=(255, 0, 0), fg_color=(0, 255, 0)):
    rect = entity.rect()
    max_width = rect.width
    health_ratio = max(current_health / max_health, 0)
    bar_width = int(max_width * health_ratio)
    bar_pos = (rect.x - offset[0], rect.y - 8 - offset[1])  # 8px above the enemy

    # Draw background and foreground
    pygame.draw.rect(surf, bg_color, (*bar_pos, max_width, height))  # Background
    pygame.draw.rect(surf, fg_color, (*bar_pos, bar_width, height))  # Foreground

# Draws player UI, including cooldowns and buffs
def draw_player_ui(display, player, assets, font_path, height):
    icon_padding = 6  # spacing between icons

    # Ability Icon padding (Bottom Left)
    icon_x = 8  
    icon_y = height - 50  

    # Draws default smokebomb icon with cooldown display
    if player.ability_type == "smoke_bomb":
        icon = assets.get('icon/smoke_bomb')
        if icon:
            display.blit(icon, (icon_x, icon_y))
            if player.smoke_cooldown_timer > 0:
                cooldown_ratio = player.smoke_cooldown_timer / player.smoke_cooldown_duration
                fill_height = int(icon.get_height() * cooldown_ratio)
                overlay = pygame.Surface((icon.get_width(), fill_height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160))
                display.blit(overlay, (icon_x, icon_y + icon.get_height() - fill_height))
            else:
                pygame.draw.rect(display, (46, 83, 57), (icon_x - 1, icon_y - 1, icon.get_width() + 2, icon.get_height() + 2), 2)
    # Else if blowgun ability, draws blowgun icon with cooldown display   
    elif player.ability_type == "blowgun":
        icon = assets.get('icon/blowgun')
        if icon:
            display.blit(icon, (icon_x, icon_y))
            if player.shoot_timer > 0:
                cooldown_ratio = player.shoot_timer / player.shoot_cooldown
                fill_height = int(icon.get_height() * cooldown_ratio)
                overlay = pygame.Surface((icon.get_width(), fill_height), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160))
                display.blit(overlay, (icon_x, icon_y + icon.get_height() - fill_height))

    # Sushi Shield Icon (Above ability)
    if player.has_sushi_shield:
        sushi_icon = assets['icon/sushi_shield']
        sushi_x = icon_x
        sushi_y = icon_y - sushi_icon.get_height() - icon_padding
        display.blit(sushi_icon, (sushi_x, sushi_y))

    # Spirit Blessing Icon (Above Sushi Shield)
    if player.has_spirit_blessing:
        blessing_icon = assets.get('icon/spirit_blessing')
        if blessing_icon:
            blessing_x = icon_x
            blessing_y = icon_y - 2 * blessing_icon.get_height() - icon_padding * 2
            display.blit(blessing_icon, (blessing_x, blessing_y))

    # Spicy Ramen (centered UI bar)
    if player.ramen_timer > 0:
        max_duration = 15 * 60
        bar_width = 50
        bar_height = 6
        remaining = player.ramen_timer / max_duration

        ramen_icon = assets['icon/spicy_ramen']
        pos = (display.get_width() / 2 - ramen_icon.get_width() * 1.75, height - ramen_icon.get_height() * 1.5)
        bar_x = pos[0] + ramen_icon.get_width() + 4
        bar_y = pos[1] + (ramen_icon.get_height() - bar_height) // 2

        display.blit(ramen_icon, pos)
        pygame.draw.rect(display, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(display, (255, 100, 0), (bar_x, bar_y, int(bar_width * remaining), bar_height))

# Defines intro screen and tutorial messages
def setup_tutorials(game):
    # Show intro screen only once per run
    if game.level == 0 and "level_0_intro" not in game.tutorial_shown:
        show_message_screen(
            game.screen,
            "data/images/backgrounds/HiroDeparture.png",
            game.font_path,
            title="Evil forces have invaded!",
            subtitle="Leave no invader standing and free your allies from their demonic clutches!", #奴らを止めろ!
            wait_for_key=True 
        )
        game.tutorial_shown["level_0_intro"] = True

    # Define level specific tips
    tutorials = {
        0: [("A/D to move", 3, 8),
            ("W to jump/double jump | S to slide", 4, 8),
            ("SHIFT to dash attack | SPACE to smoke bomb", 4, 6),
            ("Smoke bomb grants 2 seconds of invulnerability", 4, 6),],           
        1: [("Jump early in a slide to boosted jump", 4, 8),
            ("You can dash through projectiles", 4, 8)],
        2: [("Fall against walls to wall slide", 3, 8),
            ("Jump during wall slides to wall jump", 3, 8)],
        11: [("You can slide under ceiling spikes", 3, 8),],
        13: [("You can jump through platforms", 3, 8),
             ("S while still to fall through them", 3, 8)]
            # crumble block tutorial?
    }

    # Queue tips only once per level
    level_tip_key = f"level_{game.level}_tips"
    if game.level in tutorials and level_tip_key not in game.tutorial_shown:
        queue_tips(game, tutorials[game.level])
        game.tutorial_shown[level_tip_key] = True

# Sets the queue of tips
def queue_tips(game, tips):
    game.tip_queue = []
    for i, (text, duration, font_size) in enumerate(tips):
        fire_at = game.timer + sum(t[1] for t in tips[:i])
        game.tip_queue.append((fire_at, text, duration, font_size))

# Updates the queue as tips are sent over as messages
def update_tip_queue(game):
    if hasattr(game, "tip_queue") and game.tip_queue:
        fire_at, text, duration, font_size = game.tip_queue[0]
        if game.timer >= fire_at:
            show_tip(game, text, duration, font_size)
            game.tip_queue.pop(0)

# Adds the queued tip to messaages
def show_tip(game, text, duration=3, font_size=8):
    font = pygame.font.Font(game.font_path, font_size)
    game.messages.append((text, duration, game.timer, font))

# Renders all messages
def handle_tip_messages(game):
    for msg_data in game.messages[:]:
        text, duration, start_time, font = msg_data
        if game.timer - start_time > duration:
            game.messages.remove(msg_data)
            continue
        render_centered_text(game.display_2, text, font, 0, (202, 122, 44), game.display_2.get_height() - 10, True)

# Unlocks characters under specific level clear conditions
def check_character_unlocks(game):
    unlocked = game.save_data["unlocked_characters"]

    # Unlock Ninja Hana after completing level 10 
    if game.level == 10 and "Ninja Hana" not in unlocked:
        unlocked.append("Ninja Hana")
        show_message_screen(
            game.screen,
            "data/images/backgrounds/HanaUnlock.png",
            game.font_path,
            title="Character Unlocked!",
            subtitle="You unlocked Ninja Hana! Select her in the character menu.",
            character_sprite_data=game.character_data["Ninja Hana"],
            wait_for_key=True
        )

    # Unlock Tengu after completing level 20 
    elif game.level == 20 and "Tengu" not in unlocked:
        unlocked.append("Tengu")
        show_message_screen(
            game.screen,
            "data/images/backgrounds/TenguUnlock.png",
            game.font_path,
            title="Character Unlocked!",
            subtitle="You unlocked the Tengu! Select him in the character menu.",
            character_sprite_data=game.character_data["Tengu"],
            wait_for_key=True
        )

# Stops all ongoing sfx, used in theme change and game clear
def stop_dedicated_channels(game):
    for channel in game.dedicated_channels:
        game.dedicated_channels[channel].stop()     


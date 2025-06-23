import math
import random
import pygame
from scripts.particle import Particle
from scripts.spark import Spark

# Base physic entity, all entities inherit from it
class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}  
        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip = False
        self.last_movement = [0,0]
    
    # Returns a rect for the actual hitbox, size and position of the player
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    # Sets a character's animation state based on action
    def set_action(self, action):
        if action != self.action:
            self.action = action
            try:
                self.animation = self.game.assets[self.type + '/' + self.action].copy()
            except KeyError:
                print(f"Missing animation: {self.type}/{self.action}")

    # Update a physics entities movement, including base collisions
    def update(self, tilemap, movement=(0, 0), ignore_platforms=False, extra_solids=None):
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        previous_bottom = self.rect().bottom
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        
        # Update horizontal player movement
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        physics_rects = tilemap.physics_rects_around(self.pos, include_spikes=self.spike_collisions())
        # Include crumble blocks from the game if they exist and are in a solid state
        if hasattr(self.game, 'crumble_blocks'):
            physics_rects += [crumble_block.rect for crumble_block in self.game.crumble_blocks if crumble_block.is_solid()]
        # Handles horizontal collisions
        for rect in physics_rects:
            if entity_rect.colliderect(rect):
                # Rightside collision
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                # Leftside collision
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x
        # Update vertical player movement
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        physics_rects = tilemap.physics_rects_around(self.pos, include_spikes=self.spike_collisions())
        # Include crumble blocks from the game if they exist and are in a solid state
        if hasattr(self.game, 'crumble_blocks'):
            physics_rects += [crumble_block.rect for crumble_block in self.game.crumble_blocks if crumble_block.is_solid()]
        # Handles veritcal collisions
        for rect in physics_rects:
            if entity_rect.colliderect(rect):
                # Bottom collision
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                    self.velocity[1] = 0
                # Top collision
                elif frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                    self.velocity[1] = 0
                self.pos[1] = entity_rect.y

        # Handle platform collisions only if falling onto them
        if frame_movement[1] > 0:
            for rect in tilemap.platform_rects_around(self.pos):
                if entity_rect.colliderect(rect):
                    # Go to falling through logic if set
                    if ignore_platforms:
                        continue 
                    # Check if player was above the platform (allowing 1.2px grace, snapping up from under the top of the platform)
                    if previous_bottom <= rect.top + 1.2 and entity_rect.bottom >= rect.top:
                        entity_rect.bottom = rect.top
                        self.collisions['down'] = True
                        self.velocity[1] = 0
                        self.pos[1] = entity_rect.y
        # Ignore all platform collisions after signaling a fall through a platform
        if ignore_platforms:
            # Make sure we don't snap back onto a platform mid-fall
            for rect in tilemap.platform_rects_around(self.pos):
                if self.rect().colliderect(rect):
                    overlap = self.rect().bottom - rect.top
                    # Gentle nudge, when the player is less than halfway through the platform
                    if 0 < overlap < self.size[1] / 2:
                        self.pos[1] += max(overlap / 2, 0.1)  

        # Re-fetch updated rect after physics collision adjustment
        entity_rect = self.rect()
        # Apply gravity
        self.velocity[1] = min(5, self.velocity[1] + 0.1)
        # Update animations every frame
        self.animation.update()
        
    # Base render function
    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset [1] + self.anim_offset[1]))

    # To let enemies treat spikes as walls
    def spike_collisions(self):
        return False

# Base player class for all characters
class BasePlayer(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.set_action('idle')        
        self.air_time = 0
        self.jumps = 2
        self.wall_slide = False
        self.was_grounded = 0
        self.spike_grace_timer = 0

        self.dash_damage = 1        
        self.dashing = 0
        self.dash_cooldown_timer = 0
        self.dash_cooldown_duration = 60 # 1s
        self.dash_cooldown_multiplier = 1.0

        self.sliding = False
        self.slide_triggered = False  # Prevents retrigger for hold
        self.slide_pressed = False
        self.slide_locked = False  # Prevents supplementary movement during a slide
        self.slide_timer = 0
        self.slide_boost_timer = 0        
        self.slide_boost_duration = 30  # 0.5s
        self.slide_cooldown_timer = 0
        self.slide_cooldown_duration = 60  # 1s
        self.drop_through_timer = 0

        self.ramen_timer = 0
        self.has_sushi_shield = False
        self.has_spirit_blessing = False

        self.smoke_active_timer = 0  # Invulnerable state timer 
        self.smoke_duration = 120  # 2s
        self.smoke_cooldown_timer = 0  # Ability cooldown timer        
        self.smoke_cooldown_duration = 480  # 8s

    # Overwritten update function, calls base as well
    def update(self, tilemap, movement=(0, 0), extra_solids=None):
        self.input_vector = list(movement)

        # Restrict supplementary movement during a slide
        if self.sliding and self.slide_timer > 0:
            movement = [0, movement[1]] 
        else:
            movement = self.input_vector 

        # Handle slide input (trigger only once per press)
        if self.slide_pressed and not self.slide_triggered and self.was_grounded > 0:
            self.slide()
            self.slide_triggered = True
        elif not self.slide_pressed:
            self.slide_triggered = False

        # For tracking animation
        self.last_movement = movement  

        # Always update flip from player movement direction
        if self.input_vector[0] != 0:
            self.flip = self.input_vector[0] < 0

        # Slide Logic
        if self.sliding:
            # Apply decaying movement speed during a slide
            if abs(self.velocity[0]) > 0.2:
                decay_rate = 0.02  # slower decay
                if self.velocity[0] > 0:
                    self.velocity[0] = max(self.velocity[0] - decay_rate, 0)
                elif self.velocity[0] < 0:
                    self.velocity[0] = min(self.velocity[0] + decay_rate, 0)
            else:
                self.velocity[0] = 0 
            # Slide ends only if 's' is released, even if stationary
            if not self.slide_pressed:
                self.sliding = False
                self.slide_locked = False
        # Do not allow horizontal movement while sliding
        if self.slide_locked:
            movement[0] = 0

        # Handle drop-through
        ignore_platforms = self.handle_platform_fallthrough()

        # Call base physics
        super().update(tilemap, movement=movement, ignore_platforms=ignore_platforms, extra_solids=extra_solids)

        # Reset jumps, air time and grounded timer when on a tile
        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 2
            self.was_grounded = 4
        # Else increment air time and decrement grounded grace period timer
        elif self.was_grounded > 0:
            self.air_time += 1            
            self.was_grounded -= 1
        # Else player is falling
        else:
            self.air_time += 1

        # Lose a ground jump if you leave the ground, small 4 frame grace window
        if self.jumps == 2 and self.air_time > 4 and not self.collisions['down']:
            self.jumps -= 1

        #  Animation Logic, sliding first
        if self.sliding or self.slide_locked:
            self.set_action('slide')
        # Wall sliding if wall collision during falling or jumping, cannot be grounded
        elif (self.collisions['right'] or self.collisions['left']) and (self.velocity[1] > 0.4 or self.air_time >= 4) and not self.collisions['down'] :
            self.wall_slide = True
            self.air_time = 5
            self.velocity[1] = min(self.velocity[1], 0.5)
            if self.collisions['left']:
                self.flip = True
            elif self.collisions['right']:
                self.flip = False
            self.set_action('wall_slide')
        # Jump animation
        elif self.air_time > 4:
            self.set_action('jump')
            self.wall_slide = False
        # Run animation
        elif self.last_movement[0] != 0:
            self.set_action('run')
            self.wall_slide = False
        # Else idle animation
        else:
            self.set_action('idle')
            self.wall_slide = False

        # Dash particle burst
        if abs(self.dashing) in {60, 50}:
            for _ in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                # Uses cherry_blossom particles for Ninja Hana
                if isinstance(self, NinjaHana):
                    self.game.particles.append(Particle(
                        self.game,
                        'cherry_blossom_dash',
                        self.rect().center,
                        velocity=vel,
                        frame=random.randint(0, 2)
                    ))
                else: 
                    self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=vel, frame=random.randint(0, 7)))

        # Dash cooldown
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= 1

        # Slide and slide boost cooldowns
        if self.slide_boost_timer > 0:
            self.slide_boost_timer -= 1
        if self.slide_cooldown_timer > 0:
            self.slide_cooldown_timer -= 1

        # Basic smoke bomb ability cooldown
        if self.smoke_cooldown_timer > 0:
            self.smoke_cooldown_timer -= 1
        if self.smoke_active_timer > 0:
            self.smoke_active_timer -= 1

        # Ramen timers and dash cooldown override
        if self.ramen_timer > 0:
            self.ramen_timer -= 1
            if self.ramen_timer == 0:
                self.dash_cooldown_multiplier = 1.0

        # Timer for spike damage if shield was used for initial damage
        if self.spike_grace_timer > 0:
            self.spike_grace_timer -= 1

        # Handles directional movement for dash direction
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)

        # Apply dash movement for the first 10 frames of the cooldown
        if abs(self.dashing) > 50:
            self.velocity[0] = (8 if self.dashing > 0 else -8)
            # Spawn particle burst right before dash movement goes off
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            vel = [random.random() * 3 * (1 if self.dashing > 0 else -1), 0]
            # Use cherry blossoms for NinjaHana, particles otherwise
            if isinstance(self, NinjaHana):
                self.game.particles.append(Particle(
                    self.game,
                    'cherry_blossom_dash',
                    self.rect().center,
                    velocity=vel,
                    frame=random.randint(0, 7)
                ))
            else:
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=vel, frame=random.randint(0, 7)))
       
        # Air resistance
        if not self.sliding:
            if self.velocity[0] > 0:
                self.velocity[0] = max(self.velocity[0] - 0.1, 0)
            else:
                self.velocity[0] = min(self.velocity[0] + 0.1, 0)

        # Death when falling out of bounds, need to fall for more than 3 seconds
        if self.air_time > 180:
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1

    # Makes player invisible during dash and adds sushi_shield outline    
    def render(self, surf, offset=(0, 0)):
        # While not in the middle of the initial movement part of a dash
        if abs(self.dashing) <= 50:
            # Get current animation frame
            frame = pygame.transform.flip(self.animation.img(), self.flip, False)
            render_x = self.pos[0] + self.anim_offset[0] - offset[0]
            render_y = self.pos[1] + self.anim_offset[1] - offset[1]

            # Render a bubble sushi shield around the player if they have the buff
            if self.has_sushi_shield:
                glow_width = frame.get_width()
                glow_height = frame.get_height()
                glow_surf = pygame.Surface((glow_width, glow_height), pygame.SRCALPHA)
                color = (140, 240, 255, 100)
                pygame.draw.ellipse(glow_surf, color, glow_surf.get_rect())
                surf.blit(glow_surf, (render_x, render_y))

            # Render spirit flame around the player if they have the buff
            if self.has_spirit_blessing and pygame.time.get_ticks() % 3 == 0:
                angle = random.uniform(-0.3, 0.3)
                radius = random.uniform(0.5, 1.0)
                flame_x = self.rect().centerx + math.cos(angle) * radius
                flame_y = self.rect().centery + math.sin(angle) * radius
                self.game.particles.append(Particle(
                    self.game,
                    'divine_flame',
                    [flame_x, flame_y],
                    velocity=[random.uniform(-0.05, 0.05), random.uniform(-0.25, -0.15)],
                    frame=random.randint(0, 3),
                    alpha=80
                ))
            # Make the player semi-transparent during smoke bomb
            if self.smoke_active_timer > 0:
                frame = frame.copy()
                frame.set_alpha(120)  

            # Draw player sprite
            surf.blit(frame, (render_x, render_y))

            # To display debug hitbox
            if self.game.debug_hitboxes:
                pygame.draw.rect(surf, (0, 255, 0), self.rect().move(-offset[0], -offset[1]), 1)
    
    # Handles jumping physics and animations
    def jump(self):
        # Over ride a slide state
        if self.sliding:
            self.sliding = False
            self.slide_locked = False

        # Handle wall jump velocities
        if self.wall_slide:
            if self.flip and self.input_vector[0] < 0:
                self.velocity[0] = 3.5
                self.velocity[1] = -2.2
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                self.game.sfx['jump'].play()
                return True
            elif not self.flip and self.input_vector[0] > 0:
                self.velocity[0] = -3.5
                self.velocity[1] = -2.2
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                self.game.sfx['jump'].play()
                return True            
        # Handle ground and air jumps
        elif self.jumps:
            slide_boost = 1.3 if self.slide_boost_timer > 0 else 1.0
            self.velocity[1] = -3.1 * slide_boost
            self.jumps -= 1
            self.air_time = 5

            # Cloud burst effects only on air jump
            if self.jumps < 1:
                self.spawn_cloud_burst()
                self.game.sfx['cloud_jump'].play()
            else:
                # Slide jump effects if in speed boost part of a slide
                if slide_boost > 1.0:
                    self.game.sfx['slide_jump'].play()
                    self.spawn_cloud_burst() 
                # Else ground jump sfx
                else:
                    self.game.sfx['jump'].play()
            return True
                
    # Starts dash logic and sets timer            
    def dash(self):
        if self.dash_cooldown_timer == 0:
            self.sliding = False
            self.slide_locked = False
            self.game.sfx['dash'].play()
            # Sets dashing to 60, dash movement ends at 50
            self.dashing = -60 if self.flip else 60
            self.dash_cooldown_timer = int(self.dash_cooldown_duration * self.dash_cooldown_multiplier)

    # Handles player velocity during a slide, also enables dropping from platforms
    def slide(self):
        # Drop through platform logic first
        if abs(self.input_vector[0]) < 0.1 and abs(self.input_vector[1]) < 0.1 and self.was_grounded > 0:
            below_pos = (self.rect().centerx, self.rect().bottom + 1)
            tile = self.game.tilemap.get_tile_at(below_pos)
            if tile and tile.get('type') in self.game.tilemap.PLATFORM_TILES:
                self.drop_through_timer = 4
                self.velocity[1] = max(self.velocity[1], 0.05)
                self.pos[1] += 0.2  # Prevent platform re-collision
                return

        # Actual slide logic, if off cooldown
        if self.slide_cooldown_timer == 0:
            self.sliding = True
            direction = -1 if self.flip else 1

            # Gives the initially boosted slide speed as long as the player is actually moving
            if abs(self.input_vector[0]) > 0:
                self.velocity[0] = max(abs(self.velocity[0]), 2.0) * direction
                self.game.sfx['slide'].play()
            # Else enter slide animation in place, like a crouch
            else:
                self.velocity[0] = 0

            # Put slide on cooldown and set timers
            self.slide_locked = True
            self.slide_boost_timer = 30
            self.slide_cooldown_timer = self.slide_cooldown_duration

    # Reset effects on player, every level
    def reset_effects(self):
        # Movement & jump state
        self.velocity = [0, 0]
        self.air_time = 0
        self.jumps = 2
        self.flip = False  # Optional, depends on spawn direction

        # Dash
        self.dashing = 0
        self.dash_cooldown_timer = 0
        self.dash_cooldown_multiplier = 1.0

        # Slide
        self.sliding = False
        self.slide_triggered = False
        self.slide_locked = False
        self.slide_timer = 0
        self.slide_boost_timer = 0
        self.slide_cooldown_timer = 0

        # Interactive tile timers
        self.drop_through_timer = 0
        self.spike_grace_timer = 0

        # Powerups
        self.ramen_timer = 0
        self.has_sushi_shield = False
        self.has_spirit_blessing = False

        # Smoke bomb
        self.smoke_active_timer = 0
        self.smoke_cooldown_timer = 0

        # Animation reset
        self.set_action('idle')

    # Spawn a burst of clouds under the player
    def spawn_cloud_burst(self, clouds=20):
        foot_x = self.rect().centerx
        foot_y = self.rect().bottom

        # Spawn 20 small clouds unless another count is given
        for _ in range(clouds): 
            # Tight spawn range under the player
            x_offset = random.uniform(-2.5, 2.5)
            y_offset = random.uniform(0, 1.5)
            # Cloud momentum mostly down and slightly outwards
            speed_x = random.uniform(-0.3, 0.3)
            speed_y = random.uniform(0.2, 0.45)

            self.game.particles.append(Particle(
                self.game,
                'cloud_jump',
                [foot_x + x_offset, foot_y + y_offset],
                velocity=[speed_x, speed_y],
                frame=random.randint(0, 3)
            ))

    # Invulnerability smoke bomb
    def smoke_bomb(self):
        # Use ability if off of cooldown
        if self.smoke_cooldown_timer == 0:
            self.smoke_active_timer = self.smoke_duration
            self.smoke_cooldown_timer = self.smoke_cooldown_duration
            self.game.dedicated_channels['smoke_bomb'].play(self.game.sfx['smoke_bomb'])

            # Initial burst of smoke
            for _ in range(25):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(0.5, 1.5)
                vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(Particle(
                    self.game,
                    'cloud_jump',
                    self.rect().center,
                    velocity=vel,
                    frame=random.randint(0, 3),
                ))

    # For recieving spike damage
    def take_spike_damage(self):
        self.game.dead = 1 

    def die(self):
        self.game.dead += 1  
        self.game.sfx['hit'].play()
        self.game.screenshake = max(16, self.game.screenshake)
        for _ in range(30):
            angle = random.random() * math.pi * 2
            speed = random.random() * 5
            self.game.sparks.append(Spark(self.game.player.rect().center, angle, 2 + random.random()))
            self.game.particles.append(Particle(
                self.game, 'particle', self.game.player.rect().center,
                velocity=[
                    math.cos(angle + math.pi) * speed * 0.5,
                    math.sin(angle + math.pi) * speed * 0.5
                ],
                frame=random.randint(0, 7)
            ))

    # Called regularly to update fall through capabilities
    def handle_platform_fallthrough(self):
        if self.drop_through_timer > 0:
            self.drop_through_timer -= 1
            return True
        return False

# ------------------------------------------------------------ Playable characters -----------------------------------------------------------

class NinjaHiro(BasePlayer):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size)
        self.ability_type = "smoke_bomb"

class NinjaHana(BasePlayer):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size)
        self.ability_type = "smoke_bomb"

class Knight(BasePlayer):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size)
        self.ability_type = "smoke_bomb"

class Tengu(BasePlayer):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size)
        self.ability_type = "blowgun"
        self.shoot_cooldown = 30  # frames (0.5s at 60 FPS)
        self.shoot_timer = 0

    # Adds a shooting cooldown timer increment
    def update(self, tilemap, movement=(0, 0), extra_solids=None):
        super().update(tilemap, movement)
        if self.shoot_timer > 0:
            self.shoot_timer -= 1

    # Handles shooting effects and projectile spawns
    def shoot(self):
        if self.shoot_timer == 0:
            self.shoot_timer = self.shoot_cooldown
            direction = -1 if self.flip else 1
            speed = 3.0
            # Position at blowdart gun barrel
            gun_offset_x = 8 * direction
            gun_pos = [self.rect().centerx + gun_offset_x, self.rect().centery]
            # Add projectile
            self.game.projectiles.append({
                "pos": gun_pos,
                "vel": [speed * direction, 0],
                "timer": 0,
                "source": "player",
                "sprite": "blowdart",
                "damage": 1,
                "flip": direction < 0
            })
            # Sound
            self.game.sfx['blowgun'].play()
            # Muzzle flash 
            for _ in range(4):
                angle = random.random() - 0.5 + (math.pi if direction < 0 else 0)
                self.game.sparks.append(Spark(gun_pos, angle, 2 + random.random()))

    # Render player blowdart gun on top of base player render       
    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)
        if self.flip:
            surf.blit(pygame.transform.flip(self.game.assets['blowgun'], True, False), (self.rect().centerx - 4 - self.game.assets['blowgun'].get_width() - offset[0], self.rect().centery - offset[1] -  self.game.assets['blowgun'].get_height() * 2))
        else:
            surf.blit(self.game.assets['blowgun'], (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1] -  self.game.assets['blowgun'].get_height() * 2))

# --------------------------------------------------------------- ENEMIES -----------------------------------------------------------------

# Base enemy class, defines tile checking behavior and damage taking
class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size, e_type='enemy'):
        super().__init__(game, e_type, pos, size)
        self.health = 1

    # Base render class
    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset)

    # Returns True if the tile ahead is walkable and not a spike  
    def is_safe_ahead(self, tilemap):
        # X position in front of enemy
        ahead_x = self.rect().centerx + (-7 if self.flip else 7)
        # Y position just under the feet
        foot_y = self.rect().bottom - 1
        below_y = self.rect().bottom + 1
        return tilemap.solid_check((ahead_x, below_y)) and not tilemap.is_dangerous_tile((ahead_x, foot_y))

    # Basic take damage function, decrementing health until death
    def take_damage(self, amount, ignore_invuln=False):
        # Ignore damage during invulnerability frames
        if hasattr(self, 'invulnerable_timer') and self.invulnerable_timer > 0 and not ignore_invuln:
            return False  

        # Decrement health by damage attack amount and set invulnerability
        self.health -= amount
        if hasattr(self, 'invulnerable_duration'):
            self.invulnerable_timer = self.invulnerable_duration

        # Hit effects
        self.game.sfx['hit'].play()
        self.game.screenshake = max(16, self.game.screenshake)

        # Hit particles
        for _ in range(15):
            angle = random.random() * math.pi * 2
            speed = random.random() * 5
            self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
            self.game.particles.append(Particle(
                self.game, 'particle', list(self.rect().center),
                velocity=[math.cos(angle + math.pi) * speed * 0.5,
                        math.sin(angle + math.pi) * speed * 0.5],
                frame=random.randint(0, 7)
            ))
        # Only returns true on kill
        return self.health <= 0

    # Death function 
    def die(self, sound=None):
        # Death effects
        self.game.screenshake = max(16, self.game.screenshake)
        
        # Death sound, else basic hit noise
        if sound:
            self.game.sfx[sound].play()
        else:
            self.game.sfx['hit'].play()

        # Smaller spark particles
        for _ in range(30):
            angle = random.random() * math.pi * 2
            speed = random.random() * 5
            self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
            self.game.particles.append(Particle(
                self.game, 'particle', list(self.rect().center),
                velocity=[
                    math.cos(angle + math.pi) * speed * 0.5,
                    math.sin(angle + math.pi) * speed * 0.5
                ],
                frame=random.randint(0, 7)
            ))

        # Extra big sparks
        self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random()))
        self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random()))

        # Signals that an enemy should be removed
        return True  

# Gunner
class Gunner(Enemy):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, e_type='gunner')  
        self.walking = 0
        self.set_action('idle')
        
    def update(self, tilemap, movement=(0, 0)):
        # Checks tile ahead to turn around if no tile ahead
        if self.walking:
            # Check for a tile ahead
            ahead_x = self.rect().centerx + (-7 if self.flip else 7)
            ahead_y = self.rect().centery

            # Check for walls
            wall_in_front = tilemap.solid_check((ahead_x, ahead_y))

            # If it's not safe ahead (gap/spike) or a wall is directly in front, turn around
            if not self.is_safe_ahead(tilemap) or wall_in_front:
                self.flip = not self.flip
            else:
                movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
                
            # Decrement walking counter 
            self.walking = max(0, self.walking - 1)
            
            # Handle shooting when idle
            if not self.walking:
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                # Gives enemies a y axis viewrange of 16 pixels
                if (abs(dis[1]) < 16):
                    # Shoot left
                    if (self.flip and dis[0] < 0):
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append({
                        "pos": [self.rect().centerx + (-7 if self.flip else 7), self.rect().centery],
                        "vel": [-1.5 if self.flip else 1.5, 0],
                        "timer": 0,
                        "source": "enemy",
                        "sprite": "projectile"
                        })
                        for i in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1]["pos"], random.random() - 0.5 + math.pi, 2 + random.random()))
                    # Shoot right
                    if (not self.flip and dis[0] > 0):
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append({
                        "pos": [self.rect().centerx + (-7 if self.flip else 7), self.rect().centery],
                        "vel": [-1.5 if self.flip else 1.5, 0],
                        "timer": 0,
                        "source": "enemy",
                        "sprite": "projectile"
                        })
                        for i in range(4):
                             self.game.sparks.append(Spark(self.game.projectiles[-1]["pos"], random.random() - 0.5, 2 + random.random()))        
        # If idle state, begin walking randomly about 45% chance every second
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)         
            
        super().update(tilemap, movement=movement)
        
        # Set animation frames
        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')
            
        # Take 1 damage from collision with player during dash
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.take_damage(self.game.player.dash_damage)

        # Die if no health      
        if self.health <= 0:    
            return self.die()
        return False
           
    # Render enemy guns       
    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)
        if self.flip:
            surf.blit(pygame.transform.flip(self.game.assets['gun'], True, False), (self.rect().centerx - 4 - self.game.assets['gun'].get_width() - offset[0], self.rect().centery - offset[1]))
        else:
            surf.blit(self.game.assets['gun'], (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]))
        # Draw hitbox for debugging
        if self.game.debug_hitboxes:
            pygame.draw.rect(surf, (255, 0, 0), self.rect().move(-offset[0], -offset[1]), 1)

# Oni
class Oni(Enemy):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, e_type='oni')  
        self.health = 5  
        self.shoot_cooldown = 60  # 1s
        self.shoot_timer = 0
        self.invulnerable_timer = 0
        self.invulnerable_duration = 24  # 0.4s
        self.death_noise = 'oni_death'
        self.enraged = False

    # Overriden movement to enrage and move towards the plyer when within 300 in game pixels
    def update(self, tilemap, movement=(0, 0)):
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1

        # Distance to player
        dx = self.game.player.rect().centerx - self.rect().centerx
        distance = abs(dx)
        movement = [0, 0]

        # shoot loop which triggers every second, once player enters firing range of 450
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_cooldown and distance < 450:
            self.shoot()
            self.shoot_timer = 0
            self.enraged = True

        # If less than 300 away, move towards player
        if distance < 300:
            speed = 0.3
            movement[0] = speed if dx > 0 else -speed
            self.flip = dx < 0
            # Do not walk off ledges or into hazard tiles
            if not self.is_safe_ahead(tilemap):
                movement[0] = 0
            # run animation if moving
            self.set_action('run' if movement[0] != 0 else 'idle')
        # else oni is idle
        else:
            self.set_action('idle')
            self.enraged = False

        # Apply movement
        super().update(tilemap, movement=movement)

        # Dash hit detection
        if abs(self.game.player.dashing) >= 50 and self.invulnerable_timer == 0:
            if self.rect().colliderect(self.game.player.rect()):
                self.take_damage(self.game.player.dash_damage)

        # Die if no health      
        if self.health <= 0:    
            return self.die(self.death_noise)
        return False
    
    # Shoot function, adds projectiles, plays sfx and shows sparks
    def shoot(self):
        # Fire two fast shots in both directions
        for direction in [-1, 1]:
            self.game.sfx['shoot'].play()
            self.game.projectiles.append({
            "pos": [self.rect().centerx, self.rect().centery],
            "vel": [direction * 2.5, 0],
            "timer": 0,
            "source": "enemy",
            "sprite": "projectile"
            })
            for _ in range(4):
                self.game.sparks.append(Spark(self.rect().center, random.random() - 0.5 + (math.pi if direction < 0 else 0), 2 + random.random()))

    # Render the Oni
    def render(self, surf, offset=(0, 0)):
        # Draw Oni animations
        img = self.animation.img()
        img = pygame.transform.flip(img, self.flip, False)
        render_pos = (
            self.pos[0] - offset[0] + self.anim_offset[0],
            self.pos[1] - offset[1] + self.anim_offset[1]
        )
        # Flash while invulnerable after taking damage
        if self.invulnerable_timer > 0 and self.invulnerable_timer % 6 < 3:
            flash_img = img.copy()
            flash_img.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_ADD)
            surf.blit(flash_img, render_pos)
        else:
            surf.blit(img, render_pos)

        # Draw hitbox for debugging
        if self.game.debug_hitboxes:
            pygame.draw.rect(surf, (255, 0, 0), self.rect().move(-offset[0], -offset[1]), 1)
            # Draw line of sight (yellow)
            player_pos = self.game.player.rect().center
            if self.enraged:
                pygame.draw.line(
                    surf,
                    (255, 255, 0),
                    (self.rect().centerx - offset[0], self.rect().centery - offset[1]),
                    (player_pos[0] - offset[0], player_pos[1] - offset[1]),
                    1
                )

# Yurei
class Yurei(Enemy):
    def __init__(self, game, pos, size):
        super().__init__(game, pos, size, e_type='yurei')
        self.health = 3
        self.invulnerable_timer = 0
        self.invulnerable_duration = 24   # .4s
        self.death_noise = 'yurei_death'
        self.player_contact_cooldown = 0  # prevents repeated contact triggers
        self.set_action('idle')

    # Moves towards the player when in sight, does not call base physics
    def update(self, tilemap, movement=(0, 0)):        
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1
        if self.player_contact_cooldown > 0:
            self.player_contact_cooldown -= 1

        # Slight vertical bob for when idle
        bob_offset = math.sin(pygame.time.get_ticks() * 0.002) * 0.05

        # Euclidean distance to player
        player_pos = self.game.player.rect().center
        dx = player_pos[0] - self.rect().centerx
        dy = player_pos[1] - self.rect().centery
        distance = math.hypot(dx, dy)

        # Seeks player if in LOS and within 180 "pixels"
        if self.has_line_of_sight(tilemap, player_pos) and distance < 180 and distance > 1e-3:
            speed = 0.5
            dir_x = dx / distance
            dir_y = dy / distance
            self.pos[0] += dir_x * speed
            self.pos[1] += dir_y * speed
            self.set_action('run')
            self.flip = dx < 0
        # Else default to idle and bob in place
        else:
            self.set_action('idle')
            self.pos[1] += bob_offset       

        # Checks for immunity before damaging the player on collision
        if self.rect().colliderect(self.game.player.rect()) and self.player_contact_cooldown == 0:
            self.touch_damage_player()
            self.player_contact_cooldown = 60  # 1 seconds cooldown

        # Dash hit detection — only works if the player has the blessing
        if abs(self.game.player.dashing) >= 50 and self.game.player.has_spirit_blessing:
            if self.rect().colliderect(self.game.player.rect()) and self.invulnerable_timer == 0:
                self.take_damage(self.game.player.dash_damage)

        self.animation.update()

        # Die if no health      
        if self.health <= 0:    
            return self.die(self.death_noise)
        return False
    
    # Checks if player is in line of sight
    def has_line_of_sight(self, tilemap, target_pos):
        yurei_x, yurei_y = self.rect().center
        player_x, player_y = target_pos

        # Checks for solid tiles about every 8 pixels in the furthest direction
        steps = int(max(abs(player_x - yurei_x), abs(player_y - yurei_y)) // 8)
        for i in range(1, steps):
            x = yurei_x + (player_x - yurei_x) * (i / steps)
            y = yurei_y + (player_y - yurei_y) * (i / steps)
            if tilemap.solid_check((x, y)):
                return False
        return True

    # Deals an instance of touch damage to the player, first checking immunities
    def touch_damage_player(self):
        player = self.game.player
        # No damage during dash
        if abs(player.dashing) >= 50:
            return  
        # No damage during smoke bomb
        if player.smoke_active_timer > 0:  
            return  
        # Sushi shield check 
        if player.has_sushi_shield:
            player.has_sushi_shield = False
            self.game.sfx.get('sushi_shield_shatter', self.game.sfx['hit']).play()
            return
        # Otherwise kill the player 
        player.die()

    # Only take damage when player has a spirit blessing
    def take_damage(self, amount, ignore_invuln=False):
        if not self.game.player.has_spirit_blessing:
            return False
        return super().take_damage(amount, ignore_invuln)

    # Consume player's spitrit blessing buff on death
    def die(self, sound=None):
        if self.game.player.has_spirit_blessing:
            self.game.player.has_spirit_blessing = False  
        return super().die(sound)
    
    # Render the yurei to pulse through semi-transparency levels
    def render(self, surf, offset=(0, 0)):
        base_img = self.animation.img()
        # Use scaled sprite image        
        scaled_img = pygame.transform.scale(
            pygame.transform.flip(base_img, self.flip, False),
            (int(base_img.get_width() * 0.75), int(base_img.get_height() * 0.75))
        )
        img = scaled_img.copy()

        # Ghostly alpha pulse effect
        t = pygame.time.get_ticks() * 0.001
        alpha = int(140 + 80 * math.sin(t))
        img.set_alpha(alpha)

        # Sprite position
        render_pos = (
            self.pos[0] - offset[0] + self.anim_offset[0],
            self.pos[1] - offset[1] + self.anim_offset[1]
        )
        # Flash if invulnerable
        if self.invulnerable_timer > 0 and self.invulnerable_timer % 6 < 3:
            flash = img.copy()
            flash.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_ADD)
            surf.blit(flash, render_pos)
        else:
            surf.blit(img, render_pos)

        # For debugging, draws hit boxes and LOS
        if self.game.debug_hitboxes:
            # Draw hitbox (red)
            pygame.draw.rect(surf, (255, 0, 0), self.rect().move(-offset[0], -offset[1]), 1)
            # Draw line of sight (yellow)
            player_pos = self.game.player.rect().center
            if self.has_line_of_sight(self.game.tilemap, player_pos):
                pygame.draw.line(
                    surf,
                    (255, 255, 0),
                    (self.rect().centerx - offset[0], self.rect().centery - offset[1]),
                    (player_pos[0] - offset[0], player_pos[1] - offset[1]),
                    1
                )
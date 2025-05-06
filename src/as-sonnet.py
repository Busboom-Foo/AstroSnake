#!/usr/bin/env python3
import pygame
import sys
import math
import random
from typing import List, Tuple, Optional

# Initialize pygame
pygame.init()

# Game constants
WIDTH = 800
HEIGHT = 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Create the game window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Astersnake")
clock = pygame.time.Clock()

# Player class
class Player:
    def __init__(self):
        self.position = [WIDTH // 2, HEIGHT // 2]
        self.velocity = [0, 0]
        self.acceleration = 0.1
        self.max_velocity = 5
        self.friction = 0.98
        self.angle = 0
        self.rotation_speed = 4
        self.size = 15
        self.color = WHITE
        self.trail = []  # Store positions for the tail
        self.trail_length = 0  # Increases as player collects orbs
        self.trail_spacing = 5  # Store every nth position
        self.frame_counter = 0
        self.shoot_cooldown = 0
        self.invulnerable = 180  # 3 seconds of invulnerability at start
        self.lives = 3
        self.score = 0
        self.tail_color = (0, 200, 200)  # Cyan-ish color for the tail
        
    def update(self):
        # Apply velocity
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        
        # Apply friction
        self.velocity[0] *= self.friction
        self.velocity[1] *= self.friction
        
        # Screen wrapping
        if self.position[0] < 0:
            self.position[0] = WIDTH
        elif self.position[0] > WIDTH:
            self.position[0] = 0
        
        if self.position[1] < 0:
            self.position[1] = HEIGHT
        elif self.position[1] > HEIGHT:
            self.position[1] = 0
        
        # Update tail
        self.frame_counter += 1
        if self.frame_counter % self.trail_spacing == 0:
            self.trail.append(self.position.copy())
            # Limit trail to actual tail length
            while len(self.trail) > self.trail_length:
                self.trail.pop(0)
        
        # Update shoot cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        
        # Update invulnerability
        if self.invulnerable > 0:
            self.invulnerable -= 1
    
    def rotate(self, direction):
        self.angle += direction * self.rotation_speed
        self.angle %= 360  # Keep angle between 0-360
    
    def thrust(self):
        # Apply acceleration in the direction of the ship's angle
        angle_rad = math.radians(self.angle)
        self.velocity[0] += math.cos(angle_rad) * self.acceleration
        self.velocity[1] -= math.sin(angle_rad) * self.acceleration
        
        # Limit maximum velocity
        velocity_magnitude = math.sqrt(self.velocity[0]**2 + self.velocity[1]**2)
        if velocity_magnitude > self.max_velocity:
            scale = self.max_velocity / velocity_magnitude
            self.velocity[0] *= scale
            self.velocity[1] *= scale
    
    def shoot(self, bullets):
        if self.shoot_cooldown <= 0:
            angle_rad = math.radians(self.angle)
            bullet_velocity = [
                math.cos(angle_rad) * 10 + self.velocity[0],
                -math.sin(angle_rad) * 10 + self.velocity[1]
            ]
            bullet_pos = [
                self.position[0] + math.cos(angle_rad) * self.size,
                self.position[1] - math.sin(angle_rad) * self.size
            ]
            bullets.append(Bullet(bullet_pos, bullet_velocity, "player"))
            self.shoot_cooldown = 15  # 1/4 second cooldown between shots
    
    def collect_orb(self):
        self.trail_length += 20  # Increase tail length
        self.score += 50  # Increase score
    
    def check_tail_collision(self):
        # Skip first few segments as they're too close to the player
        # Also skip if player is invulnerable
        if self.invulnerable > 0 or len(self.trail) < 20:
            return False
            
        player_rect = pygame.Rect(
            self.position[0] - self.size/2, 
            self.position[1] - self.size/2,
            self.size, self.size
        )
        
        # Check collision with tail segments (skip recent segments)
        for i, pos in enumerate(self.trail[:-15]):  # Skip last 15 positions
            segment_rect = pygame.Rect(pos[0] - 3, pos[1] - 3, 6, 6)
            if player_rect.colliderect(segment_rect):
                return True
        return False
    
    def draw(self, surface):
        # Draw the tail
        for i, pos in enumerate(self.trail):
            # Gradient color from blue to cyan based on position in tail
            intensity = min(255, int(i / len(self.trail) * 255)) if self.trail else 0
            color = (0, intensity, min(255, intensity + 100))
            pygame.draw.circle(surface, color, (int(pos[0]), int(pos[1])), 3)
        
        # Calculate points for the triangular ship
        angle_rad = math.radians(self.angle)
        points = [
            (
                self.position[0] + math.cos(angle_rad) * self.size,
                self.position[1] - math.sin(angle_rad) * self.size
            ),
            (
                self.position[0] + math.cos(angle_rad + 2.5) * (self.size / 2),
                self.position[1] - math.sin(angle_rad + 2.5) * (self.size / 2)
            ),
            (
                self.position[0] + math.cos(angle_rad - 2.5) * (self.size / 2),
                self.position[1] - math.sin(angle_rad - 2.5) * (self.size / 2)
            )
        ]
        
        # Draw ship (flashing if invulnerable)
        if self.invulnerable == 0 or self.invulnerable % 10 < 5:
            pygame.draw.polygon(surface, self.color, points)
        
        # Draw thrust effect when thrusting
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            thrust_points = [
                (
                    self.position[0] - math.cos(angle_rad) * (self.size / 2),
                    self.position[1] + math.sin(angle_rad) * (self.size / 2)
                ),
                (
                    self.position[0] + math.cos(angle_rad + 3) * (self.size / 3),
                    self.position[1] - math.sin(angle_rad + 3) * (self.size / 3)
                ),
                (
                    self.position[0] + math.cos(angle_rad - 3) * (self.size / 3),
                    self.position[1] - math.sin(angle_rad - 3) * (self.size / 3)
                )
            ]
            pygame.draw.polygon(surface, YELLOW, thrust_points)

# Bullet class
class Bullet:
    def __init__(self, position, velocity, owner, size=3):
        self.position = position
        self.velocity = velocity
        self.owner = owner  # "player" or "enemy"
        self.size = size
        self.life = 60  # Bullets last for 60 frames (1 second)
    
    def update(self):
        # Move bullet
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        
        # Screen wrapping
        if self.position[0] < 0:
            self.position[0] = WIDTH
        elif self.position[0] > WIDTH:
            self.position[0] = 0
        
        if self.position[1] < 0:
            self.position[1] = HEIGHT
        elif self.position[1] > HEIGHT:
            self.position[1] = 0
        
        # Decrease lifetime
        self.life -= 1
    
    def draw(self, surface):
        if self.owner == "player":
            color = GREEN
        else:
            color = RED
        
        pygame.draw.circle(surface, color, 
                          (int(self.position[0]), int(self.position[1])), 
                          self.size)

# Asteroid class
class Asteroid:
    def __init__(self, position=None, velocity=None, size="large"):
        # If no position provided, place randomly on the edge
        if position is None:
            side = random.randint(0, 3)
            if side == 0:  # Top
                position = [random.randint(0, WIDTH), 0]
            elif side == 1:  # Right
                position = [WIDTH, random.randint(0, HEIGHT)]
            elif side == 2:  # Bottom
                position = [random.randint(0, WIDTH), HEIGHT]
            else:  # Left
                position = [0, random.randint(0, HEIGHT)]
        
        self.position = position
        
        # If no velocity provided, generate random velocity
        if velocity is None:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 2)
            velocity = [math.cos(angle) * speed, math.sin(angle) * speed]
        
        self.velocity = velocity
        self.size = size
        
        # Set asteroid radius based on size
        if size == "large":
            self.radius = 40
            self.points = 20
        elif size == "medium":
            self.radius = 20
            self.points = 50
        else:  # small
            self.radius = 10
            self.points = 100
        
        # Generate a random shape for the asteroid
        self.vertices = []
        num_vertices = random.randint(8, 12)
        for i in range(num_vertices):
            angle = math.pi * 2 * i / num_vertices
            distance = self.radius * random.uniform(0.8, 1.2)
            self.vertices.append((math.cos(angle) * distance, math.sin(angle) * distance))
    
    def update(self):
        # Move asteroid
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        
        # Screen wrapping
        if self.position[0] < -self.radius:
            self.position[0] = WIDTH + self.radius
        elif self.position[0] > WIDTH + self.radius:
            self.position[0] = -self.radius
        
        if self.position[1] < -self.radius:
            self.position[1] = HEIGHT + self.radius
        elif self.position[1] > HEIGHT + self.radius:
            self.position[1] = -self.radius
    
    def split(self):
        if self.size == "large":
            new_size = "medium"
        elif self.size == "medium":
            new_size = "small"
        else:
            return []  # Small asteroids don't split
        
        # Create two new asteroids with slightly different directions
        new_asteroids = []
        for _ in range(2):
            angle_offset = random.uniform(-math.pi/4, math.pi/4)
            speed_multiplier = random.uniform(.7, .95)
            
            velocity_magnitude = math.sqrt(self.velocity[0]**2 + self.velocity[1]**2)
            angle = math.atan2(self.velocity[1], self.velocity[0]) + angle_offset
            
            new_velocity = [
                math.cos(angle) * velocity_magnitude * speed_multiplier,
                math.sin(angle) * velocity_magnitude * speed_multiplier
            ]
            
            new_asteroids.append(
                Asteroid(self.position.copy(), new_velocity, new_size)
            )
        
        return new_asteroids
    
    def draw(self, surface):
        # Draw the asteroid
        points = [(self.position[0] + x, self.position[1] + y) for x, y in self.vertices]
        pygame.draw.polygon(surface, WHITE, points, 1)

# Orb (energy) class
class Orb:
    def __init__(self, position=None):
        if position is None:
            # Generate a random position away from the player
            self.position = [
                random.randint(50, WIDTH - 50),
                random.randint(50, HEIGHT - 50)
            ]
        else:
            self.position = position
        
        self.radius = 8
        self.pulse_timer = 0
    
    def update(self):
        self.pulse_timer += 0.1
    
    def draw(self, surface):
        # Pulsating effect
        pulse = abs(math.sin(self.pulse_timer)) * 3
        color_intensity = min(255, 100 + int(pulse * 50))
        
        # Draw outer glow
        for r in range(int(self.radius + pulse), int(self.radius - 2 + pulse), -1):
            alpha = int(150 * (r - self.radius + 2) / (pulse + 2))
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (0, color_intensity, color_intensity, alpha), (r, r), r)
            surface.blit(s, (self.position[0] - r, self.position[1] - r))
        
        # Draw core
        pygame.draw.circle(surface, (200, 255, 255), 
                          (int(self.position[0]), int(self.position[1])), 
                          int(self.radius - 2))

# Enemy Saucer class
class Saucer:
    def __init__(self, difficulty=1):
        # Start from a random edge
        side = random.randint(0, 3)
        if side == 0:  # Top
            position = [random.randint(0, WIDTH), 0]
        elif side == 1:  # Right
            position = [WIDTH, random.randint(0, HEIGHT)]
        elif side == 2:  # Bottom
            position = [random.randint(0, WIDTH), HEIGHT]
        else:  # Left
            position = [0, random.randint(0, HEIGHT)]
        
        self.position = position
        self.angle = random.uniform(0, 2 * math.pi)
        self.speed = 2
        self.velocity = [math.cos(self.angle) * self.speed, math.sin(self.angle) * self.speed]
        self.radius = 15
        self.shoot_cooldown = random.randint(30, 90)  # Time until first shot
        self.difficulty = difficulty  # Higher difficulty = more accurate shots
        self.points = 150
        self.change_dir_timer = random.randint(60, 180)  # 1-3 seconds
    
    def update(self, player_pos, bullets):
        # Move saucer
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        
        # Screen wrapping
        if self.position[0] < 0:
            self.position[0] = WIDTH
        elif self.position[0] > WIDTH:
            self.position[0] = 0
        
        if self.position[1] < 0:
            self.position[1] = HEIGHT
        elif self.position[1] > HEIGHT:
            self.position[1] = 0
        
        # Occasionally change direction
        self.change_dir_timer -= 1
        if self.change_dir_timer <= 0:
            self.angle = random.uniform(0, 2 * math.pi)
            self.velocity = [math.cos(self.angle) * self.speed, math.sin(self.angle) * self.speed]
            self.change_dir_timer = random.randint(60, 180)
        
        # Shoot at player
        self.shoot_cooldown -= 1
        if self.shoot_cooldown <= 0:
            self.shoot(player_pos, bullets)
            self.shoot_cooldown = random.randint(60, 120)  # 1-2 seconds between shots
    
    def shoot(self, player_pos, bullets):
        # Calculate angle to player
        dx = player_pos[0] - self.position[0]
        dy = player_pos[1] - self.position[1]
        angle = math.atan2(dy, dx)
        
        # Add some inaccuracy based on difficulty
        accuracy_factor = 0.2 / self.difficulty  # Higher difficulty = less deviation
        angle += random.uniform(-accuracy_factor, accuracy_factor)
        
        # Create bullet
        velocity = [math.cos(angle) * 5, math.sin(angle) * 5]
        bullets.append(Bullet(self.position.copy(), velocity, "enemy", 2))
    
    def draw(self, surface):
        # Draw the saucer body
        pygame.draw.ellipse(surface, WHITE, 
                           (self.position[0] - self.radius, self.position[1] - self.radius/2,
                            self.radius * 2, self.radius))
        
        # Draw the cabin
        pygame.draw.ellipse(surface, WHITE,
                           (self.position[0] - self.radius/2, self.position[1] - self.radius,
                            self.radius, self.radius/2))

# Game state management
class Game:
    def __init__(self):
        self.state = "menu"  # menu, playing, game_over
        self.player = Player()
        self.bullets = []
        self.asteroids = []
        self.orbs = []
        self.saucers = []
        self.asteroid_spawn_timer = 60*6  # seconds
        self.orb_spawn_timer = 300  # 5 seconds
        self.saucer_spawn_timer = 1200  # 20 seconds
        self.level = 1
        self.high_score = 0
        self.font = pygame.font.SysFont('Arial', 24)
        self.big_font = pygame.font.SysFont('Arial', 48)
    
    def reset(self):
        self.player = Player()
        self.bullets = []
        self.asteroids = []
        self.orbs = []
        self.saucers = []
        self.asteroid_spawn_timer = 180
        self.orb_spawn_timer = 300
        self.saucer_spawn_timer = 1200
        
        # Add initial asteroids
        for _ in range(4):
            self.asteroids.append(Asteroid())
    
    def update(self):
        if self.state == "playing":
            # Update player
            self.player.update()
            
            # Check for tail collision
            if self.player.check_tail_collision():
                self.player_hit()
            
            # Update bullets
            for bullet in self.bullets[:]:
                bullet.update()
                
                # Remove expired bullets
                if bullet.life <= 0:
                    self.bullets.remove(bullet)
            
            # Update asteroids
            for asteroid in self.asteroids[:]:
                asteroid.update()
                
                # Check for collision with player
                if self.player.invulnerable <= 0:
                    dx = asteroid.position[0] - self.player.position[0]
                    dy = asteroid.position[1] - self.player.position[1]
                    distance = math.sqrt(dx**2 + dy**2)
                    if distance < asteroid.radius + self.player.size / 2:
                        self.player_hit()
                        break  # Exit loop as player state has changed
                
                # Check for collision with bullets
                for bullet in self.bullets[:]:
                    if bullet.owner == "player":  # Only player bullets destroy asteroids
                        dx = asteroid.position[0] - bullet.position[0]
                        dy = asteroid.position[1] - bullet.position[1]
                        distance = math.sqrt(dx**2 + dy**2)
                        
                        if distance < asteroid.radius + bullet.size:
                            # Create new asteroids based on size
                            new_asteroids = asteroid.split()
                            self.asteroids.extend(new_asteroids)
                            
                            # Score points
                            self.player.score += asteroid.points
                            
                            # Remove the asteroid and bullet
                            if asteroid in self.asteroids:
                                self.asteroids.remove(asteroid)
                            if bullet in self.bullets:
                                self.bullets.remove(bullet)
                            break
            
            # Update orbs
            for orb in self.orbs[:]:
                orb.update()
                
                # Check for collision with player
                dx = orb.position[0] - self.player.position[0]
                dy = orb.position[1] - self.player.position[1]
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance < orb.radius + self.player.size / 2:
                    self.player.collect_orb()
                    self.orbs.remove(orb)
            
            # Update saucers
            for saucer in self.saucers[:]:
                saucer.update(self.player.position, self.bullets)
                
                # Check for collision with player
                if self.player.invulnerable <= 0:
                    dx = saucer.position[0] - self.player.position[0]
                    dy = saucer.position[1] - self.player.position[1]
                    distance = math.sqrt(dx**2 + dy**2)
                    
                    if distance < saucer.radius + self.player.size / 2:
                        self.player_hit()
                        if saucer in self.saucers:
                            self.saucers.remove(saucer)
                        break
                
                # Check for collision with bullets
                for bullet in self.bullets[:]:
                    if bullet.owner == "player":  # Only player bullets destroy saucers
                        dx = saucer.position[0] - bullet.position[0]
                        dy = saucer.position[1] - bullet.position[1]
                        distance = math.sqrt(dx**2 + dy**2)
                        
                        if distance < saucer.radius + bullet.size:
                            # Score points
                            self.player.score += saucer.points
                            
                            # Remove the saucer and bullet
                            if saucer in self.saucers:
                                self.saucers.remove(saucer)
                            if bullet in self.bullets:
                                self.bullets.remove(bullet)
                            break
                            
                # Check if player is hit by saucer bullets
                for bullet in self.bullets[:]:
                    if bullet.owner == "enemy" and self.player.invulnerable <= 0:
                        dx = self.player.position[0] - bullet.position[0]
                        dy = self.player.position[1] - bullet.position[1]
                        distance = math.sqrt(dx**2 + dy**2)
                        
                        if distance < self.player.size / 2 + bullet.size:
                            self.player_hit()
                            if bullet in self.bullets:
                                self.bullets.remove(bullet)
                            break
                            
            # Spawn new game objects
            self.asteroid_spawn_timer -= 1
            if self.asteroid_spawn_timer <= 0 and len(self.asteroids) < 10 + self.level:
                self.asteroids.append(Asteroid())
                self.asteroid_spawn_timer = 300 - self.level * 10  # Spawn faster as levels increase
            
            self.orb_spawn_timer -= 1
            if self.orb_spawn_timer <= 0 and len(self.orbs) < 5:
                self.orbs.append(Orb())
                self.orb_spawn_timer = 300  # 5 seconds
            
            self.saucer_spawn_timer -= 1
            if self.saucer_spawn_timer <= 0 and len(self.saucers) < 1 + self.level // 3:
                self.saucers.append(Saucer(difficulty=min(5, 1 + self.level // 2)))
                self.saucer_spawn_timer = 1200 - self.level * 50  # Spawn faster as levels increase
                
            # Check for level advancement
            if self.player.score >= self.level * 1000:
                self.level += 1
                
            # Update high score
            if self.player.score > self.high_score:
                self.high_score = self.player.score
    
    def player_hit(self):
        if self.player.invulnerable <= 0:
            self.player.lives -= 1
            if self.player.lives <= 0:
                self.state = "game_over"
            else:
                self.player.invulnerable = 180  # 3 seconds of invulnerability
                self.player.position = [WIDTH // 2, HEIGHT // 2]
                self.player.velocity = [0, 0]
                self.player.trail = []  # Clear the tail on hit
    
    def draw(self, surface):
        # Clear screen
        surface.fill(BLACK)
        
        if self.state == "menu":
            # Draw title
            title_text = self.big_font.render("ASTERSNAKE", True, WHITE)
            surface.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//4))
            
            # Draw instructions
            instructions = [
                "Arrow Keys or WASD to move",
                "SPACE to shoot",
                "Collect orbs to grow your tail",
                "Avoid asteroids, saucers, and your own tail",
                "",
                "Press ENTER to start"
            ]
            
            y_pos = HEIGHT//2
            for line in instructions:
                text = self.font.render(line, True, WHITE)
                surface.blit(text, (WIDTH//2 - text.get_width()//2, y_pos))
                y_pos += 30
        
        elif self.state == "playing":
            # Draw game objects
            for asteroid in self.asteroids:
                asteroid.draw(surface)
            
            for orb in self.orbs:
                orb.draw(surface)
                
            for bullet in self.bullets:
                bullet.draw(surface)
            
            for saucer in self.saucers:
                saucer.draw(surface)
            
            self.player.draw(surface)
            
            # Draw HUD
            # Score
            score_text = self.font.render(f"Score: {self.player.score}", True, WHITE)
            surface.blit(score_text, (10, 10))
            
            # High score
            high_score_text = self.font.render(f"High Score: {self.high_score}", True, WHITE)
            surface.blit(high_score_text, (WIDTH - high_score_text.get_width() - 10, 10))
            
            # Lives
            lives_text = self.font.render(f"Lives: {self.player.lives}", True, WHITE)
            surface.blit(lives_text, (10, 40))
            
            # Level
            level_text = self.font.render(f"Level: {self.level}", True, WHITE)
            surface.blit(level_text, (WIDTH - level_text.get_width() - 10, 40))
        
        elif self.state == "game_over":
            # Draw game over screen
            game_over_text = self.big_font.render("GAME OVER", True, RED)
            surface.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//3))
            
            score_text = self.font.render(f"Score: {self.player.score}", True, WHITE)
            surface.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
            
            high_score_text = self.font.render(f"High Score: {self.high_score}", True, WHITE)
            surface.blit(high_score_text, (WIDTH//2 - high_score_text.get_width()//2, HEIGHT//2 + 30))
            
            restart_text = self.font.render("Press ENTER to restart", True, WHITE)
            surface.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 80))

# Main game loop
def main():
    game = Game()
    running = True
    
    while running:
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if game.state == "menu" or game.state == "game_over":
                        game.state = "playing"
                        game.reset()
                elif event.key == pygame.K_ESCAPE:
                    if game.state == "playing":
                        game.state = "menu"
        
        # Process input
        if game.state == "playing":
            keys = pygame.key.get_pressed()
            
            # Rotation
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                game.player.rotate(1)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                game.player.rotate(-1)
            
            # Thrust
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                game.player.thrust()
            
            # Shoot
            if keys[pygame.K_SPACE]:
                game.player.shoot(game.bullets)
        
        # Update game
        game.update()
        
        # Draw everything
        game.draw(screen)
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
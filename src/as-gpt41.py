import pygame
import math
import random

# Game constants
WIDTH, HEIGHT = 800, 600
FPS = 60
SHIP_SIZE = 30
BULLET_SPEED = 8
ASTEROID_SIZES = {'large': 60, 'medium': 40, 'small': 20}
ASTEROID_SPEEDS = {'large': 2, 'medium': 3, 'small': 4}
ORB_RADIUS = 10
SAUCER_SIZE = 40
TAIL_SEGMENT_LENGTH = 12
TAIL_MAX_POINTS = 500

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Astersnake')
clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 24)

# Helper functions
def wrap_position(pos):
    x, y = pos
    return x % WIDTH, y % HEIGHT

def angle_to_vector(angle):
    rad = math.radians(angle)
    return math.cos(rad), -math.sin(rad)

def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

# Classes
class Ship:
    def __init__(self):
        self.pos = (WIDTH // 2, HEIGHT // 2)
        self.angle = 0
        self.vel = [0, 0]
        self.tail = []
        self.tail_length = 0
        self.alive = True
        self.cooldown = 0

    def update(self, keys):
        if keys[pygame.K_LEFT]:
            self.angle = (self.angle + 4) % 360
        if keys[pygame.K_RIGHT]:
            self.angle = (self.angle - 4) % 360
        if keys[pygame.K_UP]:
            dx, dy = angle_to_vector(self.angle)
            self.vel[0] += dx * 0.2
            self.vel[1] += dy * 0.2
        self.vel[0] *= 0.99
        self.vel[1] *= 0.99
        self.pos = wrap_position((self.pos[0] + self.vel[0], self.pos[1] + self.vel[1]))
        # Tail follows ship
        self.tail.insert(0, self.pos)
        if len(self.tail) > self.tail_length:
            self.tail.pop()
        if len(self.tail) > TAIL_MAX_POINTS:
            self.tail = self.tail[:TAIL_MAX_POINTS]
        if self.cooldown > 0:
            self.cooldown -= 1

    def grow_tail(self):
        self.tail_length += TAIL_SEGMENT_LENGTH

    def draw(self, surf):
        # Draw tail
        if len(self.tail) > 1:
            pygame.draw.lines(surf, (0, 255, 0), False, self.tail, 4)
        # Draw ship
        dx, dy = angle_to_vector(self.angle)
        perp = (-dy, dx)
        points = [
            (self.pos[0] + dx * SHIP_SIZE, self.pos[1] + dy * SHIP_SIZE),
            (self.pos[0] - dx * SHIP_SIZE * 0.6 + perp[0] * SHIP_SIZE * 0.5, self.pos[1] - dy * SHIP_SIZE * 0.6 + perp[1] * SHIP_SIZE * 0.5),
            (self.pos[0] - dx * SHIP_SIZE * 0.6 - perp[0] * SHIP_SIZE * 0.5, self.pos[1] - dy * SHIP_SIZE * 0.6 - perp[1] * SHIP_SIZE * 0.5)
        ]
        pygame.draw.polygon(surf, (255, 255, 255), points)

    def shoot(self):
        if self.cooldown == 0:
            dx, dy = angle_to_vector(self.angle)
            bullet_pos = (self.pos[0] + dx * SHIP_SIZE, self.pos[1] + dy * SHIP_SIZE)
            bullet_vel = (self.vel[0] + dx * BULLET_SPEED, self.vel[1] + dy * BULLET_SPEED)
            self.cooldown = 10
            return Bullet(bullet_pos, bullet_vel)
        return None

    def check_tail_collision(self):
        # Ignore first few tail points (ship body)
        for pt in self.tail[SHIP_SIZE*2//TAIL_SEGMENT_LENGTH:]:
            if distance(self.pos, pt) < TAIL_SEGMENT_LENGTH:
                return True
        return False

class Bullet:
    def __init__(self, pos, vel):
        self.pos = pos
        self.vel = vel
        self.lifetime = 60

    def update(self):
        self.pos = wrap_position((self.pos[0] + self.vel[0], self.pos[1] + self.vel[1]))
        self.lifetime -= 1

    def draw(self, surf):
        pygame.draw.circle(surf, (255, 255, 0), (int(self.pos[0]), int(self.pos[1])), 3)

    def alive(self):
        return self.lifetime > 0

class Asteroid:
    def __init__(self, pos, size):
        self.pos = pos
        self.size = size
        self.radius = ASTEROID_SIZES[size] // 2
        angle = random.uniform(0, 360)
        speed = ASTEROID_SPEEDS[size]
        dx, dy = angle_to_vector(angle)
        self.vel = (dx * speed, dy * speed)
        self.points = self.generate_shape()

    def generate_shape(self):
        points = []
        for i in range(8):
            ang = math.radians(i * 45)
            r = self.radius * random.uniform(0.8, 1.2)
            points.append((math.cos(ang) * r, math.sin(ang) * r))
        return points

    def update(self):
        self.pos = wrap_position((self.pos[0] + self.vel[0], self.pos[1] + self.vel[1]))

    def draw(self, surf):
        pts = [(self.pos[0] + x, self.pos[1] + y) for (x, y) in self.points]
        pygame.draw.polygon(surf, (150, 150, 150), pts, 2)

    def split(self):
        if self.size == 'large':
            return [Asteroid(self.pos, 'medium'), Asteroid(self.pos, 'medium')]
        elif self.size == 'medium':
            return [Asteroid(self.pos, 'small'), Asteroid(self.pos, 'small')]
        else:
            return []

class EnergyOrb:
    def __init__(self):
        self.pos = (random.randint(ORB_RADIUS, WIDTH-ORB_RADIUS), random.randint(ORB_RADIUS, HEIGHT-ORB_RADIUS))

    def draw(self, surf):
        pygame.draw.circle(surf, (0, 200, 255), (int(self.pos[0]), int(self.pos[1])), ORB_RADIUS)

class Saucershot:
    def __init__(self, pos, vel):
        self.pos = pos
        self.vel = vel
        self.lifetime = 90

    def update(self):
        self.pos = wrap_position((self.pos[0] + self.vel[0], self.pos[1] + self.vel[1]))
        self.lifetime -= 1

    def draw(self, surf):
        pygame.draw.circle(surf, (255, 0, 0), (int(self.pos[0]), int(self.pos[1])), 3)

    def alive(self):
        return self.lifetime > 0

class Saucer:
    def __init__(self):
        self.pos = (random.choice([0, WIDTH]), random.randint(0, HEIGHT))
        self.vel = (random.choice([-3, 3]), random.uniform(-1, 1))
        self.cooldown = 0
        self.radius = SAUCER_SIZE // 2

    def update(self):
        self.pos = wrap_position((self.pos[0] + self.vel[0], self.pos[1] + self.vel[1]))
        if self.cooldown > 0:
            self.cooldown -= 1

    def draw(self, surf):
        pygame.draw.rect(surf, (255, 0, 255), (self.pos[0] - self.radius, self.pos[1] - self.radius//2, SAUCER_SIZE, SAUCER_SIZE//2))
        pygame.draw.circle(surf, (255, 0, 255), (int(self.pos[0]), int(self.pos[1])), self.radius//2)

    def shoot(self, target):
        if self.cooldown == 0:
            dx = target[0] - self.pos[0]
            dy = target[1] - self.pos[1]
            dist = math.hypot(dx, dy)
            if dist == 0:
                dist = 1
            vel = (dx/dist*6, dy/dist*6)
            self.cooldown = 40
            return Saucershot(self.pos, vel)
        return None

# Game loop and logic
def main():
    ship = Ship()
    bullets = []
    asteroids = [Asteroid((random.randint(0, WIDTH), random.randint(0, HEIGHT)), 'large') for _ in range(4)]
    orbs = [EnergyOrb()]
    saucers = []
    saucershots = []
    score = 0
    saucer_timer = 0
    running = True
    game_over = False

    while running:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if not game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bullet = ship.shoot()
                    if bullet:
                        bullets.append(bullet)
            if game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    main()
                    return

        if not game_over:
            ship.update(keys)
            for bullet in bullets:
                bullet.update()
            bullets = [b for b in bullets if b.alive()]
            for asteroid in asteroids:
                asteroid.update()
            for orb in orbs:
                pass
            for saucer in saucers:
                saucer.update()
                if random.random() < 0.02:
                    shot = saucer.shoot(ship.pos)
                    if shot:
                        saucershots.append(shot)
            for shot in saucershots:
                shot.update()
            saucershots = [s for s in saucershots if s.alive()]

            # Collisions
            # Ship with asteroids
            for asteroid in asteroids:
                if distance(ship.pos, asteroid.pos) < asteroid.radius + SHIP_SIZE//2:
                    game_over = True
            # Ship with saucers
            for saucer in saucers:
                if distance(ship.pos, saucer.pos) < saucer.radius + SHIP_SIZE//2:
                    game_over = True
            # Ship with saucer shots
            for shot in saucershots:
                if distance(ship.pos, shot.pos) < SHIP_SIZE//2 + 3:
                    game_over = True
            # Ship with tail
            if ship.check_tail_collision():
                game_over = True
            # Ship with orbs
            for orb in orbs[:]:
                if distance(ship.pos, orb.pos) < SHIP_SIZE//2 + ORB_RADIUS:
                    orbs.remove(orb)
                    ship.grow_tail()
                    score += 10
                    orbs.append(EnergyOrb())
            # Bullets with asteroids
            for bullet in bullets[:]:
                for asteroid in asteroids[:]:
                    if distance(bullet.pos, asteroid.pos) < asteroid.radius:
                        bullets.remove(bullet)
                        asteroids.remove(asteroid)
                        new_asteroids = asteroid.split()
                        asteroids.extend(new_asteroids)
                        score += 20 if asteroid.size == 'small' else 10
                        break
            # Bullets with saucers
            for bullet in bullets[:]:
                for saucer in saucers[:]:
                    if distance(bullet.pos, saucer.pos) < saucer.radius:
                        bullets.remove(bullet)
                        saucers.remove(saucer)
                        score += 50
                        break
            # Bullets with saucer shots (cancel out)
            for bullet in bullets[:]:
                for shot in saucershots[:]:
                    if distance(bullet.pos, shot.pos) < 6:
                        bullets.remove(bullet)
                        saucershots.remove(shot)
                        break

            # Spawn saucers
            saucer_timer += 1
            if saucer_timer > 600:
                saucers.append(Saucer())
                saucer_timer = 0
            # Keep orbs on field
            if len(orbs) < 1:
                orbs.append(EnergyOrb())
            # Keep asteroids on field
            if len(asteroids) < 3:
                asteroids.append(Asteroid((random.randint(0, WIDTH), random.randint(0, HEIGHT)), random.choice(['large', 'medium'])))

        # Drawing
        screen.fill((10, 10, 30))
        for orb in orbs:
            orb.draw(screen)
        for asteroid in asteroids:
            asteroid.draw(screen)
        for bullet in bullets:
            bullet.draw(screen)
        for saucer in saucers:
            saucer.draw(screen)
        for shot in saucershots:
            shot.draw(screen)
        ship.draw(screen)
        score_text = font.render(f'Score: {score}', True, (255,255,255))
        screen.blit(score_text, (10, 10))
        if game_over:
            over_text = font.render('GAME OVER! Press R to restart.', True, (255, 0, 0))
            screen.blit(over_text, (WIDTH//2 - over_text.get_width()//2, HEIGHT//2))
        pygame.display.flip()

    pygame.quit()

if __name__ == '__main__':
    main()

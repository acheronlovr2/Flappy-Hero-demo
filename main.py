import pygame
import random
import sys
import time
import math

pygame.init()

# === SCREEN ===
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
pygame.display.set_caption("Flappy Hero")

clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Arial", WIDTH // 12)
SMALL_FONT = pygame.font.SysFont("Arial", WIDTH // 28)
CARD_FONT = pygame.font.SysFont("Arial", WIDTH // 45)

# === COLORS ===
SKY_TOP = (70, 130, 220)
SKY_BOT = (175, 215, 245)
GREEN = (30, 180, 30)
DARK_GREEN = (15, 110, 15)
LIGHT_GREEN = (90, 220, 90)
RED = (255, 50, 50)
WHITE = (255, 255, 255)
PURPLE = (180, 0, 180)
GRAY = (200, 200, 200)
DARK_GRAY = (40, 40, 50)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
DARK_BLUE = (10, 15, 40)
GOLD = (212, 175, 55)
BLACK = (0, 0, 0)
CYAN = (0, 255, 255)
CRIMSON = (150, 0, 30)

# === PRE-RENDER GRADIENT BACKGROUND (FIXES LAG) ===
background_surface = pygame.Surface((WIDTH, HEIGHT))
for i in range(HEIGHT):
    color = (
        int(SKY_TOP[0] + (SKY_BOT[0] - SKY_TOP[0]) * (i / HEIGHT)),
        int(SKY_TOP[1] + (SKY_BOT[1] - SKY_TOP[1]) * (i / HEIGHT)),
        int(SKY_TOP[2] + (SKY_BOT[2] - SKY_TOP[2]) * (i / HEIGHT))
    )
    pygame.draw.line(background_surface, color, (0, i), (WIDTH, i))

# Pre-draw static background features once onto the surface
pygame.draw.circle(background_surface, (255, 250, 200), (WIDTH - 150, 100), 60)
pygame.draw.polygon(background_surface, (100, 160, 200), [(0, HEIGHT), (WIDTH // 4, HEIGHT - 180), (WIDTH // 2, HEIGHT)])
pygame.draw.polygon(background_surface, (120, 180, 220), [(WIDTH // 3, HEIGHT), (WIDTH * 0.7, HEIGHT - 220), (WIDTH, HEIGHT)])

# === PLAYER ===
base_bird_size = WIDTH // 12
bird_size = base_bird_size
player_img = pygame.Surface((bird_size, bird_size))
player_img.fill(WHITE)
gravity = 0.5
flap_strength = -8
bird_x = WIDTH // 8
bird_y = HEIGHT // 2
velocity = 0
player_health = 3
max_health = 3
invincible = False
last_hit = 0

# === GAME STATE ===
main_menu = True
countdown_active = False
countdown_start_time = 0
COUNTDOWN_DURATION = 3

# === PIPE ===
pipe_width = WIDTH // 10
pipe_gap_multiplier = 1.0
pipe_gap = int((HEIGHT // 4) * pipe_gap_multiplier)
pipe_speed = WIDTH // 90
pipe_x = WIDTH
pipe_height = random.randint(HEIGHT // 6, HEIGHT // 2)

# === BACKGROUND CLOUDS ===
bg_clouds = [{"x": random.randint(0, WIDTH), "y": random.randint(30, HEIGHT // 3), "speed": random.uniform(0.3, 0.8), "size": random.randint(40, 70)} for _ in range(5)]

# === BOSS ===
boss_active = False
boss_number = 0
boss_health = 0
boss_max_health = 0
boss_intro = False
boss_intro_time = 0
boss_size = base_bird_size * 3
boss_right_margin = 20
boss_x_pos = WIDTH - boss_size - boss_right_margin
boss_rect = pygame.Rect(boss_x_pos, HEIGHT // 2 - boss_size // 2, boss_size, boss_size)
boss_speed = HEIGHT // 100
boss_direction = 1
boss_spike_timer = 0
boss_phase_timer = 0
spikes = []
player_bullets = []
player_bullet_speed = WIDTH // 50
can_shoot = False
boss_dying = False
boss_death_time = 0

# === BUFF SYSTEM VARIABLES ===
buff_selection_active = False
buff_cards_offered = []
boss_health_modifier = 1.0
has_no_pipes_buff = False
no_pipes_active = False
no_pipes_timer = 0
no_pipes_check_timer = 0
no_pipes_duration = 10

heal_per_min_active = False
heal_per_min_timer = 0

BUFF_POOL = [
    {"id": "max_hp", "title": "Increase Max Health", "desc": "+1 Max Health & heals 1 HP."},
    {"id": "less_boss_hp", "title": "Less Boss Health", "desc": "Next boss health -10%."},
    {"id": "smaller_bird", "title": "Smaller Bird", "desc": "Shrinks hero size by 10%."},
    {"id": "heal_over_time", "title": "Heal Every Minute", "desc": "Restores 1 HP every 60s (2% for 2 HP)."},
    {"id": "wider_gaps", "title": "Wider Pipe Gaps", "desc": "Pipe gaps become 5% wider."},
    {"id": "no_pipes", "title": "No Pipes", "desc": "5% chance for pipes to vanish 10s every 25s."}
]

# === ANIMATED CUTSCENE VARIABLES ===
cutscene = False
cutscene_start = 0
cutscene_duration = 5
stars = [{"x": random.randint(0, WIDTH), "y": random.randint(0, HEIGHT), "speed": random.uniform(1, 3)} for _ in range(80)]
clouds = [{"x": random.randint(0, WIDTH), "y": random.randint(50, HEIGHT // 2), "speed": random.uniform(0.5, 1.5), "size": random.randint(40, 80)} for _ in range(6)]

score = 0
win = False
game_over = False
start_button = pygame.Rect(0, 0, 0, 0)
restart_button = pygame.Rect(0, 0, 0, 0)
quit_button = pygame.Rect(0, 0, 0, 0)

boss_names = ["Spike Brute", "Rapid Raptor", "Screech Fiend", "Wave Leaper", "Hellclaw", "Void Eater"]
BOSS_SCORES = [25, 50, 75, 100, 125, 150]


# === RESET FUNCTION ===
def reset_game():
    global bird_x, bird_y, velocity, pipe_x, pipe_height, score, game_over, win
    global boss_active, boss_number, boss_health, boss_max_health, boss_rect
    global spikes, player_bullets, can_shoot, player_health, max_health, invincible, last_hit
    global cutscene, boss_dying, boss_intro, countdown_active, countdown_start_time
    global bird_size, player_img, pipe_gap_multiplier, pipe_gap, boss_health_modifier
    global buff_selection_active, has_no_pipes_buff, no_pipes_active, heal_per_min_active, main_menu

    bird_size = base_bird_size
    player_img = pygame.Surface((bird_size, bird_size))
    player_img.fill(WHITE)
    bird_x = WIDTH // 8
    bird_y = HEIGHT // 2
    velocity = 0
    pipe_gap_multiplier = 1.0
    pipe_gap = int((HEIGHT // 4) * pipe_gap_multiplier)
    pipe_x = WIDTH
    pipe_height = random.randint(HEIGHT // 6, HEIGHT // 2)
    score = 0
    game_over = False
    win = False
    boss_active = False
    boss_number = 0
    boss_health = 0
    boss_max_health = 0
    boss_health_modifier = 1.0
    boss_rect.x = boss_x_pos
    boss_rect.y = HEIGHT // 2 - boss_size // 2
    spikes.clear()
    player_bullets.clear()
    can_shoot = False
    max_health = 3
    player_health = max_health
    invincible = False
    last_hit = 0
    cutscene = False
    boss_dying = False
    boss_intro = False
    
    buff_selection_active = False
    has_no_pipes_buff = False
    no_pipes_active = False
    heal_per_min_active = False

    main_menu = True
    countdown_active = False


def update_bird_size(new_size):
    global bird_size, player_img
    bird_size = max(15, int(new_size))
    player_img = pygame.Surface((bird_size, bird_size))
    player_img.fill(WHITE)


# === BUFF SELECTION LOGIC ===
def trigger_buff_selection():
    global buff_selection_active, buff_cards_offered
    buff_selection_active = True
    
    available = [b for b in BUFF_POOL if not (b["id"] == "no_pipes" and has_no_pipes_buff)]
    count = min(3, len(available))
    buff_cards_offered = random.sample(available, count)


def apply_buff(buff_id):
    global max_health, player_health, boss_health_modifier, pipe_gap_multiplier, pipe_gap
    global has_no_pipes_buff, heal_per_min_active, heal_per_min_timer, no_pipes_check_timer

    if buff_id == "max_hp":
        max_health += 1
        player_health = min(max_health, player_health + 1)
    elif buff_id == "less_boss_hp":
        boss_health_modifier *= 0.90
    elif buff_id == "smaller_bird":
        update_bird_size(bird_size * 0.90)
    elif buff_id == "heal_over_time":
        heal_per_min_active = True
        heal_per_min_timer = time.time()
    elif buff_id == "wider_gaps":
        pipe_gap_multiplier += 0.05
        pipe_gap = int((HEIGHT // 4) * pipe_gap_multiplier)
    elif buff_id == "no_pipes":
        has_no_pipes_buff = True
        no_pipes_check_timer = time.time()


# === DRAW HELPERS ===
def draw_button(text, x, y, w, h):
    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, GRAY, rect, border_radius=10)
    pygame.draw.rect(screen, WHITE, rect, 3, border_radius=10)
    label = SMALL_FONT.render(text, True, RED)
    screen.blit(label, (x + (w - label.get_width()) // 2, y + (h - label.get_height()) // 2))
    return rect


def draw_health():
    for i in range(max_health):
        color = GREEN if i < player_health else RED
        pygame.draw.rect(screen, color, (20 + i * 30, 20, 20, 20))
    pygame.draw.rect(screen, WHITE, (15, 15, max_health * 30, 30), 2)


def draw_background():
    # Fast blit of pre-rendered gradient background
    screen.blit(background_surface, (0, 0))

    # Moving Clouds
    for cloud in bg_clouds:
        cloud["x"] -= cloud["speed"]
        if cloud["x"] < -cloud["size"] * 2:
            cloud["x"] = WIDTH + cloud["size"]
            cloud["y"] = random.randint(30, HEIGHT // 3)
        pygame.draw.circle(screen, (255, 255, 255, 200), (int(cloud["x"]), int(cloud["y"])), cloud["size"])
        pygame.draw.circle(screen, (255, 255, 255, 200), (int(cloud["x"] + cloud["size"] * 0.6), int(cloud["y"])), int(cloud["size"] * 0.8))


def draw_detailed_pipe(rect, is_top=True):
    # Main Pipe Body
    pygame.draw.rect(screen, GREEN, rect)
    pygame.draw.rect(screen, DARK_GREEN, rect, 4)

    # Highlights & Shadows
    pygame.draw.rect(screen, LIGHT_GREEN, (rect.x + 8, rect.y, rect.width // 4, rect.height))
    pygame.draw.rect(screen, DARK_GREEN, (rect.x + rect.width - 15, rect.y, 10, rect.height))

    # Pipe Rim
    rim_h = 24
    rim_y = rect.bottom - rim_h if is_top else rect.top
    rim_rect = pygame.Rect(rect.x - 6, rim_y, rect.width + 12, rim_h)
    
    pygame.draw.rect(screen, GREEN, rim_rect, border_radius=4)
    pygame.draw.rect(screen, DARK_GREEN, rim_rect, 3, border_radius=4)
    pygame.draw.rect(screen, LIGHT_GREEN, (rim_rect.x + 8, rim_rect.y + 2, rim_rect.width // 4, rim_rect.height - 4))


# === UNIQUE BOSS DRAWING & VISUALS ===
def draw_boss(b_num, rect, t):
    cx, cy = rect.centerx, rect.centery
    w, h = rect.width, rect.height

    if b_num == 1:
        pygame.draw.rect(screen, CRIMSON, rect, border_radius=15)
        pygame.draw.rect(screen, BLACK, rect, 4, border_radius=15)
        eye_x = cx - 10 + int(math.sin(t * 3) * 10)
        pygame.draw.circle(screen, WHITE, (eye_x, cy - 10), 22)
        pygame.draw.circle(screen, RED, (eye_x, cy - 10), 10)
        pygame.draw.circle(screen, BLACK, (eye_x, cy - 10), 4)
        pygame.draw.polygon(screen, BLACK, [(cx - 20, cy + 25), (cx, cy + 15), (cx + 20, cy + 25), (cx, cy + 35)])

    elif b_num == 2:
        points = [(cx + w // 2, cy), (cx - w // 2, cy - h // 2), (cx - w // 4, cy), (cx - w // 2, cy + h // 2)]
        pygame.draw.polygon(screen, ORANGE, points)
        pygame.draw.polygon(screen, RED, points, 3)
        pygame.draw.line(screen, YELLOW, (cx - 10, cy - 15), (cx + 10, cy - 5), 4)
        pygame.draw.line(screen, YELLOW, (cx - 10, cy + 15), (cx + 10, cy + 5), 4)

    elif b_num == 3:
        pts = [(cx, cy - h // 2), (cx + w // 2, cy), (cx, cy + h // 2), (cx - w // 2, cy)]
        pygame.draw.polygon(screen, PURPLE, pts)
        pygame.draw.polygon(screen, WHITE, pts, 3)
        pygame.draw.circle(screen, BLACK, (cx - 15, cy - 15), 10)
        pygame.draw.circle(screen, BLACK, (cx + 15, cy - 15), 10)
        mouth_h = int(15 + math.sin(t * 10) * 8)
        pygame.draw.ellipse(screen, BLACK, (cx - 12, cy + 5, 24, mouth_h))

    elif b_num == 4:
        pygame.draw.ellipse(screen, CYAN, rect)
        pygame.draw.ellipse(screen, BLUE, rect, 4)
        pygame.draw.circle(screen, WHITE, (cx - 20, cy - 15), 12)
        pygame.draw.circle(screen, WHITE, (cx + 20, cy - 15), 12)
        pygame.draw.circle(screen, BLACK, (cx - 20, cy - 15), 5)
        pygame.draw.circle(screen, BLACK, (cx + 20, cy - 15), 5)
        pygame.draw.arc(screen, BLACK, (cx - 25, cy, 50, 20), math.pi, 0, 3)

    elif b_num == 5:
        pygame.draw.rect(screen, DARK_GRAY, rect, border_radius=8)
        pygame.draw.rect(screen, RED, rect, 3, border_radius=8)
        pygame.draw.ellipse(screen, YELLOW, (cx - 25, cy - 20, 18, 8))
        pygame.draw.ellipse(screen, YELLOW, (cx + 7, cy - 20, 18, 8))
        pygame.draw.line(screen, RED, (cx - 16, cy - 20), (cx - 16, cy - 12), 3)
        pygame.draw.line(screen, RED, (cx + 16, cy - 20), (cx + 16, cy - 12), 3)
        pygame.draw.polygon(screen, RED, [(cx - 30, cy + 20), (cx - 45, cy + 35), (cx - 20, cy + 30)])
        pygame.draw.polygon(screen, RED, [(cx + 30, cy + 20), (cx + 45, cy + 35), (cx + 20, cy + 30)])

    elif b_num == 6:
        pulse = int(math.sin(t * 5) * 8)
        pygame.draw.circle(screen, PURPLE, (cx, cy), w // 2 + pulse)
        pygame.draw.circle(screen, BLACK, (cx, cy), w // 2 - 5)
        pygame.draw.circle(screen, RED, (cx, cy), 15)
        pygame.draw.circle(screen, YELLOW, (cx, cy), 6)


# === UNIQUE BOSS MOVEMENTS & ATTACKS ===
def update_boss_behavior(b_num, rect, t, now):
    global boss_direction, boss_spike_timer, boss_phase_timer, boss_rect

    if b_num == 1:
        rect.y += boss_direction * boss_speed
        if rect.top <= 0 or rect.bottom >= HEIGHT:
            boss_direction *= -1

    elif b_num == 2:
        rect.y = int(HEIGHT // 2 + math.sin(t * 4) * (HEIGHT // 2 - boss_size))

    elif b_num == 3:
        rect.y += boss_direction * (boss_speed + 2)
        rect.x = boss_x_pos + int(math.sin(t * 8) * 30)
        if rect.top <= 20 or rect.bottom >= HEIGHT - 20:
            boss_direction *= -1

    elif b_num == 4:
        rect.y += boss_direction * (boss_speed + 4)
        if rect.top <= 50 or rect.bottom >= HEIGHT - 50:
            boss_direction *= -1

    elif b_num == 5:
        if now - boss_phase_timer > 2.0:
            rect.y = random.randint(50, HEIGHT - boss_size - 50)
            boss_phase_timer = now

    elif b_num == 6:
        target_y = HEIGHT // 2 - boss_size // 2 + int(math.sin(t * 2) * 100)
        rect.y += (target_y - rect.y) * 0.05

    rect.y = max(0, min(HEIGHT - boss_size, rect.y))

    if now - boss_spike_timer > max(0.6, 1.8 - b_num * 0.15):
        if b_num == 1:
            for vy in [-4, 0, 4]:
                spikes.append({"rect": pygame.Rect(rect.x, rect.centery, 22, 22), "vx": -8, "vy": vy, "color": ORANGE})

        elif b_num == 2:
            spikes.append({"rect": pygame.Rect(rect.x, rect.centery, 16, 12), "vx": -16, "vy": 0, "color": RED})

        elif b_num == 3:
            for angle in range(-2, 3):
                spikes.append({"rect": pygame.Rect(rect.x, rect.centery, 18, 18), "vx": -7, "vy": angle * 3, "color": PURPLE})

        elif b_num == 4:
            spikes.append({"rect": pygame.Rect(rect.x, rect.centery, 20, 20), "vx": -7, "vy": -6, "gravity": 0.3, "color": CYAN})

        elif b_num == 5:
            spikes.append({"rect": pygame.Rect(rect.x, rect.top + 20, 25, 12), "vx": -12, "vy": -1, "color": RED})
            spikes.append({"rect": pygame.Rect(rect.x, rect.bottom - 20, 25, 12), "vx": -12, "vy": 1, "color": RED})

        elif b_num == 6:
            for vy in [-6, -3, 0, 3, 6]:
                spikes.append({"rect": pygame.Rect(rect.x, rect.centery, 20, 20), "vx": -9, "vy": vy, "color": GOLD})

        boss_spike_timer = now


# === GAME START ===
reset_game()
running = True

while running:
    clock.tick(60)
    now = time.time()

    # === EVENTS ===
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # MAIN MENU INTERACTION
        if main_menu and event.type == pygame.MOUSEBUTTONDOWN:
            if start_button.collidepoint(event.pos):
                main_menu = False
                countdown_active = True
                countdown_start_time = time.time()
            elif quit_button.collidepoint(event.pos):
                pygame.quit()
                sys.exit()

        # BUFF SELECTION CLICK EVENT
        if buff_selection_active and event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            card_w, card_h = WIDTH // 4, HEIGHT // 2
            start_x = (WIDTH - (len(buff_cards_offered) * card_w + (len(buff_cards_offered) - 1) * 30)) // 2
            card_y = HEIGHT // 2 - card_h // 2

            for i, buff in enumerate(buff_cards_offered):
                card_x = start_x + i * (card_w + 30)
                card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
                if card_rect.collidepoint(mouse_pos):
                    apply_buff(buff["id"])
                    buff_selection_active = False
                    countdown_active = True
                    countdown_start_time = time.time()
                    break

        if not main_menu and not game_over and not win and not boss_intro and not cutscene and not countdown_active and not buff_selection_active and event.type == pygame.MOUSEBUTTONDOWN:
            velocity = flap_strength
            if can_shoot and boss_active:
                bullet = pygame.Rect(bird_x + bird_size, bird_y + bird_size // 2 - 5, 10, 10)
                player_bullets.append(bullet)

        if (game_over or win) and event.type == pygame.MOUSEBUTTONDOWN:
            if restart_button.collidepoint(pygame.mouse.get_pos()):
                reset_game()
            elif quit_button.collidepoint(pygame.mouse.get_pos()):
                pygame.quit()
                sys.exit()

    # === MAIN MENU UI ===
    if main_menu:
        draw_background()
        title = FONT.render("FLAPPY HERO", True, GOLD)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 5))

        # Flapping Hero Preview
        bird_y = HEIGHT // 2 - 50 + int(math.sin(now * 5) * 15)
        screen.blit(player_img, (WIDTH // 2 - bird_size // 2, bird_y))

        start_button = draw_button("Start Game", WIDTH // 2 - 150, HEIGHT // 2 + 50, 300, 60)
        quit_button = draw_button("Quit", WIDTH // 2 - 150, HEIGHT // 2 + 130, 300, 60)

        pygame.display.update()
        continue

    # === PASSIVE BUFF UPDATES ===
    if not game_over and not win and not countdown_active and not buff_selection_active:
        if heal_per_min_active and now - heal_per_min_timer >= 60:
            heal_per_min_timer = now
            if player_health < max_health:
                heal_amount = 2 if random.random() < 0.02 else 1
                player_health = min(max_health, player_health + heal_amount)

        if has_no_pipes_buff:
            if no_pipes_active:
                if now - no_pipes_timer >= no_pipes_duration:
                    no_pipes_active = False
            elif now - no_pipes_check_timer >= 25:
                no_pipes_check_timer = now
                if random.random() < 0.05:
                    no_pipes_active = True
                    no_pipes_timer = now

    # === ANIMATED CUTSCENE ===
    if cutscene:
        elapsed = now - cutscene_start
        screen.fill(DARK_BLUE)
        
        for star in stars:
            star["x"] -= star["speed"]
            if star["x"] < 0:
                star["x"] = WIDTH
                star["y"] = random.randint(0, HEIGHT)
            pygame.draw.circle(screen, WHITE, (int(star["x"]), int(star["y"])), 2)

        for cloud in clouds:
            cloud["x"] -= cloud["speed"]
            if cloud["x"] < -cloud["size"] * 2:
                cloud["x"] = WIDTH + cloud["size"]
            pygame.draw.circle(screen, GRAY, (int(cloud["x"]), int(cloud["y"])), cloud["size"])

        hero_cutscene_x = (elapsed / cutscene_duration) * (WIDTH + bird_size) - bird_size
        hero_cutscene_y = HEIGHT // 2 + random.randint(-5, 5)
        pygame.draw.rect(screen, WHITE, (hero_cutscene_x, hero_cutscene_y, bird_size, bird_size))

        text = FONT.render("The Skies Are Finally Peaceful...", True, YELLOW)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
        screen.blit(text, text_rect)

        if elapsed > cutscene_duration:
            cutscene = False
            win = True
            
        pygame.display.update()
        continue

    draw_background()

    # === BUFF CARD SELECTION OVERLAY ===
    if buff_selection_active:
        velocity += gravity
        bird_y += velocity
        if bird_y > HEIGHT // 2 + 50 or bird_y < HEIGHT // 2 - 50:
            velocity = flap_strength
        
        screen.blit(player_img, (bird_x, bird_y))

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        header = FONT.render("CHOOSE A BUFF", True, GOLD)
        screen.blit(header, (WIDTH // 2 - header.get_width() // 2, HEIGHT // 8))

        card_w, card_h = WIDTH // 4, HEIGHT // 2
        start_x = (WIDTH - (len(buff_cards_offered) * card_w + (len(buff_cards_offered) - 1) * 30)) // 2
        card_y = HEIGHT // 2 - card_h // 2
        mouse_pos = pygame.mouse.get_pos()

        for i, buff in enumerate(buff_cards_offered):
            card_x = start_x + i * (card_w + 30)
            card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
            is_hovered = card_rect.collidepoint(mouse_pos)

            bg_color = DARK_GRAY if not is_hovered else (60, 60, 80)
            border_color = GOLD if is_hovered else WHITE
            pygame.draw.rect(screen, bg_color, card_rect, border_radius=15)
            pygame.draw.rect(screen, border_color, card_rect, 4, border_radius=15)

            title_txt = SMALL_FONT.render(buff["title"], True, YELLOW)
            screen.blit(title_txt, (card_x + (card_w - title_txt.get_width()) // 2, card_y + 30))

            words = buff["desc"].split(' ')
            lines = []
            cur_line = ""
            for w in words:
                test_line = cur_line + w + " "
                if CARD_FONT.size(test_line)[0] < card_w - 40:
                    cur_line = test_line
                else:
                    lines.append(cur_line)
                    cur_line = w + " "
            lines.append(cur_line)

            for l_idx, line in enumerate(lines):
                desc_txt = CARD_FONT.render(line, True, WHITE)
                screen.blit(desc_txt, (card_x + (card_w - desc_txt.get_width()) // 2, card_y + 120 + l_idx * 30))

        draw_health()
        pygame.display.update()
        continue

    # === BOSS INTRO ===
    if boss_intro:
        screen.fill((0, 0, 0))
        if boss_number > 0:
            label = SMALL_FONT.render(f"BOSS {boss_number}: {boss_names[boss_number - 1]}", True, RED)
            screen.blit(label, (WIDTH // 2 - label.get_width() // 2, HEIGHT // 2))
        else:
            label = SMALL_FONT.render("A dark presence appears...", True, RED)
            screen.blit(label, (WIDTH // 2 - label.get_width() // 2, HEIGHT // 2))
        if now - boss_intro_time > 2:
            boss_intro = False
            boss_active = True
            can_shoot = True
            countdown_active = True
            countdown_start_time = now
        pygame.display.update()
        continue

    # === 3-SECOND COUNTDOWN STATE ===
    if countdown_active:
        elapsed = now - countdown_start_time
        remaining = COUNTDOWN_DURATION - int(elapsed)

        bird_y = HEIGHT // 2 + (random.randint(-2, 2))
        bird_rect = pygame.Rect(bird_x, bird_y, bird_size, bird_size)
        screen.blit(player_img, (bird_x, bird_y))

        if not boss_active and not no_pipes_active:
            top_pipe = pygame.Rect(pipe_x, 0, pipe_width, pipe_height)
            bottom_pipe = pygame.Rect(pipe_x, pipe_height + pipe_gap, pipe_width, HEIGHT)
            draw_detailed_pipe(top_pipe, is_top=True)
            draw_detailed_pipe(bottom_pipe, is_top=False)
        elif boss_active:
            draw_boss(boss_number, boss_rect, now)

        draw_health()
        
        if remaining > 0:
            count_text = FONT.render(str(remaining), True, YELLOW)
            screen.blit(count_text, (WIDTH // 2 - count_text.get_width() // 2, HEIGHT // 3))
        else:
            count_text = FONT.render("GO!", True, GREEN)
            screen.blit(count_text, (WIDTH // 2 - count_text.get_width() // 2, HEIGHT // 3))

        if elapsed >= COUNTDOWN_DURATION + 0.5:
            countdown_active = False

        pygame.display.update()
        continue

    # === PLAYER PHYSICS ===
    velocity += gravity
    bird_y += velocity
    bird_rect = pygame.Rect(bird_x, bird_y, bird_size, bird_size)

    if invincible and now - last_hit > 2:
        invincible = False

    # === PIPE MOVEMENT ===
    if not boss_active and not boss_dying and score not in BOSS_SCORES:
        pipe_x -= pipe_speed
        if pipe_x < -pipe_width:
            pipe_x = WIDTH
            pipe_height = random.randint(HEIGHT // 6, HEIGHT // 2)
            score += 1

    # === BOSS TRIGGER ===
    if score in BOSS_SCORES and not boss_active and not boss_dying and not boss_intro:
        boss_number = BOSS_SCORES.index(score) + 1
        base_hp = 10 + boss_number * 5
        boss_health = max(1, int(base_hp * boss_health_modifier))
        boss_max_health = boss_health
        boss_rect.x = boss_x_pos
        boss_rect.y = HEIGHT // 2 - boss_size // 2
        boss_intro = True
        boss_intro_time = now
        spikes.clear()
        player_bullets.clear()

    # === DEATH CHECK ===
    if bird_y > HEIGHT or bird_y < 0:
        game_over = True

    # === PIPE COLLISION ===
    top_pipe = pygame.Rect(pipe_x, 0, pipe_width, pipe_height)
    bottom_pipe = pygame.Rect(pipe_x, pipe_height + pipe_gap, pipe_width, HEIGHT)
    if not boss_active and not boss_dying and not no_pipes_active and (bird_rect.colliderect(top_pipe) or bird_rect.colliderect(bottom_pipe)):
        if not invincible:
            player_health -= 1
            last_hit = now
            invincible = True
            if player_health <= 0:
                game_over = True

    # === BOSS BEHAVIOR ===
    if boss_active:
        update_boss_behavior(boss_number, boss_rect, now, now)
        draw_boss(boss_number, boss_rect, now)

        # Spikes / Attacks logic
        for spike in spikes[:]:
            spike["rect"].x += spike["vx"]
            spike["rect"].y += spike["vy"]
            if "gravity" in spike:
                spike["vy"] += spike["gravity"]

            pygame.draw.rect(screen, spike.get("color", ORANGE), spike["rect"])

            if bird_rect.colliderect(spike["rect"]) and not invincible:
                player_health -= 1
                last_hit = now
                invincible = True
                if player_health <= 0:
                    game_over = True
            if spike["rect"].x < 0 or spike["rect"].y > HEIGHT or spike["rect"].y < 0:
                spikes.remove(spike)

        # Bullets
        for bullet in player_bullets[:]:
            bullet.x += player_bullet_speed
            pygame.draw.rect(screen, YELLOW, bullet)
            if bullet.colliderect(boss_rect):
                boss_health -= 1
                player_bullets.remove(bullet)
                if boss_health <= 0:
                    boss_active = False
                    boss_dying = True
                    boss_death_time = now
            elif bullet.x > WIDTH:
                player_bullets.remove(bullet)

        # Boss Health bar
        pygame.draw.rect(screen, RED, (WIDTH - 210, 20, 200, 20))
        pygame.draw.rect(screen, GREEN, (WIDTH - 210, 20, max(0, 200 * (boss_health / boss_max_health)), 20))

    # === BOSS DEATH ===
    if boss_dying:
        elapsed = now - boss_death_time
        if elapsed < 1.5:
            scale = 1 - (elapsed / 1.5)
            dying_rect = pygame.Rect(
                boss_rect.centerx - int(boss_rect.width * scale) // 2,
                boss_rect.centery - int(boss_rect.height * scale) // 2,
                int(boss_rect.width * scale),
                int(boss_rect.height * scale))
            pygame.draw.rect(screen, RED, dying_rect)
        else:
            boss_dying = False
            score += 1
            if score >= 150:
                cutscene = True
                cutscene_start = time.time()
            else:
                pipe_x = WIDTH
                trigger_buff_selection()

    # === DRAW PLAYER ===
    if not invincible or int(now * 10) % 2 == 0:
        screen.blit(player_img, (bird_x, bird_y))

    # === DRAW PIPE ===
    if not boss_active and not no_pipes_active:
        draw_detailed_pipe(top_pipe, is_top=True)
        draw_detailed_pipe(bottom_pipe, is_top=False)

    # === SCORE + HEALTH ===
    score_text = FONT.render(str(score), True, WHITE)
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 20))
    draw_health()

    # === GAME OVER / WIN ===
    if game_over or win:
        label = FONT.render("You Win!" if win else "Game Over", True, YELLOW if win else RED)
        screen.blit(label, (WIDTH // 2 - label.get_width() // 2, HEIGHT // 4))
        restart_button = draw_button("Restart", WIDTH // 2 - 150, HEIGHT // 2, 300, 60)
        quit_button = draw_button("Quit", WIDTH // 2 - 150, HEIGHT // 2 + 100, 300, 60)

    pygame.display.update()

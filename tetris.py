import pygame
import random
import math
import array

# ---------------------------------------------------------------------------
#  Cozy Games — Tetris & Block Blast
# ---------------------------------------------------------------------------

SCREEN_WIDTH = 550
SCREEN_HEIGHT = 700
FPS = 60

COLORS = {
    "bg": (245, 245, 220),
    "board": (250, 249, 246),
    "grid": (230, 228, 220),
    "text": (80, 78, 72),
    "accent": (180, 170, 150),
    "I": (163, 209, 216),
    "J": (142, 167, 190),
    "L": (224, 160, 118),
    "O": (232, 218, 137),
    "S": (166, 194, 154),
    "T": (193, 173, 202),
    "Z": (197, 139, 139),
}

# ---------------------------------------------------------------------------
#  Sound
# ---------------------------------------------------------------------------

def _make_sound(freq, duration, volume=0.25, sample_rate=22050):
    n_samples = int(sample_rate * duration)
    buf = array.array('h', [0]) * n_samples
    for i in range(n_samples):
        t = i / sample_rate
        envelope = max(0, 1.0 - i / n_samples * 0.6)
        value = int(volume * 32767 * envelope * math.sin(2 * math.pi * freq * t))
        buf[i] = value
    return pygame.mixer.Sound(buffer=bytes(buf))


class SoundManager:
    def __init__(self):
        self.enabled = True
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=22050, size=-16, channels=1)
        except pygame.error:
            self.enabled = False

        self.sounds = {}
        if self.enabled:
            self.sounds = {
                "move": _make_sound(200, 0.05, 0.1),
                "rotate": _make_sound(400, 0.08, 0.12),
                "drop": _make_sound(150, 0.15, 0.15),
                "lock": _make_sound(250, 0.12, 0.15),
                "clear1": _make_sound(523, 0.15, 0.2),
                "clear2": _make_sound(659, 0.15, 0.2),
                "clear3": _make_sound(784, 0.15, 0.2),
                "clear4": _make_sound(1047, 0.25, 0.25),
                "levelup": _make_sound(880, 0.3, 0.2),
                "gameover": _make_sound(300, 0.5, 0.2),
                "bb_place": _make_sound(350, 0.1, 0.15),
                "bb_clear": _make_sound(660, 0.2, 0.2),
            }

    def play(self, name):
        if not self.enabled:
            return
        snd = self.sounds.get(name)
        if snd:
            snd.play()


# ===========================================================================
#  TETRIS
# ===========================================================================

def _make_font(size):
    try:
        return pygame.font.SysFont("Helvetica, Arial, sans-serif", size)
    except:
        pass
    try:
        return pygame.font.Font(None, size)
    except:
        return None

TETRIS_CELL = 28
TETRIS_PAD = 2
TETRIS_COLS = 10
TETRIS_ROWS = 20
TETRIS_BOARD_X = (SCREEN_WIDTH - TETRIS_COLS * TETRIS_CELL) // 2
TETRIS_BOARD_Y = 60

TETRIS_SHAPES = {
    "I": [
        [[0,0,0,0],[1,1,1,1],[0,0,0,0],[0,0,0,0]],
        [[0,0,1,0],[0,0,1,0],[0,0,1,0],[0,0,1,0]],
    ],
    "J": [
        [[1,0,0],[1,1,1],[0,0,0]],
        [[0,1,1],[0,1,0],[0,1,0]],
        [[0,0,0],[1,1,1],[0,0,1]],
        [[0,1,0],[0,1,0],[1,1,0]],
    ],
    "L": [
        [[0,0,1],[1,1,1],[0,0,0]],
        [[0,1,0],[0,1,0],[0,1,1]],
        [[0,0,0],[1,1,1],[1,0,0]],
        [[1,1,0],[0,1,0],[0,1,0]],
    ],
    "O": [
        [[0,1,1,0],[0,1,1,0],[0,0,0,0]],
    ],
    "S": [
        [[0,1,1],[1,1,0],[0,0,0]],
        [[0,1,0],[0,1,1],[0,0,1]],
        [[0,0,0],[0,1,1],[1,1,0]],
        [[1,0,0],[1,1,0],[0,1,0]],
    ],
    "T": [
        [[0,1,0],[1,1,1],[0,0,0]],
        [[0,1,0],[0,1,1],[0,1,0]],
        [[0,0,0],[1,1,1],[0,1,0]],
        [[0,1,0],[1,1,0],[0,1,0]],
    ],
    "Z": [
        [[1,1,0],[0,1,1],[0,0,0]],
        [[0,0,1],[0,1,1],[0,1,0]],
        [[0,0,0],[1,1,0],[0,1,1]],
        [[0,1,0],[1,1,0],[1,0,0]],
    ],
}

TETRIS_SPAWN_OFFSETS = {
    "I": (-2, 3), "J": (-2, 3), "L": (-2, 3), "O": (-2, 4),
    "S": (-2, 3), "T": (-2, 3), "Z": (-2, 3),
}

TETRIS_SCORE_TABLE = {1: 100, 2: 300, 3: 500, 4: 800}
TETRIS_BASE_DROP = 1000
TETRIS_MIN_DROP = 150
LINE_CLEAR_FLASH = 400
LINE_CLEAR_FADE = 200
LOCK_FLASH_DUR = 150
SCORE_POPUP_DUR = 1200


class Tetromino:
    def __init__(self, shape_name, x=None, y=None):
        self.shape_name = shape_name
        self.color = COLORS[shape_name]
        self.rotations = TETRIS_SHAPES[shape_name]
        self.rotation_index = 0
        self.matrix = self.rotations[0]
        if x is None or y is None:
            off_y, off_x = TETRIS_SPAWN_OFFSETS[shape_name]
            self.x = off_x
            self.y = off_y
        else:
            self.x = x
            self.y = y

    def cells(self):
        blocks = []
        for r, row in enumerate(self.matrix):
            for c, v in enumerate(row):
                if v:
                    blocks.append((self.y + r, self.x + c))
        return blocks

    def rotate(self, board, clockwise=True):
        direction = 1 if clockwise else -1
        new_idx = (self.rotation_index + direction) % len(self.rotations)
        new_mat = self.rotations[new_idx]
        kicks = [(0,0),(1,0),(-1,0),(0,-1),(0,1)]
        for dx, dy in kicks:
            ok = True
            for r, row in enumerate(new_mat):
                for c, v in enumerate(row):
                    if v:
                        nr, nc = self.y + r + dy, self.x + c + dx
                        if not board.is_valid(nr, nc):
                            ok = False
                            break
                if not ok:
                    break
            if ok:
                self.rotation_index = new_idx
                self.matrix = new_mat
                self.x += dx
                self.y += dy
                return True
        return False

    def move(self, dx, dy, board):
        for r, row in enumerate(self.matrix):
            for c, v in enumerate(row):
                if v:
                    nr, nc = self.y + r + dy, self.x + c + dx
                    if not board.is_valid(nr, nc):
                        return False
        self.x += dx
        self.y += dy
        return True

    def draw(self, surf, ox, oy):
        cs, pd = TETRIS_CELL, TETRIS_PAD
        for r, row in enumerate(self.matrix):
            for c, v in enumerate(row):
                if v:
                    rect = pygame.Rect(ox + (self.x+c)*cs + pd, oy + (self.y+r)*cs + pd,
                                       cs - pd*2, cs - pd*2)
                    pygame.draw.rect(surf, self.color, rect, border_radius=3)


class TetrisBoard:
    def __init__(self):
        self.rows = TETRIS_ROWS
        self.cols = TETRIS_COLS
        self.grid = [[None]*self.cols for _ in range(self.rows)]
        self.score = 0
        self.lines = 0
        self.level = 1

    def is_valid(self, row, col):
        if col < 0 or col >= self.cols or row >= self.rows:
            return False
        if row < 0:
            return True
        return self.grid[row][col] is None

    def lock(self, piece):
        cells = []
        for r, c in piece.cells():
            if 0 <= r < self.rows and 0 <= c < self.cols:
                self.grid[r][c] = piece.color
                cells.append((r, c))
            else:
                return False, cells
        return True, cells

    def clear_lines(self):
        cleared = 0
        r = self.rows - 1
        while r >= 0:
            if all(c is not None for c in self.grid[r]):
                del self.grid[r]
                self.grid.insert(0, [None]*self.cols)
                cleared += 1
            else:
                r -= 1
        return cleared

    def reset(self):
        self.grid = [[None]*self.cols for _ in range(self.rows)]
        self.score = 0
        self.lines = 0
        self.level = 1

    def draw_bg(self, surf):
        cs = TETRIS_CELL
        bx, by = TETRIS_BOARD_X, TETRIS_BOARD_Y
        rect = pygame.Rect(bx, by, self.cols*cs, self.rows*cs)
        pygame.draw.rect(surf, COLORS["board"], rect, border_radius=6)
        for c in range(self.cols+1):
            x = bx + c*cs
            pygame.draw.line(surf, COLORS["grid"], (x, by), (x, by+self.rows*cs))
        for r in range(self.rows+1):
            y = by + r*cs
            pygame.draw.line(surf, COLORS["grid"], (bx, y), (bx+self.cols*cs, y))

    def draw_blocks(self, surf, skip=None):
        cs, pd = TETRIS_CELL, TETRIS_PAD
        bx, by = TETRIS_BOARD_X, TETRIS_BOARD_Y
        for r, row in enumerate(self.grid):
            if skip and r in skip:
                continue
            for c, color in enumerate(row):
                if color:
                    rect = pygame.Rect(bx + c*cs + pd, by + r*cs + pd, cs-pd*2, cs-pd*2)
                    pygame.draw.rect(surf, color, rect, border_radius=3)


class TetrisGame:
    def __init__(self, screen, clock, sound):
        self.screen = screen
        self.clock = clock
        self.sound = sound
        self.font = _make_font(28)
        self.title_font = _make_font(36)
        self.small_font = _make_font(22)

        self.board = TetrisBoard()
        self.next_name = random.choice(list(TETRIS_SHAPES.keys()))
        self.piece = self._spawn()
        self.drop_timer = 0
        self.game_over = False
        self.hard_dropped = False
        self.line_clear_anim = None
        self.lock_flash = None
        self.popups = []
        self.go_timer = 0
        self.go_done = False

    def _spawn(self):
        name = self.next_name
        self.next_name = random.choice(list(TETRIS_SHAPES.keys()))
        return Tetromino(name)

    def _ghost(self):
        g = Tetromino(self.piece.shape_name)
        g.x, g.y = self.piece.x, self.piece.y
        g.rotation_index = self.piece.rotation_index
        g.matrix = self.piece.matrix
        while g.move(0, 1, self.board):
            pass
        return g

    def _full_rows(self):
        return [r for r in range(self.board.rows)
                if all(c is not None for c in self.board.grid[r])]

    def _lock(self):
        _, locked = self.board.lock(self.piece)
        self.sound.play("lock")
        if locked:
            self.lock_flash = {"cells": locked, "timer": 0, "dur": LOCK_FLASH_DUR}

        rows = self._full_rows()
        cleared = self.board.clear_lines()
        if cleared:
            self.board.lines += cleared
            self.board.score += TETRIS_SCORE_TABLE[cleared] * self.board.level
            nl = 1 + self.board.lines // 10
            if nl > self.board.level:
                self.board.level = nl
                self.sound.play("levelup")
            else:
                self.sound.play(["clear1","clear2","clear3","clear4"][min(cleared,4)-1])
            self.line_clear_anim = {"rows": rows, "timer": 0,
                                    "flash": LINE_CLEAR_FLASH, "fade": LINE_CLEAR_FADE}
            pts = TETRIS_SCORE_TABLE[cleared] * self.board.level
            self.popups.append({
                "text": f"+{pts}",
                "x": TETRIS_BOARD_X + self.board.cols * TETRIS_CELL // 2,
                "y": TETRIS_BOARD_Y + rows[0]*TETRIS_CELL,
                "timer": 0, "dur": SCORE_POPUP_DUR,
            })

        self.piece = self._spawn()
        self.hard_dropped = False
        if not self._fits(self.piece):
            self.game_over = True
            self.sound.play("gameover")
            self.go_timer = 0
            self.go_done = False

    def _fits(self, p):
        for r, c in p.cells():
            if not self.board.is_valid(r, c):
                return False
        return True

    def _drop_int(self):
        interval = max(TETRIS_MIN_DROP, TETRIS_BASE_DROP - (self.board.level-1)*80)
        return 50 if self.hard_dropped else interval

    def _update(self, dt):
        if self.line_clear_anim:
            self.line_clear_anim["timer"] += dt
            total = self.line_clear_anim["flash"] + self.line_clear_anim["fade"]
            if self.line_clear_anim["timer"] >= total:
                self.line_clear_anim = None
        if self.lock_flash:
            self.lock_flash["timer"] += dt
            if self.lock_flash["timer"] >= self.lock_flash["dur"]:
                self.lock_flash = None
        for p in self.popups[:]:
            p["timer"] += dt
            p["y"] -= 0.8
            if p["timer"] >= p["dur"]:
                self.popups.remove(p)
        if self.game_over:
            if not self.go_done:
                self.go_timer += dt
                if self.go_timer >= 800:
                    self.go_done = True
            return
        self.drop_timer += dt
        if self.drop_timer >= self._drop_int():
            self.drop_timer = 0
            if not self.piece.move(0, 1, self.board):
                self._lock()

    def _draw(self):
        s = self.screen
        s.fill(COLORS["bg"])
        t = self.title_font.render("Cozy Tetris", True, COLORS["text"])
        s.blit(t, t.get_rect(center=(SCREEN_WIDTH//2, 32)))

        self.board.draw_bg(s)

        skip_rows = set()
        if self.line_clear_anim:
            skip_rows = set(self.line_clear_anim["rows"])
            t = self.line_clear_anim["timer"]
            fd = self.line_clear_anim["flash"]
            for r in skip_rows:
                for c in range(self.board.cols):
                    rect = pygame.Rect(TETRIS_BOARD_X + c*TETRIS_CELL,
                                       TETRIS_BOARD_Y + r*TETRIS_CELL,
                                       TETRIS_CELL, TETRIS_CELL)
                    if t < fd:
                        white = int(255 * ((math.sin(t*0.04)+1)/2))
                        pygame.draw.rect(s, (white, white, white), rect, border_radius=3)
                    else:
                        a = int(255 * (1 - (t-fd)/self.line_clear_anim["fade"]))
                        surf = pygame.Surface((TETRIS_CELL, TETRIS_CELL), pygame.SRCALPHA)
                        surf.fill((255, 255, 255, a))
                        s.blit(surf, rect.topleft)

        self.board.draw_blocks(s, skip=skip_rows if self.line_clear_anim else None)

        if self.lock_flash:
            t = self.lock_flash["timer"] / self.lock_flash["dur"]
            if t < 1:
                w = int(255 * (1-t))
                for r, c in self.lock_flash["cells"]:
                    rect = pygame.Rect(TETRIS_BOARD_X + c*TETRIS_CELL + TETRIS_PAD,
                                       TETRIS_BOARD_Y + r*TETRIS_CELL + TETRIS_PAD,
                                       TETRIS_CELL - TETRIS_PAD*2, TETRIS_CELL - TETRIS_PAD*2)
                    pygame.draw.rect(s, (w, w, w), rect, border_radius=3)

        if not self.game_over:
            g = self._ghost()
            for r, row in enumerate(g.matrix):
                for c, v in enumerate(row):
                    if v:
                        rect = pygame.Rect(
                            TETRIS_BOARD_X + (g.x+c)*TETRIS_CELL + TETRIS_PAD + 2,
                            TETRIS_BOARD_Y + (g.y+r)*TETRIS_CELL + TETRIS_PAD + 2,
                            TETRIS_CELL - TETRIS_PAD*2 - 4, TETRIS_CELL - TETRIS_PAD*2 - 4)
                        pygame.draw.rect(s, g.color, rect, width=2, border_radius=3)
            self.piece.draw(s, TETRIS_BOARD_X, TETRIS_BOARD_Y)

        bx, by = SCREEN_WIDTH - 160, TETRIS_BOARD_Y
        sl = self.font.render("Score", True, COLORS["text"])
        sv = self.font.render(str(self.board.score), True, COLORS["text"])
        s.blit(sl, (bx, by+20))
        s.blit(sv, (bx, by+55))
        ll = self.small_font.render("Lines", True, COLORS["text"])
        lv = self.small_font.render(str(self.board.lines), True, COLORS["text"])
        s.blit(ll, (bx, by+105))
        s.blit(lv, (bx, by+130))
        lvl = self.small_font.render("Level", True, COLORS["text"])
        lvv = self.small_font.render(str(self.board.level), True, COLORS["text"])
        s.blit(lvl, (bx, by+165))
        s.blit(lvv, (bx, by+190))
        pv = self.font.render("Next", True, COLORS["text"])
        s.blit(pv, (bx, by+260))
        self._draw_preview()

        for p in self.popups:
            a = int(255 * (1 - p["timer"]/p["dur"]))
            sf = self.small_font.render(p["text"], True, COLORS["text"])
            sf.set_alpha(a)
            s.blit(sf, sf.get_rect(center=(p["x"], p["y"])))

        if self.game_over:
            self._draw_go()
        pygame.display.flip()

    def _draw_preview(self):
        bx, by = SCREEN_WIDTH - 170, TETRIS_BOARD_Y + 300
        bs = 120
        pygame.draw.rect(self.screen, COLORS["board"], (bx, by, bs, bs), border_radius=6)
        p = Tetromino(self.next_name)
        m, co = p.matrix, p.color
        blk = 22
        pw, ph = len(m[0])*blk, len(m)*blk
        sx, sy = bx + (bs-pw)//2, by + (bs-ph)//2
        for r, row in enumerate(m):
            for c, v in enumerate(row):
                if v:
                    pygame.draw.rect(self.screen, co,
                                     (sx+c*blk+2, sy+r*blk+2, blk-4, blk-4), border_radius=3)

    def _draw_go(self):
        s = self.screen
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((250, 249, 246, 200))
        s.blit(ov, (0, 0))
        scale = 1.0 + 0.3*(1 - min(self.go_timer/800, 1)) if not self.go_done else 1.0
        msg = self.title_font.render("Game Over", True, COLORS["text"])
        sz = msg.get_size()
        scaled = pygame.transform.scale(msg, (int(sz[0]*scale), int(sz[1]*scale)))
        s.blit(scaled, scaled.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2-50)))
        fs = self.font.render(f"Final Score: {self.board.score}", True, COLORS["text"])
        s.blit(fs, fs.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2+10)))
        if self.go_done:
            r = self.font.render("Press 'R' to restart   ESC for menu", True, COLORS["text"])
            s.blit(r, r.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2+60)))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_AC_BACK):
                        return "menu"
                    if self.game_over:
                        if event.key == pygame.K_r and self.go_done:
                            self.board.reset()
                            self.next_name = random.choice(list(TETRIS_SHAPES.keys()))
                            self.piece = self._spawn()
                            self.drop_timer = 0
                            self.game_over = False
                            self.hard_dropped = False
                            self.line_clear_anim = None
                            self.lock_flash = None
                            self.popups = []
                            self.go_timer = 0
                            self.go_done = False
                        continue
                    moved = False
                    if event.key == pygame.K_LEFT:
                        moved = self.piece.move(-1, 0, self.board)
                    elif event.key == pygame.K_RIGHT:
                        moved = self.piece.move(1, 0, self.board)
                    elif event.key == pygame.K_UP:
                        moved = self.piece.rotate(self.board)
                    elif event.key == pygame.K_DOWN:
                        moved = self.piece.move(0, 1, self.board)
                    elif event.key == pygame.K_SPACE:
                        while self.piece.move(0, 1, self.board):
                            pass
                        self.sound.play("drop")
                        self.hard_dropped = True
                        self.drop_timer = self._drop_int()
                        moved = True
                    if moved:
                        if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_DOWN):
                            self.sound.play("move")
                        elif event.key == pygame.K_UP:
                            self.sound.play("rotate")
            self._update(dt)
            self._draw()
        return "quit"


# ===========================================================================
#  BLOCK BLAST
# ===========================================================================

BB_CELL = 44
BB_PAD = 2
BB_COLS = 8
BB_ROWS = 8
BB_GRID_W = BB_COLS * BB_CELL
BB_GRID_H = BB_ROWS * BB_CELL
BB_GRID_X = (SCREEN_WIDTH - BB_GRID_W) // 2
BB_GRID_Y = 100

BB_TRAY_Y = BB_GRID_Y + BB_ROWS * BB_CELL + 28
BB_TRAY_SLOT_W = 130
BB_TRAY_SLOT_H = 90
BB_TRAY_GAP = 12
BB_TRAY_START_X = (SCREEN_WIDTH - (BB_TRAY_SLOT_W * 3 + BB_TRAY_GAP * 2)) // 2

BB_CLEAR_FLASH = 350
BB_CLEAR_FADE = 200
BB_PLACE_FLASH = 150
BB_SCORE_POPUP = 1200

BB_PALETTE = [
    (255, 107, 107), (255, 159, 67), (255, 205, 86),
    (80, 200, 120), (68, 160, 255), (147, 112, 219),
    (255, 105, 180), (0, 188, 212),
]

BB_SHAPES = [
    [[1]],
    [[1, 1]],
    [[1], [1]],
    [[1, 1, 1]],
    [[1], [1], [1]],
    [[1, 0], [1, 0], [1, 1]],
    [[0, 1], [0, 1], [1, 1]],
    [[1, 1, 1, 1]],
    [[1], [1], [1], [1]],
    [[1, 1], [1, 1]],
    [[1, 1, 1], [0, 1, 0]],
    [[1, 1, 0], [0, 1, 1]],
    [[0, 1, 1], [1, 1, 0]],
    [[1, 0], [1, 0], [1, 1], [0, 1]],
    [[0, 1], [0, 1], [1, 1], [1, 0]],
    [[1, 1, 1, 1, 1]],
    [[1], [1], [1], [1], [1]],
]


class BBGrid:
    def __init__(self):
        self.rows = BB_ROWS
        self.cols = BB_COLS
        self.grid = [[None]*BB_COLS for _ in range(BB_ROWS)]

    def can_place(self, r, c, matrix):
        for dr, row in enumerate(matrix):
            for dc, v in enumerate(row):
                if v:
                    nr, nc = r + dr, c + dc
                    if nr < 0 or nr >= self.rows or nc < 0 or nc >= self.cols:
                        return False
                    if self.grid[nr][nc] is not None:
                        return False
        return True

    def place(self, r, c, matrix, color):
        cells = []
        for dr, row in enumerate(matrix):
            for dc, v in enumerate(row):
                if v:
                    self.grid[r+dr][c+dc] = color
                    cells.append((r+dr, c+dc))
        return cells

    def check_clears(self):
        rows = [r for r in range(self.rows) if all(self.grid[r][c] is not None for c in range(self.cols))]
        cols = [c for c in range(self.cols) if all(self.grid[r][c] is not None for r in range(self.rows))]
        return rows, cols

    def apply_clears(self, rows, cols):
        cleared = set()
        for r in rows:
            for c in range(self.cols):
                self.grid[r][c] = None
                cleared.add((r, c))
        for c in cols:
            for r in range(self.rows):
                self.grid[r][c] = None
                cleared.add((r, c))
        return cleared

    def reset(self):
        self.grid = [[None]*BB_COLS for _ in range(BB_ROWS)]


class BlockBlastGame:
    def __init__(self, screen, clock, sound):
        self.screen = screen
        self.clock = clock
        self.sound = sound
        self.font = _make_font(28)
        self.small_font = _make_font(22)
        self.title_font = _make_font(36)
        self.big_font = _make_font(48)

        self.grid = BBGrid()
        self.score = 0
        self.tray = []
        self.selected = None
        self.hover_r = self.hover_c = -1
        self.can_place_hover = False
        self.game_over = False
        self.go_timer = 0
        self.go_done = False

        self.clear_anim = None
        self.place_flash = None
        self.popups = []
        self.cleared_cells = set()

        self._refill_tray()

    def _random_shape(self):
        mat = random.choice(BB_SHAPES)
        color = random.choice(BB_PALETTE)
        return {"matrix": mat, "color": color}

    def _refill_tray(self):
        self.tray = [self._random_shape() for _ in range(3)]
        self.selected = None
        if not self._any_move_possible():
            self.game_over = True
            self.sound.play("gameover")

    def _any_move_possible(self):
        for shape in self.tray:
            m = shape["matrix"]
            h, w = len(m), len(m[0])
            for r in range(self.grid.rows - h + 1):
                for c in range(self.grid.cols - w + 1):
                    if self.grid.can_place(r, c, m):
                        return True
        return False

    def _get_grid_cell(self, mx, my):
        c = (mx - BB_GRID_X) // BB_CELL
        r = (my - BB_GRID_Y) // BB_CELL
        if 0 <= r < self.grid.rows and 0 <= c < self.grid.cols:
            return r, c
        return None, None

    def _get_tray_slot(self, mx, my):
        for i in range(3):
            sx = BB_TRAY_START_X + i * (BB_TRAY_SLOT_W + BB_TRAY_GAP)
            sy = BB_TRAY_Y
            if sx <= mx <= sx + BB_TRAY_SLOT_W and sy <= my <= sy + BB_TRAY_SLOT_H:
                return i
        return None

    def _place_selected(self, r, c):
        shape = self.tray[self.selected]
        if not self.grid.can_place(r, c, shape["matrix"]):
            return
        placed = self.grid.place(r, c, shape["matrix"], shape["color"])
        self.sound.play("bb_place")

        self.place_flash = {"cells": placed, "timer": 0, "dur": BB_PLACE_FLASH}

        rows, cols = self.grid.check_clears()
        if rows or cols:
            self.cleared_cells = self.grid.apply_clears(rows, cols)
            self.score += len(self.cleared_cells) * 10
            self.sound.play("bb_clear")

            total_dur = BB_CLEAR_FLASH + BB_CLEAR_FADE
            self.clear_anim = {
                "rows": rows, "cols": cols,
                "timer": 0, "total": total_dur,
                "flash": BB_CLEAR_FLASH, "fade": BB_CLEAR_FADE,
            }

            pts = len(self.cleared_cells) * 10
            self.popups.append({
                "text": f"+{pts}",
                "x": BB_GRID_X + BB_GRID_W // 2,
                "y": BB_GRID_Y + (rows[0] if rows else cols[0] if cols else 0) * BB_CELL,
                "timer": 0, "dur": BB_SCORE_POPUP,
            })

        self.tray.pop(self.selected)
        self.selected = None
        if not self.tray:
            self._refill_tray()
        elif not self._any_move_possible():
            self.game_over = True
            self.sound.play("gameover")
            self.go_timer = 0
            self.go_done = False

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)
            mx, my = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_AC_BACK):
                        return "menu"
                    if event.key == pygame.K_r and self.game_over and self.go_done:
                        self.grid.reset()
                        self.score = 0
                        self.game_over = False
                        self.clear_anim = None
                        self.place_flash = None
                        self.popups = []
                        self.go_timer = 0
                        self.go_done = False
                        self._refill_tray()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_over or self.clear_anim:
                        continue
                    if event.button == 3:
                        self.selected = None
                        continue
                    if event.button != 1:
                        continue
                    slot = self._get_tray_slot(mx, my)
                    if slot is not None:
                        self.selected = slot if self.selected != slot else None
                        continue
                    if self.selected is not None:
                        r, c = self._get_grid_cell(mx, my)
                        if r is not None:
                            shape = self.tray[self.selected]
                            if self.grid.can_place(r, c, shape["matrix"]):
                                self._place_selected(r, c)
                            else:
                                self.sound.play("lock")

            self.hover_r, self.hover_c = -1, -1
            self.can_place_hover = False
            if not self.game_over and not self.clear_anim and self.selected is not None:
                r, c = self._get_grid_cell(mx, my)
                if r is not None:
                    shape = self.tray[self.selected]
                    if self.grid.can_place(r, c, shape["matrix"]):
                        self.hover_r, self.hover_c = r, c
                        self.can_place_hover = True

            self._update(dt)
            self._draw()
        return "quit"

    def _update(self, dt):
        if self.clear_anim:
            self.clear_anim["timer"] += dt
            if self.clear_anim["timer"] >= self.clear_anim["total"]:
                self.clear_anim = None
                if not self.tray and not self.game_over:
                    self._refill_tray()
                elif not self.game_over and not self._any_move_possible():
                    self.game_over = True
                    self.sound.play("gameover")
                    self.go_timer = 0
                    self.go_done = False

        if self.place_flash:
            self.place_flash["timer"] += dt
            if self.place_flash["timer"] >= self.place_flash["dur"]:
                self.place_flash = None

        for p in self.popups[:]:
            p["timer"] += dt
            p["y"] -= 1.0
            if p["timer"] >= p["dur"]:
                self.popups.remove(p)

        if self.game_over and not self.go_done:
            self.go_timer += dt
            if self.go_timer >= 800:
                self.go_done = True

    def _can_hover(self):
        return self.selected is not None and self.hover_r >= 0 and self.can_place_hover

    def _draw(self):
        s = self.screen
        s.fill(COLORS["bg"])

        t = self.title_font.render("Block Blast", True, COLORS["text"])
        s.blit(t, t.get_rect(center=(SCREEN_WIDTH//2, 35)))

        sc = self.font.render(f"Score: {self.score}", True, COLORS["text"])
        s.blit(sc, (20, 65))

        gx, gy = BB_GRID_X, BB_GRID_Y
        pygame.draw.rect(s, COLORS["board"], (gx, gy, BB_GRID_W, BB_GRID_H), border_radius=6)
        for c in range(BB_COLS+1):
            x = gx + c*BB_CELL
            pygame.draw.line(s, COLORS["grid"], (x, gy), (x, gy + BB_GRID_H))
        for r in range(BB_ROWS+1):
            y = gy + r*BB_CELL
            pygame.draw.line(s, COLORS["grid"], (gx, y), (gx + BB_GRID_W, y))

        # Clear animation overlay
        clearing_cells = set()
        if self.clear_anim:
            t = self.clear_anim["timer"]
            fd = self.clear_anim["flash"]
            rows_set = set(self.clear_anim["rows"])
            cols_set = set(self.clear_anim["cols"])
            for r in rows_set:
                for c in range(BB_COLS):
                    clearing_cells.add((r, c))
            for c in cols_set:
                for r in range(BB_ROWS):
                    clearing_cells.add((r, c))
            for (cr, cc) in clearing_cells:
                rect = pygame.Rect(gx + cc*BB_CELL, gy + cr*BB_CELL, BB_CELL, BB_CELL)
                if t < fd:
                    white = int(255 * ((math.sin(t*0.05)+1)/2))
                    pygame.draw.rect(s, (white, white, white), rect, border_radius=4)
                else:
                    a = int(255 * (1 - (t-fd)/self.clear_anim["fade"]))
                    surf = pygame.Surface((BB_CELL, BB_CELL), pygame.SRCALPHA)
                    surf.fill((255, 255, 255, a))
                    s.blit(surf, rect.topleft)

        # Draw blocks
        for r in range(BB_ROWS):
            for c in range(BB_COLS):
                if self.clear_anim and (r, c) in clearing_cells:
                    continue
                color = self.grid.grid[r][c]
                if color:
                    rect = pygame.Rect(gx + c*BB_CELL + BB_PAD, gy + r*BB_CELL + BB_PAD,
                                       BB_CELL - BB_PAD*2, BB_CELL - BB_PAD*2)
                    pygame.draw.rect(s, color, rect, border_radius=4)
                    inner = rect.inflate(-4, -4)
                    highlight = tuple(min(255, v+40) for v in color)
                    pygame.draw.rect(s, highlight, inner, border_radius=3)

        # Place flash
        if self.place_flash:
            t = self.place_flash["timer"] / self.place_flash["dur"]
            if t < 1:
                w = int(255 * (1-t))
                for (pr, pc) in self.place_flash["cells"]:
                    rect = pygame.Rect(gx + pc*BB_CELL + BB_PAD, gy + pr*BB_CELL + BB_PAD,
                                       BB_CELL - BB_PAD*2, BB_CELL - BB_PAD*2)
                    pygame.draw.rect(s, (w, w, w), rect, border_radius=4)

        # Hover preview
        if self._can_hover():
            shape = self.tray[self.selected]
            m, co = shape["matrix"], shape["color"]
            for dr, row in enumerate(m):
                for dc, v in enumerate(row):
                    if v:
                        hr, hc = self.hover_r + dr, self.hover_c + dc
                        rect = pygame.Rect(gx + hc*BB_CELL + BB_PAD, gy + hr*BB_CELL + BB_PAD,
                                           BB_CELL - BB_PAD*2, BB_CELL - BB_PAD*2)
                        surf = pygame.Surface((BB_CELL-BB_PAD*2, BB_CELL-BB_PAD*2), pygame.SRCALPHA)
                        surf.fill((*co, 140))
                        s.blit(surf, rect.topleft)
                        pygame.draw.rect(s, co, rect, width=2, border_radius=4)
        elif not self.game_over and not self.clear_anim and self.selected is not None:
            shape = self.tray[self.selected]
            m, co = shape["matrix"], shape["color"]
            r, c = self._get_grid_cell(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1])
            if r is not None:
                for dr, row in enumerate(m):
                    for dc, v in enumerate(row):
                        if v:
                            hr, hc = r + dr, c + dc
                            if 0 <= hr < BB_ROWS and 0 <= hc < BB_COLS:
                                rect = pygame.Rect(gx + hc*BB_CELL + BB_PAD, gy + hr*BB_CELL + BB_PAD,
                                                   BB_CELL - BB_PAD*2, BB_CELL - BB_PAD*2)
                                pygame.draw.rect(s, (200, 100, 100), rect, width=2, border_radius=4)

        # Tray
        for i, shape in enumerate(self.tray):
            sx = BB_TRAY_START_X + i * (BB_TRAY_SLOT_W + BB_TRAY_GAP)
            sy = BB_TRAY_Y
            selected = self.selected == i
            hovered = not self.clear_anim and sx <= pygame.mouse.get_pos()[0] <= sx + BB_TRAY_SLOT_W \
                      and sy <= pygame.mouse.get_pos()[1] <= sy + BB_TRAY_SLOT_H
            bg = (210, 205, 190) if selected else (COLORS["accent"] if hovered else COLORS["board"])
            pygame.draw.rect(s, bg, (sx, sy, BB_TRAY_SLOT_W, BB_TRAY_SLOT_H), border_radius=8)
            if selected:
                pygame.draw.rect(s, COLORS["text"], (sx, sy, BB_TRAY_SLOT_W, BB_TRAY_SLOT_H),
                                 width=3, border_radius=8)

            m, co = shape["matrix"], shape["color"]
            blk = 18
            pw, ph = len(m[0])*blk, len(m)*blk
            ox = sx + (BB_TRAY_SLOT_W - pw)//2
            oy = sy + (BB_TRAY_SLOT_H - ph)//2
            for dr, row in enumerate(m):
                for dc, v in enumerate(row):
                    if v:
                        pygame.draw.rect(s, co, (ox + dc*blk + 1, oy + dr*blk + 1, blk-2, blk-2),
                                         border_radius=2)
                        inner_co = tuple(min(255, v+50) for v in co)
                        pygame.draw.rect(s, inner_co, (ox + dc*blk + 3, oy + dr*blk + 3, blk-6, blk-6),
                                         border_radius=1)

        # Score popups
        for p in self.popups:
            a = int(255 * (1 - p["timer"]/p["dur"]))
            surf = self.big_font.render(p["text"], True, (100, 200, 100))
            surf.set_alpha(a)
            s.blit(surf, surf.get_rect(center=(p["x"], p["y"])))

        if self.game_over:
            ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            ov.fill((250, 249, 246, 200))
            s.blit(ov, (0, 0))
            scale = 1.0 + 0.3*(1 - min(self.go_timer/800, 1)) if not self.go_done else 1.0
            msg = self.title_font.render("Game Over", True, COLORS["text"])
            sz = msg.get_size()
            scaled = pygame.transform.scale(msg, (int(sz[0]*scale), int(sz[1]*scale)))
            s.blit(scaled, scaled.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2-50)))
            fs = self.font.render(f"Final Score: {self.score}", True, COLORS["text"])
            s.blit(fs, fs.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2+10)))
            if self.go_done:
                r = self.small_font.render("Press 'R' to restart   ESC for menu", True, COLORS["text"])
                s.blit(r, r.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2+55)))

        pygame.display.flip()


# ===========================================================================
#  MENU
# ===========================================================================

class Menu:
    def __init__(self, screen, clock, sound):
        self.screen = screen
        self.clock = clock
        self.sound = sound
        self.font = _make_font(28)
        self.small_font = _make_font(22)
        self.title_font = _make_font(48)
        self.big_font = _make_font(36)

        self.buttons = [
            {"label": "Tetris",     "rect": pygame.Rect(0, 0, 250, 70)},
            {"label": "Block Blast", "rect": pygame.Rect(0, 0, 250, 70)},
        ]
        cx = SCREEN_WIDTH // 2
        self.buttons[0]["rect"].center = (cx, 320)
        self.buttons[1]["rect"].center = (cx, 420)

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)
            mx, my = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_AC_BACK):
                        return "quit"
                    if event.key == pygame.K_1:
                        return "tetris"
                    if event.key == pygame.K_2:
                        return "blockblast"

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, btn in enumerate(self.buttons):
                        if btn["rect"].collidepoint(mx, my):
                            return ["tetris", "blockblast"][i]

            self._draw(mx, my)
        return "quit"

    def _draw(self, mx, my):
        s = self.screen
        s.fill(COLORS["bg"])

        t = self.title_font.render("Cozy Games", True, COLORS["text"])
        s.blit(t, t.get_rect(center=(SCREEN_WIDTH//2, 120)))

        sub = self.font.render("Choose a game", True, COLORS["accent"])
        s.blit(sub, sub.get_rect(center=(SCREEN_WIDTH//2, 175)))

        for btn in self.buttons:
            hover = btn["rect"].collidepoint(mx, my)
            color = COLORS["accent"] if hover else COLORS["board"]
            pygame.draw.rect(s, color, btn["rect"], border_radius=12)
            if hover:
                pygame.draw.rect(s, COLORS["text"], btn["rect"], width=2, border_radius=12)
            label = self.big_font.render(btn["label"], True, COLORS["text"])
            s.blit(label, label.get_rect(center=btn["rect"].center))

        hint = self.font.render("Press 1 or 2 to select", True, COLORS["accent"])
        s.blit(hint, hint.get_rect(center=(SCREEN_WIDTH//2, 530)))

        esc = self.small_font.render("ESC to quit", True, COLORS["accent"])
        s.blit(esc, esc.get_rect(center=(SCREEN_WIDTH//2, 570)))

        pygame.display.flip()


# ===========================================================================
#  MAIN
# ===========================================================================

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("Cozy Games")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    sound = SoundManager()

    while True:
        menu = Menu(screen, clock, sound)
        choice = menu.run()
        if choice == "quit":
            break
        elif choice == "tetris":
            game = TetrisGame(screen, clock, sound)
            result = game.run()
            if result == "quit":
                break
        elif choice == "blockblast":
            game = BlockBlastGame(screen, clock, sound)
            result = game.run()
            if result == "quit":
                break

    pygame.quit()

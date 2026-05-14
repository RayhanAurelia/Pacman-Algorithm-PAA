COLS = 21
ROWS = 15
TILE = 36

HUD_HEIGHT = 76
WIDTH = COLS * TILE
HEIGHT = ROWS * TILE + HUD_HEIGHT

FPS = 60

# Wall thickness (in pixels). Walls are drawn as fat rounded tubes.
WALL_THICK = max(8, TILE // 4)

BLACK         = (6, 6, 14)
BG_DEEP       = (3, 3, 10)

WALL_DARK     = (18, 22, 70)
WALL          = (66, 80, 220)
WALL_HL       = (160, 180, 255)

FLOOR         = (14, 14, 26)
FLOOR_DOT     = (26, 26, 44)

MUD           = (120, 78, 30)
MUD_DARK      = (70, 42, 14)
MUD_HL        = (180, 130, 60)

PELLET        = (255, 220, 130)
PELLET_GLOW   = (255, 180, 80)
POWER         = (255, 240, 180)

PLAYER        = (255, 226, 0)
PLAYER_DARK   = (210, 170, 0)
PLAYER_HL     = (255, 250, 200)

ENEMY_BFS       = (240, 70, 80)
ENEMY_BFS_HL    = (255, 160, 170)
ENEMY_DIJK      = (90, 190, 255)
ENEMY_DIJK_HL   = (180, 230, 255)
ENEMY_EYE       = (245, 245, 250)
ENEMY_PUPIL     = (10, 14, 40)

TEXT          = (240, 240, 245)
TEXT_DIM      = (150, 150, 175)
HUD_BG        = (3, 3, 10)
HUD_LINE      = (40, 50, 110)

WIN_COLOR     = (130, 245, 150)
LOSE_COLOR    = (250, 90, 90)

PLAYER_SPEED      = 5.0
ENEMY_BFS_SPEED   = 3.8
ENEMY_DIJK_SPEED  = 3.6

MUD_SLOWDOWN = 0.35

MUD_COST     = 6
NORMAL_COST  = 1
MUD_RATIO    = 0.16

RECOMPUTE_INTERVAL = 0.30

START_LIVES = 3

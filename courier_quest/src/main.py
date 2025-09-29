# courier_quest/src/main.py
import os, json, pygame
from collections import deque

# ---------------- Normalización de datos ----------------
def _extract_map_meta(d):
    if isinstance(d, dict):
        if isinstance(d.get("data"), dict):
            return d["data"]
        return d
    return {}

def _extract_jobs_list(d):
    if isinstance(d, list):
        return [j for j in d if isinstance(j, dict)]
    if isinstance(d, dict):
        for k in ("data", "jobs", "items", "results"):
            val = d.get(k)
            if isinstance(val, list):
                return [j for j in val if isinstance(j, dict)]
            if isinstance(val, dict):
                for k2 in ("jobs", "items", "results"):
                    inner = val.get(k2)
                    if isinstance(inner, list):
                        return [j for j in inner if isinstance(j, dict)]
        return []
    return []

# ---------------- Rutas ----------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
IMG_DIR  = os.path.join(BASE_DIR, "images")
SAV_DIR  = os.path.join(BASE_DIR, "saves")
os.makedirs(SAV_DIR, exist_ok=True)

def _json_load(rel_path):
    try:
        with open(os.path.join(DATA_DIR, rel_path), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def load_image(rel_path):
    p = os.path.join(IMG_DIR, rel_path)
    if not os.path.exists(p):
        return None
    try:
        return pygame.image.load(p).convert_alpha()
    except Exception:
        return None

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

# ---------------- Imports del juego ----------------
from .api.client import APIClient
from .api.cache import APICache
from .game import weather as weather_mod
from .game.courier import Courier
from .game import constants as C
from .game.scoreboard import save_score
from .game.savegame import save_slot, load_slot
from .game.world import World

# ---------------- Pygame (ventana final primero) ----------------
pygame.init()
pygame.display.set_caption("Courier Quest")

SCREEN_W = getattr(C, "SCREEN_W", 960)
SCREEN_H = getattr(C, "SCREEN_H", 640)
TILE     = getattr(C, "TILE_SIZE", 32)
FPS      = getattr(C, "FPS", 60)

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
clock  = pygame.time.Clock()
font   = pygame.font.SysFont("consolas", 18)

# ---------------- Datos (API → caché → /data) ----------------
api_cache = APICache()
api = APIClient(api_cache=api_cache)

map_data  = api.get_map_data()     or _json_load("map.json")
jobs_data = api.get_jobs_data()    or _json_load("jobs.json")
wea_data  = api.get_weather_data() or _json_load("weather.json")

# ---------------- Texturas ----------------
street_images = {
    "centro":                   load_image("calle_centro.png"),
    "horizontal":               load_image("calle_horizontal.png"),
    "vertical":                 load_image("calle_vertical.png"),
    "borde_izquierda":          load_image("calle_borde_izquierda.png"),
    "borde_derecha":            load_image("calle_borde_derecha.png"),
    "borde_arriba":             load_image("calle_borde_arriba.png"),
    "borde_abajo":              load_image("calle_borde_abajo.png"),
    "esquina_arriba_derecha":   load_image("calle_esquina_arriba_derecha.png"),
    "esquina_arriba_izquierda": load_image("calle_esquina_arriba_izquierda.png"),
    "esquina_abajo_derecha":    load_image("calle_esquina_abajo_derecha.png"),
    "esquina_abajo_izquierda":  load_image("calle_esquina_abajo_izquierda.png"),
    "default":                  load_image("calle.png"),
}
street_images = {k: v for k, v in street_images.items() if v is not None}

grass_image = load_image("cesped.png")

# Edificios disponibles por tamaño (según tus PNG)
_build_sizes = [
    (2,2),(3,3),(3,4),(4,4),(4,5),(5,4),(5,5),(5,7),
    (6,5),(6,8),(7,7),(7,9)
]
building_images = {}
for (w,h) in _build_sizes:
    img = load_image(f"edificio{w}x{h}.png")
    if img is not None:
        building_images[(w,h)] = img

# ---------------- Mundo / meta ----------------
world = World(map_data, building_images=building_images,
              grass_image=grass_image, street_images=street_images)

_map_meta  = _extract_map_meta(map_data)
goal_money = _map_meta.get("goal", 3000)

# ---------------- Reloj / clima / jugador ----------------
MAX_TIME  = getattr(C, "GAME_SECONDS", 12 * 60)
time_left = MAX_TIME

weather = weather_mod.WeatherManager(wea_data)

spawn = _map_meta.get("spawn", [1, 1])
courier_img = load_image("repartidor.png")
if courier_img:
    courier_img = pygame.transform.scale(courier_img, (TILE, TILE))
courier = Courier(spawn[0], spawn[1], courier_img)

# ---------------- Pedidos ----------------
AVAILABLE_JOBS = _extract_jobs_list(jobs_data)
PENDING_JOBS = [j for j in AVAILABLE_JOBS if float(j.get("release_time", 0) or 0) > 0.0]
for j in PENDING_JOBS:
    if j in AVAILABLE_JOBS:
        AVAILABLE_JOBS.remove(j)

# ---------------- Undo ----------------
class GameState:
    def __init__(self, courier, time_left):
        self.stamina = courier.stamina
        self.max_stamina = courier.max_stamina
        self.reputation = courier.reputation
        self.money = courier.money
        self.inventory = list(courier.inventory)
        self.pos = (courier.x, courier.y)
        self.time_left = time_left

def snapshot():
    return GameState(courier, time_left)

UNDO = deque(maxlen=50)

def undo_n(n=1):
    global time_left
    while n > 0 and UNDO:
        s = UNDO.pop()
        courier.stamina = s.stamina
        courier.max_stamina = s.max_stamina
        courier.reputation = s.reputation
        courier.money = s.money
        courier.inventory = deque(s.inventory)
        courier.x, courier.y = s.pos
        time_left = s.time_left
        n -= 1

# ---------------- Movimiento por celdas/seg ----------------
move_accum = 0.0

def try_move(dx, dy, dt):
    global move_accum
    if dx == 0 and dy == 0:
        courier.rest(dt_seconds=dt, boosted=False)
        return
    nx, ny = courier.x + dx, courier.y + dy
    if not world.is_walkable(nx, ny):
        return

    m_surface = world.surface_weight_at(nx, ny)
    m_clima   = weather.speed_multiplier()
    speed     = courier.speed(m_clima, m_surface)  # celdas/seg

    if speed <= 0:
        courier.rest(dt_seconds=dt, boosted=False)
        return

    move_accum += dt * speed
    if move_accum >= 1.0 and courier.step_to(nx, ny, weather.label(), m_surface):
        move_accum -= 1.0

# ---------------- Reglas reputación/pago ----------------
def apply_delivery_rules(job, arrive_early=False, late_secs=0):
    if arrive_early:
        courier.reputation = clamp(courier.reputation + 5, 0, 100)
    else:
        if late_secs <= 0:
            courier.reputation = clamp(courier.reputation + 3, 0, 100)
        elif late_secs <= 30:
            courier.reputation -= 2
        elif late_secs <= 120:
            courier.reputation -= 5
        else:
            courier.reputation -= 10

    pay = float(job.get("payout", 0))
    if courier.reputation >= 90:
        pay *= 1.05
    courier.money += pay

# ---------------- HUD ----------------
def draw_hud():
    lines = [
        f"$$: {courier.money:.0f} / Meta: {goal_money}",
        f"Rep: {courier.reputation}   Stamina: {courier.stamina:.0f}",
        f"Clima: {weather.label()}",
        f"Tiempo: {int(time_left)} s",
        f"Inv (peso {courier.total_weight()} / {courier.max_weight}): {len(courier.inventory)}"
    ]
    y = 5
    for t in lines:
        img = font.render(t, True, (255,255,255))
        screen.blit(img, (8,y))
        y += 20

    # --- DEBUG: coordenadas e inventario
    img = font.render(f"Pos: ({courier.x}, {courier.y})", True, (180, 220, 255))
    screen.blit(img, (8, y)); y += 20
    inv_ids = [str(it.get('id', '?')) for it in courier.inventory]
    img = font.render(f"Inv IDs: {', '.join(inv_ids) or '-'}", True, (180, 220, 255))
    screen.blit(img, (8, y)); y += 20

def draw_jobs_panel():
    y = 160  # bajamos un poco para que no tape el debug
    title = font.render("Pedidos (A=aceptar en pickup, D=entregar en dropoff)", True, (255,255,0))
    screen.blit(title, (8,y)); y += 22
    for j in AVAILABLE_JOBS[:6]:
        txt = f"{j.get('id')} peso:{j.get('weight')} pay:{j.get('payout')} pickup:{tuple(j.get('pickup',[]))}"
        img = font.render(txt, True, (200,200,200))
        screen.blit(img, (8,y)); y += 18

# ---------------- Bucle principal ----------------
running = True
result = "ABORT"

while running:
    dt = clock.tick(FPS) / 1000.0
    weather.update()

    # liberar jobs por release_time
    rels = []
    for j in list(PENDING_JOBS):
        j["release_time"] = max(0.0, float(j.get("release_time", 0) or 0) - dt)
        if j["release_time"] <= 0:
            rels.append(j)
    for j in rels:
        PENDING_JOBS.remove(j)
        AVAILABLE_JOBS.append(j)

    # tiempo de juego
    time_left = max(0, time_left - dt)

    # eventos
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                undo_n(5)
            elif e.key == pygame.K_z:
                undo_n(1)
            elif e.key == pygame.K_F5:
                save_slot("slot1.sav", snapshot())
            elif e.key == pygame.K_F9:
                s = load_slot("slot1.sav")
                courier.stamina = s.stamina
                courier.max_stamina = s.max_stamina
                courier.reputation = s.reputation
                courier.money = s.money
                courier.inventory = deque(s.inventory)
                courier.x, courier.y = s.pos
                time_left = s.time_left
            elif e.key == pygame.K_q:
                courier.rotate_backward()
            elif e.key == pygame.K_e:
                courier.rotate_forward()
            elif e.key == pygame.K_a:
                here = (courier.x, courier.y)
                picked = None
                for j in AVAILABLE_JOBS:
                    if tuple(j.get("pickup",[None,None])) == here:
                        if courier.accept_job(j):
                            picked = j
                            break
                if picked:
                    AVAILABLE_JOBS.remove(picked)
            elif e.key == pygame.K_d:
                if courier.inventory:
                    current = courier.inventory[0]
                    if tuple(current.get("dropoff",[None,None])) == (courier.x, courier.y):
                        courier.inventory.popleft()
                        apply_delivery_rules(current, arrive_early=False, late_secs=0)

    # movimiento
    keys = pygame.key.get_pressed()
    dx = (1 if keys[pygame.K_RIGHT] else 0) - (1 if keys[pygame.K_LEFT] else 0)
    dy = (1 if keys[pygame.K_DOWN]  else 0) - (1 if keys[pygame.K_UP]   else 0)
    if dx or dy:
        UNDO.append(snapshot())
    try_move(dx, dy, dt)

    # victoria/derrota
    if courier.reputation < 20:
        running = False
        result = "DERROTA (reputación)"
    elif time_left <= 0 and courier.money < goal_money:
        running = False
        result = "DERROTA (tiempo)"
    elif courier.money >= goal_money:
        running = False
        result = "VICTORIA"

    # render
    screen.fill((20,20,24))
    world.draw(screen, TILE)
    courier.draw(screen, TILE)
    draw_hud()
    draw_jobs_panel()
    pygame.display.flip()

# fin de partida
score_base   = courier.money * (1.05 if courier.reputation >= 90 else 1.0)
bonus_tiempo = 100 if time_left > MAX_TIME * 0.2 else 0
score        = score_base + bonus_tiempo
save_score({
    "player": "default",
    "money": round(courier.money, 2),
    "rep": courier.reputation,
    "score": round(score, 2),
    "result": result
})
print(result)
pygame.quit()

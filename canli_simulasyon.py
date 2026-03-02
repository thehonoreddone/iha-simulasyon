"""
=============================================================================
 Tarım 5.0 — Canlı & Etkileşimli Drone Veri Toplama Simülasyonu
 TEK DOSYA — python canli_simulasyon.py ile çalıştır
=============================================================================
"""

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
from collections import deque
import sys, time

# ═══════════════════════════════════════════════════════════════════════
#  AYARLAR  (değiştirmek istersen burayı düzenle)
# ═══════════════════════════════════════════════════════════════════════
ALAN_W, ALAN_H   = 500, 500        # metre
SENSOR_N          = 30              # sensör sayısı
SENSOR_ENERJI     = 0.5            # Joule başlangıç
SENSOR_BELLEK_MAX = 100            # paket
VERI_URETIM_DT    = 10             # saniye
PAKET_BIT         = 4000           # bit / paket

DRONE_HIZ         = 10             # m/s
DRONE_H           = 50             # metre uçuş yüksekliği
DRONE_MENZIL      = 60             # metre iletişim menzili
DRONE_BEKLEME     = 2              # saniye / durak
DRONE_TUR_ARASI   = 120            # saniye turlar arası mola

# Multi-hop karşılaştırma
BAZ_XY            = np.array([250.0, 550.0])
MHOP_MENZIL       = 80

# Enerji modeli (First-order radio)
E_ELEC = 50e-9;  E_FS = 10e-12;  E_MP = 0.0013e-12;  D0 = 87

# Animasyon hızı
SIM_DT      = 1.0          # her frame = 1 simülasyon-saniye
FPS         = 30            # animasyon kare hızı
SPEED       = 4            # simülasyon hız çarpanı (4x hızlı)
SEED        = 42

# ═══════════════════════════════════════════════════════════════════════
#  ENERJİ
# ═══════════════════════════════════════════════════════════════════════
def tx_energy(bits, d):
    if d < D0:
        return E_ELEC * bits + E_FS * bits * d**2
    return E_ELEC * bits + E_MP * bits * d**4

def sense_energy(bits):
    return 5e-9 * bits

def dist3d(a, b, dh=0.0):
    return np.sqrt(np.sum((a - b)**2) + dh**2)

# ═══════════════════════════════════════════════════════════════════════
#  SENSÖR
# ═══════════════════════════════════════════════════════════════════════
class Sensor:
    __slots__ = ("id","xy","e","e0","buf","alive",
                 "total_gen","total_tx","total_lost","flash")
    def __init__(self, sid, x, y):
        self.id = sid
        self.xy = np.array([x, y])
        self.e0 = SENSOR_ENERJI
        self.e  = SENSOR_ENERJI
        self.buf = 0
        self.alive = True
        self.total_gen = 0
        self.total_tx  = 0
        self.total_lost = 0
        self.flash = 0           # toplama animasyonu sayacı

    def generate(self):
        if not self.alive: return
        c = sense_energy(PAKET_BIT)
        if self.e < c:
            self.alive = False; return
        self.e -= c
        self.total_gen += 1
        if self.buf >= SENSOR_BELLEK_MAX:
            self.total_lost += 1
        else:
            self.buf += 1

    def transmit_to(self, target_xy):
        if not self.alive or self.buf == 0: return 0
        d = dist3d(self.xy, target_xy, DRONE_H)
        sent = 0
        while self.buf > 0:
            cost = tx_energy(PAKET_BIT, d)
            if self.e < cost: break
            self.e -= cost
            self.buf -= 1
            self.total_tx += 1
            sent += 1
        if self.e <= 0:
            self.e = 0; self.alive = False
        return sent

    def mhop_transmit(self, d):
        if not self.alive or self.buf == 0: return 0
        sent = 0
        while self.buf > 0:
            cost = tx_energy(PAKET_BIT, d)
            if self.e < cost:
                self.alive = False; break
            self.e -= cost; self.buf -= 1; self.total_tx += 1; sent += 1
        return sent

    @property
    def pct(self):
        return self.e / self.e0 * 100

# ═══════════════════════════════════════════════════════════════════════
#  ROTA: Nearest-Neighbour + 2-Opt
# ═══════════════════════════════════════════════════════════════════════
def build_route(positions, start):
    pts = [start] + list(positions)
    n = len(pts)
    dm = np.zeros((n, n))
    for i in range(n):
        for j in range(i+1, n):
            d = np.linalg.norm(pts[i] - pts[j])
            dm[i][j] = dm[j][i] = d
    # nearest-neighbour
    vis = [False]*n; route = [0]; vis[0] = True
    for _ in range(n-1):
        cur = route[-1]; best_j, best_d = -1, 1e18
        for j in range(n):
            if not vis[j] and dm[cur][j] < best_d:
                best_d = dm[cur][j]; best_j = j
        route.append(best_j); vis[best_j] = True
    route.append(0)
    # 2-opt
    improved = True
    while improved:
        improved = False
        for i in range(1, len(route)-2):
            for j in range(i+1, len(route)-1):
                new = route[:i] + route[i:j+1][::-1] + route[j+1:]
                old_d = sum(dm[route[k]][route[k+1]] for k in range(len(route)-1))
                new_d = sum(dm[new[k]][new[k+1]] for k in range(len(new)-1))
                if new_d < old_d - 1e-9:
                    route = new; improved = True
    return [pts[i] for i in route]

# ═══════════════════════════════════════════════════════════════════════
#  MULTI-HOP — yönlendirme
# ═══════════════════════════════════════════════════════════════════════
def mhop_routing(sensors):
    table = {}
    for s in sensors:
        d_baz = np.linalg.norm(s.xy - BAZ_XY)
        if d_baz <= MHOP_MENZIL:
            table[s.id] = d_baz
        else:
            best_d = 1e18
            for o in sensors:
                if o.id == s.id: continue
                cd = np.linalg.norm(s.xy - o.xy)
                od = np.linalg.norm(o.xy - BAZ_XY)
                if od < d_baz and cd < best_d:
                    best_d = cd
            table[s.id] = best_d if best_d < 1e18 else d_baz
    return table

# ═══════════════════════════════════════════════════════════════════════
#  SİMÜLASYON DURUMU
# ═══════════════════════════════════════════════════════════════════════
class SimState:
    def __init__(self):
        np.random.seed(SEED)
        # --- Drone senaryosu sensörleri ---
        self.sensors = []
        for i in range(SENSOR_N):
            x = np.random.uniform(20, ALAN_W-20)
            y = np.random.uniform(20, ALAN_H-20)
            self.sensors.append(Sensor(i, x, y))

        # --- Multi-hop senaryosu (aynı konumlar, ayrı nesneler) ---
        np.random.seed(SEED)
        self.mh_sensors = []
        for i in range(SENSOR_N):
            x = np.random.uniform(20, ALAN_W-20)
            y = np.random.uniform(20, ALAN_H-20)
            self.mh_sensors.append(Sensor(i, x, y))
        self.mh_table = mhop_routing(self.mh_sensors)

        # --- Drone ---
        self.drone_home = np.array([0.0, 0.0])
        self.drone_xy   = self.drone_home.copy()
        self.drone_route = []
        self.drone_seg   = 0          # route segment index
        self.drone_t     = 0.0        # segment içi ilerleme (0..1)
        self.drone_state = "wait"     # wait | fly | collect | return_home
        self.drone_wait_timer = 10    # ilk kalkış beklemesi
        self.drone_tours = 0
        self.drone_collected = 0
        self.drone_trail = deque(maxlen=3000)
        self.drone_total_dist = 0.0
        self.collect_lines = []       # (sensor_xy, alpha) toplama çizgileri

        # --- Zaman ---
        self.t = 0.0
        self.last_gen = -VERI_URETIM_DT  # ilk üretim t=0'da olsun

        # --- Tarihçe ---
        self.hist_t = []
        self.hist_drone_e = []
        self.hist_mhop_e  = []
        self.hist_drone_alive = []
        self.hist_mhop_alive  = []

        self._plan_route()

    # ── rota planla ──
    def _plan_route(self):
        alive = [s for s in self.sensors if s.alive]
        if not alive:
            self.drone_route = [self.drone_home, self.drone_home]
            return
        positions = [s.xy for s in alive]
        self.drone_route = build_route(positions, self.drone_home)
        self.drone_seg = 0
        self.drone_t = 0.0

    # ── bir simülasyon adımı (dt saniye) ──
    def step(self, dt):
        self.t += dt

        # Veri üretimi
        if self.t - self.last_gen >= VERI_URETIM_DT:
            self.last_gen = self.t
            for s in self.sensors:
                s.generate()
            for s in self.mh_sensors:
                s.generate()
            # multi-hop iletim
            for s in self.mh_sensors:
                if s.alive and s.buf > 0 and s.id in self.mh_table:
                    s.mhop_transmit(self.mh_table[s.id])

        # Flash azalt
        for s in self.sensors:
            if s.flash > 0:
                s.flash -= dt
        self.collect_lines = [(xy, a - dt*2) for xy, a in self.collect_lines if a - dt*2 > 0]

        # ── Drone durumu ──
        if self.drone_state == "wait":
            self.drone_wait_timer -= dt
            if self.drone_wait_timer <= 0:
                self.drone_state = "fly"
                self.drone_tours += 1
                self._plan_route()

        elif self.drone_state == "fly":
            if self.drone_seg >= len(self.drone_route) - 1:
                # tur bitti, eve dön
                self.drone_state = "return_home"
                return

            p1 = self.drone_route[self.drone_seg]
            p2 = self.drone_route[self.drone_seg + 1]
            seg_len = np.linalg.norm(p2 - p1)
            if seg_len < 0.1:
                self.drone_seg += 1
                self.drone_t = 0.0
                return

            move = DRONE_HIZ * dt / seg_len
            self.drone_t += move
            if self.drone_t >= 1.0:
                self.drone_xy = p2.copy()
                self.drone_total_dist += seg_len * (1.0 - (self.drone_t - move))
                self.drone_trail.append(self.drone_xy.copy())
                # toplama yap
                self._collect_at_pos()
                self.drone_seg += 1
                self.drone_t = 0.0
            else:
                self.drone_xy = p1 + (p2 - p1) * self.drone_t
                self.drone_total_dist += DRONE_HIZ * dt
                self.drone_trail.append(self.drone_xy.copy())

        elif self.drone_state == "return_home":
            d_home = np.linalg.norm(self.drone_home - self.drone_xy)
            if d_home < 1.0:
                self.drone_xy = self.drone_home.copy()
                self.drone_state = "wait"
                self.drone_wait_timer = DRONE_TUR_ARASI
            else:
                direction = (self.drone_home - self.drone_xy)
                direction = direction / np.linalg.norm(direction)
                step = direction * DRONE_HIZ * dt
                if np.linalg.norm(step) > d_home:
                    self.drone_xy = self.drone_home.copy()
                else:
                    self.drone_xy += step
                self.drone_total_dist += min(DRONE_HIZ * dt, d_home)
                self.drone_trail.append(self.drone_xy.copy())

        # tarihçe (her 30 saniyede)
        if len(self.hist_t) == 0 or self.t - self.hist_t[-1] >= 30:
            self.hist_t.append(self.t)
            d_alive = sum(1 for s in self.sensors if s.alive)
            m_alive = sum(1 for s in self.mh_sensors if s.alive)
            d_avg = np.mean([s.pct for s in self.sensors])
            m_avg = np.mean([s.pct for s in self.mh_sensors])
            self.hist_drone_e.append(d_avg)
            self.hist_mhop_e.append(m_avg)
            self.hist_drone_alive.append(d_alive)
            self.hist_mhop_alive.append(m_alive)

    def _collect_at_pos(self):
        for s in self.sensors:
            if s.alive and s.buf > 0:
                d = dist3d(self.drone_xy, s.xy, DRONE_H)
                if d <= DRONE_MENZIL:
                    n = s.transmit_to(self.drone_xy)
                    if n > 0:
                        self.drone_collected += n
                        s.flash = 3.0  # 3 saniye parlama
                        self.collect_lines.append((s.xy.copy(), 1.0))

# ═══════════════════════════════════════════════════════════════════════
#  ANİMASYON
# ═══════════════════════════════════════════════════════════════════════
def run_animation():
    state = SimState()

    fig = plt.figure(figsize=(16, 9), facecolor='#1a1a2e')
    fig.canvas.manager.set_window_title("Tarım 5.0 — Canlı Drone Simülasyonu")

    # Layout: sol = ana harita, sağ üst = enerji grafiği, sağ alt = istatistik
    gs = fig.add_gridspec(2, 3, width_ratios=[3, 1.2, 1.2],
                          height_ratios=[1, 1],
                          hspace=0.35, wspace=0.30,
                          left=0.04, right=0.97, top=0.93, bottom=0.06)

    ax_map   = fig.add_subplot(gs[:, 0])        # sol: harita
    ax_chart = fig.add_subplot(gs[0, 1:])       # sağ üst: enerji grafiği
    ax_stats = fig.add_subplot(gs[1, 1:])       # sağ alt: stats panel

    # ── Harita ──
    ax_map.set_facecolor('#0d1117')
    ax_map.set_xlim(-30, ALAN_W + 30)
    ax_map.set_ylim(-30, ALAN_H + 30)
    ax_map.set_aspect('equal')
    ax_map.set_xlabel('X (m)', color='white', fontsize=9)
    ax_map.set_ylabel('Y (m)', color='white', fontsize=9)
    ax_map.tick_params(colors='#666')

    # tarla
    tarla = plt.Rectangle((0, 0), ALAN_W, ALAN_H,
                           fill=True, facecolor='#0a1f0a', edgecolor='#2d5016',
                           linewidth=1.5, alpha=0.6)
    ax_map.add_patch(tarla)

    # grid
    for gx in range(0, ALAN_W+1, 100):
        ax_map.axvline(gx, color='#1a3a1a', lw=0.3)
    for gy in range(0, ALAN_H+1, 100):
        ax_map.axhline(gy, color='#1a3a1a', lw=0.3)

    # Sensör scatter & labels
    sensor_scatter = ax_map.scatter([], [], s=60, zorder=5,
                                     edgecolors='white', linewidth=0.4)
    sensor_texts = []
    for s in state.sensors:
        t = ax_map.text(s.xy[0], s.xy[1]-12, f'S{s.id}',
                        fontsize=5, color='#888', ha='center', va='top')
        sensor_texts.append(t)

    # Drone marker
    drone_marker, = ax_map.plot([], [], marker='v', color='#ff4757',
                                 markersize=14, markeredgecolor='white',
                                 markeredgewidth=1.5, zorder=20)
    # Drone menzil dairesi
    drone_circle = plt.Circle((0, 0), DRONE_MENZIL, fill=False,
                               color='#ff6b81', linestyle='--',
                               linewidth=0.8, alpha=0.4, zorder=15)
    ax_map.add_patch(drone_circle)

    # Drone izi
    trail_line, = ax_map.plot([], [], '-', color='#70a1ff', lw=1.0,
                               alpha=0.5, zorder=3)

    # Toplama çizgileri (lazer efekti)
    collect_lines_art = []

    # Drone ev işareti
    ax_map.plot(state.drone_home[0], state.drone_home[1], '^',
                color='#ffa502', markersize=12, markeredgecolor='white',
                markeredgewidth=1, zorder=10)
    ax_map.text(state.drone_home[0]+10, state.drone_home[1]+8, 'KALKIŞ',
                color='#ffa502', fontsize=7, fontweight='bold')

    # Baz istasyonu göster (referans)
    ax_map.plot(BAZ_XY[0], BAZ_XY[1], 's', color='#a55eea',
                markersize=10, markeredgecolor='white', markeredgewidth=1, zorder=10)
    ax_map.text(BAZ_XY[0]+10, BAZ_XY[1]+5, 'BAZ\n(Multi-hop)', color='#a55eea',
                fontsize=6, fontweight='bold')

    # ── Grafik ──
    ax_chart.set_facecolor('#0d1117')
    ax_chart.tick_params(colors='#888', labelsize=7)
    ax_chart.set_ylabel('Ort. Enerji (%)', color='white', fontsize=8)
    ax_chart.set_xlabel('Zaman (s)', color='white', fontsize=8)
    ax_chart.set_title('Enerji Karşılaştırması', color='white', fontsize=9, fontweight='bold')
    ax_chart.set_ylim(0, 105)
    ax_chart.grid(True, alpha=0.15, color='white')
    line_de, = ax_chart.plot([], [], '-', color='#70a1ff', lw=2, label='Drone')
    line_me, = ax_chart.plot([], [], '-', color='#ff6b6b', lw=2, label='Multi-hop')
    ax_chart.legend(fontsize=7, loc='lower left', facecolor='#1a1a2e',
                    edgecolor='#333', labelcolor='white')

    # ── Stats panel ──
    ax_stats.set_facecolor('#0d1117')
    ax_stats.set_xlim(0, 10); ax_stats.set_ylim(0, 10)
    ax_stats.axis('off')

    stats_text = ax_stats.text(0.5, 9.5, '', transform=ax_stats.transData,
                                fontsize=9, color='white', fontfamily='monospace',
                                verticalalignment='top', linespacing=1.8)

    # Başlık
    title_txt = fig.text(0.5, 0.97,
        'TARIM 5.0 — Mobil Baz İstasyonu (Drone/İHA) Canlı Simülasyon',
        ha='center', va='top', fontsize=13, fontweight='bold',
        color='#2ed573', fontfamily='monospace')

    time_txt = fig.text(0.04, 0.97, '', ha='left', va='top',
                         fontsize=10, color='#ffa502', fontfamily='monospace')

    # ─────────────────── UPDATE FONKSİYONU ───────────────────
    def update(frame):
        nonlocal collect_lines_art

        # Simülasyonu ilerlet
        for _ in range(SPEED):
            state.step(SIM_DT)

        t = state.t

        # ── Sensörleri güncelle ──
        xs = [s.xy[0] for s in state.sensors]
        ys = [s.xy[1] for s in state.sensors]
        colors = []
        sizes = []
        for s in state.sensors:
            if not s.alive:
                colors.append('#ff4757')  # kırmızı = ölü
                sizes.append(40)
            elif s.flash > 0:
                # Toplama animasyonu — parlak yeşil/beyaz
                brightness = min(1.0, s.flash / 1.5)
                r = int(46 + (255-46) * brightness)
                g = int(204 + (255-204) * brightness)
                b = int(113 + (255-113) * brightness)
                colors.append(f'#{r:02x}{g:02x}{b:02x}')
                sizes.append(60 + 80 * brightness)
            elif s.buf > SENSOR_BELLEK_MAX * 0.7:
                colors.append('#ffa502')  # turuncu = bellek dolu
                sizes.append(60)
            elif s.pct < 30:
                colors.append('#eccc68')  # sarı = düşük enerji
                sizes.append(55)
            else:
                colors.append('#2ed573')  # yeşil = sağlıklı
                sizes.append(55)

        offsets = np.column_stack([xs, ys])
        sensor_scatter.set_offsets(offsets)
        sensor_scatter.set_color(colors)
        sensor_scatter.set_sizes(sizes)

        # Sensör etiketlerini güncelle (enerji %)
        for i, s in enumerate(state.sensors):
            sensor_texts[i].set_text(f'{s.pct:.0f}%')
            sensor_texts[i].set_color('#ff4757' if not s.alive else '#aaa')

        # ── Drone ──
        drone_marker.set_data([state.drone_xy[0]], [state.drone_xy[1]])
        drone_circle.center = (state.drone_xy[0], state.drone_xy[1])

        # Drone izi
        if state.drone_trail:
            trail = np.array(state.drone_trail)
            trail_line.set_data(trail[:, 0], trail[:, 1])

        # Toplama laser çizgileri
        for art in collect_lines_art:
            art.remove()
        collect_lines_art = []
        for sxy, alpha in state.collect_lines:
            ln, = ax_map.plot([state.drone_xy[0], sxy[0]],
                              [state.drone_xy[1], sxy[1]],
                              '-', color='#7bed9f', lw=2, alpha=alpha*0.8, zorder=12)
            collect_lines_art.append(ln)

        # ── Enerji grafiği ──
        if state.hist_t:
            line_de.set_data(state.hist_t, state.hist_drone_e)
            line_me.set_data(state.hist_t, state.hist_mhop_e)
            ax_chart.set_xlim(0, max(state.hist_t[-1], 60))

        # ── İstatistikler ──
        d_alive = sum(1 for s in state.sensors if s.alive)
        m_alive = sum(1 for s in state.mh_sensors if s.alive)
        d_avg = np.mean([s.pct for s in state.sensors])
        m_avg = np.mean([s.pct for s in state.mh_sensors])
        d_min = min(s.pct for s in state.sensors)
        m_min = min(s.pct for s in state.mh_sensors)

        durum_map = {
            "wait": "[=] Bekliyor",
            "fly": "[>] Ucusta",
            "collect": "[*] Topluyor",
            "return_home": "[<] Eve Donus"
        }

        st = (
            f"{'─'*36}\n"
            f"   DRONE (Mobil Baz İstasyonu)\n"
            f"{'─'*36}\n"
            f"  Durum     : {durum_map.get(state.drone_state, state.drone_state)}\n"
            f"  Tur       : #{state.drone_tours}\n"
            f"  Toplanan  : {state.drone_collected} paket\n"
            f"  Mesafe    : {state.drone_total_dist:.0f} m\n"
            f"  Aktif     : {d_alive}/{SENSOR_N}\n"
            f"  Ort.Enerji: %{d_avg:.1f}  Min: %{d_min:.1f}\n"
            f"\n"
            f"{'─'*36}\n"
            f"   MULTI-HOP (Sabit Baz)\n"
            f"{'─'*36}\n"
            f"  Aktif     : {m_alive}/{SENSOR_N}\n"
            f"  Ort.Enerji: %{m_avg:.1f}  Min: %{m_min:.1f}\n"
            f"\n"
            f"{'─'*36}\n"
            f"  ⚡ Tasarruf: %{max(0, (100-d_avg)-(100-m_avg))*-1:.1f}\n"
        )

        # Tasarruf hesabı düzelt
        d_spent = 100 - d_avg
        m_spent = 100 - m_avg
        if m_spent > 0.1:
            saving = (m_spent - d_spent) / m_spent * 100
            ratio  = m_spent / max(d_spent, 0.01)
        else:
            saving = 0; ratio = 1

        st = (
            f"{'─'*34}\n"
            f"  DRONE (Mobil Baz)\n"
            f"{'─'*34}\n"
            f"  Durum      : {durum_map.get(state.drone_state,'?')}\n"
            f"  Tur        : #{state.drone_tours}\n"
            f"  Toplanan   : {state.drone_collected} paket\n"
            f"  Mesafe     : {state.drone_total_dist/1000:.1f} km\n"
            f"  Aktif      : {d_alive}/{SENSOR_N}\n"
            f"  Ort.Enerji : %{d_avg:.1f}\n"
            f"  Min.Enerji : %{d_min:.1f}\n"
            f"\n"
            f"{'─'*34}\n"
            f"  MULTI-HOP (Sabit Baz)\n"
            f"{'─'*34}\n"
            f"  Aktif      : {m_alive}/{SENSOR_N}\n"
            f"  Ort.Enerji : %{m_avg:.1f}\n"
            f"  Min.Enerji : %{m_min:.1f}\n"
            f"\n"
            f"{'─'*34}\n"
            f"  Enerji Tasarruf : %{saving:.1f}\n"
            f"  Omur Orani      : {ratio:.1f}x\n"
        )
        stats_text.set_text(st)

        # Zaman
        dakika = int(t) // 60
        saniye = int(t) % 60
        time_txt.set_text(f"T: {dakika:02d}:{saniye:02d}  ({SPEED}x)")

        # Harita başlığı
        ax_map.set_title(
            f'500m × 500m Tarım Alanı  |  {SENSOR_N} Sensör  |  Drone Tur #{state.drone_tours}',
            color='#2ed573', fontsize=9, fontfamily='monospace', pad=8)

        return (sensor_scatter, drone_marker, trail_line,
                line_de, line_me, stats_text, time_txt)

    # ─────────────────── BAŞLAT ───────────────────
    anim = FuncAnimation(fig, update, interval=1000//FPS,
                         blit=False, cache_frame_data=False)

    # Lejant (harita)
    legend_els = [
        mpatches.Patch(color='#2ed573', label='Aktif Sensör'),
        mpatches.Patch(color='#ffa502', label='Bellek Dolu'),
        mpatches.Patch(color='#eccc68', label='Düşük Enerji'),
        mpatches.Patch(color='#ff4757', label='Ölü Sensör'),
        plt.Line2D([0],[0], marker='v', color='w', markerfacecolor='#ff4757',
                   markersize=10, label='Drone'),
        plt.Line2D([0],[0], color='#70a1ff', lw=2, label='Drone İzi'),
    ]
    ax_map.legend(handles=legend_els, loc='upper right', fontsize=6,
                  facecolor='#1a1a2e', edgecolor='#333', labelcolor='white')

    plt.show()


# ═══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Tarım 5.0 — Canlı Simülasyon Başlatılıyor...")
    print("Pencereyi kapatarak durdurun.")
    run_animation()

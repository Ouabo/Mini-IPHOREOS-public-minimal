"""Build an overview video mapping Mini-IPHOREOS's existing toy-scale results
onto the EIC grant's own four objectives (O1-O4, read from
EIC_Objectives_Methodology/IPHOREOS_Section_1_3_Objectives_and_Methodology_Final3.docx).
Same technique as tools/make_ext1_video.py (PIL-rendered frames piped through
imageio_ffmpeg), reading traces already saved by experiments/run_simulation.py
and experiments/run_transfer_validation.py; no new simulation is run here,
except the one pair of Task-B traces prepared earlier this session
(results_transfer/trace_switch_{cold_start,zero_update_transfer}_seed10000.json).

O1-O4 describe the grant's eventual TRL4 demonstrator (shelf retrieval and
component sorting, on hardware). This toy wall-approach robot does not claim
to be that demonstrator. Every chapter below pairs its toy-scale evidence with
an explicit, load-bearing caveat about what that evidence does not establish,
the same discipline every other document in this project already follows.

Revision note: the first cut reused the same small "car approaching a wall"
panel in every chapter, so the only differences between O1-O4 were a few
words of caption text, unclear to a general audience. This version gives
each chapter its own large, distinct hero visual (a replication bar chart for
O1, an animated context meter for O2, a head-to-head scoreboard for O3, a
flashing rejection alert for O4) plus a consistent colour-coded badge, so the
chapters are visually distinguishable even without reading the captions.
"""
from pathlib import Path
import json, hashlib, math
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results_ext1'
TRANSFER = ROOT / 'results_transfer'
OUT = ROOT / 'Mini_IPHOREOS_EXT1_Video'
OUT.mkdir(exist_ok=True)


def load(base_dir, name):
    rows = json.loads((base_dir / name).read_text(encoding='utf-8'))
    for r in rows:
        r.setdefault('context_probabilities', {})
        r.setdefault('reason', r.get('realised_event', ''))
        r.setdefault('distance_sd', 0.6)
    return rows


TRACES = {
    'o1_normal': load(RESULTS, 'trace_normal_ext1.json'),
    'o2_switch_memory_fast': load(RESULTS, 'trace_switch_ext1_memory_fast.json'),
    'o3_cold_start': load(TRANSFER, 'trace_switch_cold_start_seed10000.json'),
    'o3_zero_update_transfer': load(TRANSFER, 'trace_switch_zero_update_transfer_seed10000.json'),
    'o4_outlier': load(RESULTS, 'trace_outlier_ext1.json'),
}

FONT = Path('C:/Windows/Fonts')


def font(n, bold=False):
    return ImageFont.truetype(str(FONT / ('arialbd.ttf' if bold else 'arial.ttf')), n)


BG = '#0b1425'; CARD = '#14233a'; CARD2 = '#192c48'; WHITE = '#eff5ff'; MUTED = '#a9bad1'
TEAL = '#49dbc3'; GOLD = '#ffcd70'; RED = '#ff7f88'; VIOLET = '#c6a6ff'
ACCENT = {'O1': TEAL, 'O2': GOLD, 'O3': VIOLET, 'O4': RED}


def text(draw, xy, t, size=24, color=WHITE, bold=False):
    draw.text(xy, t, font=font(size, bold), fill=color)


def ctext(draw, cx, y, t, size=24, color=WHITE, bold=False):
    f = font(size, bold)
    w = draw.textlength(t, font=f)
    draw.text((cx - w / 2, y), t, font=f, fill=color)


def lines(draw, xy, t, size=24, color=WHITE, gap=10):
    x, y = xy
    for line in t.split('\n'):
        text(draw, (x, y), line, size, color)
        y += size + gap


def badge(d, label):
    color = ACCENT[label]
    cx, cy, r = 1192, 46, 27
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    ctext(d, cx, cy - 13, label, 19, BG, True)


def base(obj, title, sub, chapter):
    im = Image.new('RGB', (1280, 720), BG)
    d = ImageDraw.Draw(im)
    text(d, (36, 23), 'MINI-IPHOREOS  /  TOY-SCALE EVIDENCE FOR THE GRANT\'S OBJECTIVES O1-O4', 15, TEAL, True)
    text(d, (36, 56), title, 29, WHITE, True)
    text(d, (36, 99), sub, 17, MUTED)
    text(d, (36, 684), 'Desktop simulation \u2022 synthetic traces \u2022 no physical validation', 16, MUTED)
    text(d, (1060, 684), chapter, 16, TEAL)
    if obj:
        badge(d, obj)
    return im, d


def row_at(rows, progress):
    elapsed = progress * rows[-1]['simulator_time']
    idx = max(i for i, r in enumerate(rows) if r['simulator_time'] <= elapsed + 1e-9)
    return idx, rows[idx]


def recent_flag(rows, idx, hold=5):
    for j in range(idx, max(-1, idx - hold), -1):
        event = str(rows[j].get('realised_event', ''))
        if event in ('unusable_reading', 'unexpected_outcome'):
            return event
    return None


LABEL = {'MOVE': 'MOVE', 'SAMPLE': 'MEASURE', 'DONE': 'DONE', 'ABORT': 'ABORT'}


def panel(d, box, title, rows, progress, target=25., band=4., accent=TEAL):
    x, y, w, h = box
    d.rounded_rectangle((x, y, x + w, y + h), 16, fill=CARD)
    text(d, (x + 18, y + 12), title, 16, WHITE, True)
    idx, r = row_at(rows, progress)
    left = x + 30; right = x + w - 30; scale = (right - left) / max(target * 3.6, 90)

    def sx(v):
        return right - v * scale

    sy = y + 92
    d.rectangle((sx(target + band), sy - 20, sx(target - band), sy + 22), fill='#20564e')
    d.line((right, sy - 28, right, sy + 27), fill=WHITE, width=4)
    rx = max(x + 34, sx(r['simulator_true_distance']))
    d.rounded_rectangle((rx - 32, sy - 13, rx, sy + 13), 4, fill=accent)
    text(d, (left, sy + 34), f"True: {r['simulator_true_distance']:.1f} cm (hidden)", 13, GOLD)

    mu, sd = r['estimated_distance'], r['distance_sd']
    text(d, (left, y + 148), f"Belief: {mu:.1f} \u00b1 {sd:.2f} cm", 15, accent, True)

    gx = left; gy = y + 178; gw = w - 60; gh = h - 250
    d.line((gx, gy + gh, gx + gw, gy + gh), fill=MUTED)
    tmax = max(rows[-1]['simulator_time'], .01)

    def point(j, v):
        return (gx + gw * rows[j]['simulator_time'] / tmax, gy + gh * (1 - (v - 10) / (target * 3.6)))

    if idx > 0:
        upper = [point(j, rows[j]['estimated_distance'] + 1.64 * rows[j]['distance_sd']) for j in range(idx + 1)]
        lower = [point(j, rows[j]['estimated_distance'] - 1.64 * rows[j]['distance_sd']) for j in range(idx, -1, -1)]
        d.polygon(upper + lower, fill='#21504e')
        d.line([point(j, rows[j]['simulator_true_distance']) for j in range(idx + 1)], fill=GOLD, width=2)
        d.line([point(j, rows[j]['estimated_distance']) for j in range(idx + 1)], fill=accent, width=2)

    action = r['intended_option']
    text(d, (left, y + h - 58), 'DECISION: ' + LABEL.get(action, action), 16, accent if action != 'ABORT' else RED, True)
    text(d, (left, y + h - 34), f"move {r.get('moves_completed', 0)}  \u2022  t = {r['simulator_time']:.1f}s", 12, MUTED)
    return r


def bar_chart(d, box, title, bars, unit, better):
    """bars: list of (label, value, color). `better` is 'low' or 'high'."""
    x, y, w, h = box
    d.rounded_rectangle((x, y, x + w, y + h), 16, fill=CARD)
    text(d, (x + 18, y + 14), title, 18, WHITE, True)
    maxv = max(v for _, v, _ in bars) * 1.25
    n = len(bars)
    gap = 40
    bw = (w - 2 * gap - gap * (n - 1)) / n
    base_y = y + h - 70
    top_y = y + 90
    for i, (label, v, color) in enumerate(bars):
        bx = x + gap + i * (bw + gap)
        bh = (base_y - top_y) * (v / maxv)
        d.rounded_rectangle((bx, base_y - bh, bx + bw, base_y), 8, fill=color)
        ctext(d, bx + bw / 2, base_y - bh - 34, f'{v:g}', 24, color, True)
        ctext(d, bx + bw / 2, base_y + 12, label, 14, MUTED)
    text(d, (x + 18, y + h - 26), f'Lower is better ({unit})' if better == 'low' else f'Higher is better ({unit})', 12, MUTED)


def context_meter(d, box, p_normal, p_slow, pulse_s):
    x, y, w, h = box
    d.rounded_rectangle((x, y, x + w, y + h), 16, fill=CARD)
    text(d, (x + 18, y + 14), 'Which regime is believed active?', 18, WHITE, True)
    bx, by, bw, bh = x + 30, y + 70, w - 60, 70
    nw = int(bw * p_normal)
    d.rounded_rectangle((bx, by, bx + bw, by + bh), 10, fill='#0e1c30')
    if nw > 4:
        d.rounded_rectangle((bx, by, bx + max(nw, 10), by + bh), 10, fill=TEAL)
    if bw - nw > 4:
        d.rounded_rectangle((bx + nw, by, bx + bw, by + bh), 10, fill=GOLD)
    ctext(d, bx + bw * 0.25, by + bh + 14, f'NORMAL  {p_normal*100:.0f}%', 16, TEAL, True)
    ctext(d, bx + bw * 0.75, by + bh + 14, f'SLOW  {p_slow*100:.0f}%', 16, GOLD, True)
    text(d, (x + 30, y + 210), f'Chosen pulse this decision: {pulse_s:.2f} s', 15, WHITE)
    text(d, (x + 30, y + 240), '(duration menu {0, 0.12, 0.24}s, cost-weighted against information gained)', 13, MUTED)
    text(d, (x + 30, y + h - 40), 'The non-active hypothesis is never discarded; its weight can still recover.', 13, MUTED)


def scoreboard(d, box, left_label, left_v, right_label, right_v, caption):
    x, y, w, h = box
    d.rounded_rectangle((x, y, x + w, y + h), 16, fill=CARD)
    cx = x + w / 2
    ctext(d, x + w * 0.27, y + 18, str(left_v), 54, RED, True)
    ctext(d, x + w * 0.73, y + 18, str(right_v), 54, TEAL, True)
    ctext(d, cx, y + 40, '\u2192', 40, MUTED, True)
    ctext(d, x + w * 0.27, y + 84, left_label, 15, MUTED)
    ctext(d, x + w * 0.73, y + 84, right_label, 15, MUTED)
    ctext(d, cx, y + h - 34, caption, 15, GOLD)


def alert_panel(d, box, flagged):
    x, y, w, h = box
    if flagged:
        d.rounded_rectangle((x, y, x + w, y + h), 16, fill='#4a1420', outline=RED, width=5)
        ctext(d, x + w / 2, y + 60, 'READING REJECTED', 24, RED, True)
        ctext(d, x + w / 2, y + 100, flagged.replace('_', ' '), 16, WHITE)
        text(d, (x + 30, y + 160), 'The innovation-rejection gate caught this reading before it reached the belief:', 14, WHITE)
        text(d, (x + 30, y + 186), 'it is more than 5 standardised errors from what the filter expected.', 14, WHITE)
    else:
        d.rounded_rectangle((x, y, x + w, y + h), 16, fill=CARD)
        ctext(d, x + w / 2, y + 60, 'SAFETY CHECK ACTIVE', 22, TEAL, True)
        text(d, (x + 30, y + 110), 'Verification margin: |belief - target| + 1.64 sigma <= band', 14, WHITE)
        text(d, (x + 30, y + 140), 'Overshoot-risking action sequences are excluded from planning', 14, WHITE)
        text(d, (x + 30, y + 166), 'outright, not just cost-penalised.', 14, WHITE)
    text(d, (x + 30, y + h - 36), 'Every decision is logged: intended option, reason, realised event.', 13, MUTED)


def frame(t):
    if t < 10:
        im, d = base(None, "Toy-scale preliminary evidence for the grant's four objectives",
                      'O1-O4 describe the eventual TRL4 demonstrator (shelf retrieval + component sorting, on hardware).', '0 / 5')
        lines(d, (65, 160),
              'This toy robot approaches a cardboard wall in simulation.\n'
              'It is a small-scale precursor, not a claim of satisfying O1-O4.',
              26, WHITE, 14)
        lines(d, (65, 280),
              'Each objective below gets its own colour, its own visual,\n'
              'the grant\'s own language, the toy-scale evidence this\nproject already has, and what that evidence does not establish.',
              22, TEAL, 16)
    elif t < 55:
        im, d = base('O1', 'O1  /  Learn grounded concepts and events', 'Held-out prediction with calibrated uncertainty, not just a point estimate.', '1 / 5')
        p = min(1, (t - 10) / 40)
        panel(d, (55, 140, 560, 420), 'ext1, calibrated belief, live', TRACES['o1_normal'], p, accent=TEAL)
        bar_chart(d, (655, 140, 560, 420), 'Frozen held-out replication (Milestone 4)',
                  [('Dev (10000-10099)', 3.3, TEAL), ('Held-out (50000-50099)', 3.2, GOLD)],
                  'decisions, memory+fast reconvergence', 'low')
        lines(d, (65, 592),
              'Toy evidence: calibrated uncertainty throughout (shaded band, not a bare number), an explicit\n'
              'concept/event vocabulary, and this frozen replication, never re-tuned on the held-out seeds.',
              15, GOLD, 6)
        lines(d, (65, 645), 'Not established at this scale: entities/relations beyond training appearances, or a matched unstructured-representation baseline.', 13, MUTED, 4)
    elif t < 100:
        im, d = base('O2', 'O2  /  Infer context and allocate computation', 'A compact, selectively-activated hypothesis set that can still recover excluded information.', '2 / 5')
        p = min(1, (t - 55) / 40)
        r = panel(d, (55, 140, 560, 420), 'ext1_memory_fast, belief, live', TRACES['o2_switch_memory_fast'], p, accent=GOLD)
        probs = r['context_probabilities']
        ps = probs.get('slow', 0.) or 0.
        context_meter(d, (655, 140, 560, 420), 1 - ps, ps, r.get('pulse_seconds', 0.) or 0.)
        lines(d, (65, 592),
              'Toy evidence: belief mass concentrates on the active hypothesis without discarding the\n'
              'other; a change-point detector decides when to re-weight; cost is traded against information.',
              15, GOLD, 6)
        lines(d, (65, 645), 'Not established at this scale: hardware-level latency, memory or energy; only logical decisions and a simulated pulse cost.', 13, MUTED, 4)
    elif t < 150:
        im, d = base('O3', 'O3  /  Recompose knowledge for adaptive planning', 'Transfer a library learned on one goal to a different goal, with a persistent, unseen bias.', '3 / 5')
        p = min(1, (t - 100) / 38)
        panel(d, (55, 140, 560, 330), 'Cold start (no transfer)', TRACES['o3_cold_start'], p, target=85., band=4., accent=RED)
        panel(d, (655, 140, 560, 330), 'Zero-update transfer (seeded from Task A)', TRACES['o3_zero_update_transfer'], p, target=85., band=4., accent=TEAL)
        scoreboard(d, (55, 490, 1160, 130), 'Cold start', 5, 'Zero-update transfer', 4,
                   'Decisions to recognise the switch, this seed')
        lines(d, (65, 638), 'Averaged over 100 deployments: 5.20 vs 3.79-3.85 decisions, transfer faster in 61, tied in 32, slower in 7. Overall success/moves unchanged.', 13, MUTED, 4)
    elif t < 195:
        im, d = base('O4', 'O4  /  Establish bounded trustworthiness', 'Calibrated beliefs, an independently enforced constraint, and a faithful decision record.', '4 / 5')
        p = min(1, (t - 150) / 38)
        idx, r = row_at(TRACES['o4_outlier'], p)
        panel(d, (55, 140, 560, 420), 'ext1, outlier scenario, live', TRACES['o4_outlier'], p, accent=RED)
        flagged = recent_flag(TRACES['o4_outlier'], idx, hold=5)
        alert_panel(d, (655, 140, 560, 420), flagged)
        lines(d, (65, 592),
              'Toy evidence: an uncertainty-aware verification rule, a hard overshoot-margin exclusion\n'
              'enforced independently of the cost score, and this project\'s own full decision audit trail.',
              15, GOLD, 6)
        lines(d, (65, 645), 'NOT ESTABLISHED: hardware testing. No physical robot has been built or run; this evidence covers the trust mechanisms only.', 13, RED, 4)
    else:
        im, d = base(None, 'What this evidence is, and is not', 'Four objectives, four toy-scale results, one open gap.', '5 / 5')
        lines(d, (65, 160),
              'O1  Calibrated, held-out-replicated prediction with an explicit concept/event log.\n'
              'O2  A compact, non-discarding context hypothesis + cost-aware computation.\n'
              'O3  A learned library transferring across a changed goal (the Transfer system).\n'
              'O4  Calibrated beliefs, an enforced constraint, a faithful decision record.',
              22, TEAL, 14)
        lines(d, (65, 420),
              'None of this is the TRL4 demonstrator: two real task contexts, hardware,\n'
              'and physical validation remain entirely separate and not yet attempted.',
              22, GOLD, 14)
        lines(d, (65, 540), 'Full derivations: Mathematical_Model_EXT1.pdf. Narrative: Tutorial_EXT1_EN.pdf.', 18, MUTED, 10)
    return im


fps = 12; duration = 205
writer = imageio_ffmpeg.write_frames(str(OUT / 'O1_O4_Overview_EN.mp4'), (1280, 720), fps=fps,
                                      codec='libx264', pix_fmt_in='rgb24', pix_fmt_out='yuv420p',
                                      quality=7, macro_block_size=16)
writer.send(None)
for i in range(duration * fps):
    im = frame(i / fps)
    writer.send(im.tobytes())
    if i in (60, 360, 900, 1500, 2160, 2400):
        im.save(OUT / f'preview_o1o4_EN_{i // fps}s.png')
    if i % (fps * 30) == 0:
        print(f'Video: {i // fps}/{duration}s', flush=True)
writer.close()

source_files = [ROOT / 'cognitive/controller.py', ROOT / 'cognitive/model.py',
                ROOT / 'cognitive/baselines.py', ROOT / 'experiments/run_transfer_validation.py']
manifest = {
    'duration_seconds': duration, 'fps': fps, 'resolution': [1280, 720],
    'source_sha256': {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in source_files},
    'traces_used': {
        'o1_normal': 'results_ext1/trace_normal_ext1.json',
        'o2_switch_memory_fast': 'results_ext1/trace_switch_ext1_memory_fast.json',
        'o3_cold_start': 'results_transfer/trace_switch_cold_start_seed10000.json',
        'o3_zero_update_transfer': 'results_transfer/trace_switch_zero_update_transfer_seed10000.json',
        'o4_outlier': 'results_ext1/trace_outlier_ext1.json',
    },
    'notes': ('Silent English-captioned desktop simulation mapping Mini-IPHOREOS\'s existing '
              'toy-scale results onto the EIC grant\'s own O1-O4 objective language '
              '(EIC_Objectives_Methodology/IPHOREOS_Section_1_3_Objectives_and_Methodology_Final3.docx). '
              'This does not claim the toy wall-approach robot satisfies O1-O4 at TRL4 scale; '
              'every chapter states its scope limit on screen. Revised from the first cut so each '
              'objective has its own large, distinct visual (replication bars / context meter / '
              'scoreboard / rejection alert) and colour badge, not a reused generic panel. '
              'The O3 chapter uses seed 10000 (deployment_factor~0.808), the case closest to the '
              'published paired-mean effect, not a cherry-picked best case. No physical robot data '
              'or hardware validation is presented.')
}
(OUT / 'manifest_o1o4_EN.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print('O1-O4 overview video complete', flush=True)

"""Build the EXT1 bias-reference + frozen held-out evaluation explanatory
video (Milestones 3-4). Same technique as tools/make_ext1_memory_video.py
(PIL-rendered frames piped through imageio_ffmpeg), reading traces already
saved in results_ext1/ by experiments/run_simulation.py (seed 10000) -- no
new simulation is run here.

Revision note: on-screen text was rewritten for an audience that has not
read the surrounding project documents (investor/reviewer screening), and
every double-hyphen/em-dash was removed from spoken captions in favour of
plain sentences, per explicit request. Code-level identifiers (policy names,
file paths, variable names) are kept only as small secondary labels next to
a plain-English description, never as the primary on-screen phrase. No
number, threshold, or finding was changed -- only how it is phrased.

Four findings are shown, each backed by the 100-trial numbers already
published in Tutorial_EXT1_EN.pdf / Mathematical_Model_EXT1.pdf, not read
off the single illustrative trial on screen:
  1. A constant sensor bias and a slower robot are indistinguishable from
     decisions alone -- the distance/bias confound.
  2. An explicit reference reading at a known distance breaks the confound
     (REF_DISTANCE=50cm, N_REF=5, taken once before the approach begins).
  3. Milestone 4 freezes every tunable constant and re-runs the full battery
     on seeds 50000-50099, never touched during development or tuning.
  4. The new outlier-reading scenario is reported honestly, including the
     one place the bias reference does slightly worse (a higher abort rate
     under an unlucky first-reading outlier), not just where it wins.
"""
from pathlib import Path
import json, hashlib
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results_ext1'
OUT = ROOT / 'Mini_IPHOREOS_EXT1_Video'
OUT.mkdir(exist_ok=True)


def load(name):
    rows = json.loads((RESULTS / name).read_text(encoding='utf-8'))
    for r in rows:
        r.setdefault('context_probabilities', {})
    return rows


TRACE_NAMES = {
    'bias_ext1': 'trace_bias_ext1.json', 'bias_ext1_bias_ref': 'trace_bias_ext1_bias_ref.json',
    'bias_random_ext1': 'trace_bias_random_ext1.json', 'bias_random_ext1_bias_ref': 'trace_bias_random_ext1_bias_ref.json',
    'outlier_ext1': 'trace_outlier_ext1.json',
}
TRACES = {k: load(v) for k, v in TRACE_NAMES.items()}

FONT = Path('C:/Windows/Fonts')


def font(n, bold=False):
    return ImageFont.truetype(str(FONT / ('arialbd.ttf' if bold else 'arial.ttf')), n)


BG = '#0b1425'; CARD = '#14233a'; WHITE = '#eff5ff'; MUTED = '#a9bad1'
TEAL = '#49dbc3'; GOLD = '#ffcd70'; RED = '#ff7f88'; VIOLET = '#c6a6ff'


def text(draw, xy, t, size=24, color=WHITE, bold=False):
    draw.text(xy, t, font=font(size, bold), fill=color)


def lines(draw, xy, t, size=24, color=WHITE, gap=10):
    x, y = xy
    for line in t.split('\n'):
        text(draw, (x, y), line, size, color)
        y += size + gap


def base(title, sub, chapter):
    im = Image.new('RGB', (1280, 720), BG)
    d = ImageDraw.Draw(im)
    text(d, (36, 23), 'MINI-IPHOREOS EXTENDED SYSTEM  /  BIAS REFERENCE & HELD-OUT EVALUATION, MILESTONES 3-4', 15, TEAL, True)
    text(d, (36, 56), title, 29, WHITE, True)
    text(d, (36, 99), sub, 17, MUTED)
    text(d, (36, 684), 'Desktop simulation \u2022 synthetic traces \u2022 no physical validation', 16, MUTED)
    text(d, (1060, 684), chapter, 16, TEAL)
    return im, d


def interp_row(rows, times, clock):
    if clock <= times[0]:
        return rows[0], rows[0]['simulator_true_distance']
    for i in range(1, len(times)):
        if clock <= times[i]:
            r0, r1 = rows[i - 1], rows[i]
            t0, t1 = times[i - 1], times[i]
            frac = 0. if t1 == t0 else (clock - t0) / (t1 - t0)
            dist = r0['simulator_true_distance'] + frac * (r1['simulator_true_distance'] - r0['simulator_true_distance'])
            return r0, dist
    return rows[-1], rows[-1]['simulator_true_distance']


MAX_DIST = 130.


def car_panel(d, box, title, key, progress, glitch_at=()):
    rows = TRACES[key]
    times = [r['simulator_time'] for r in rows]
    x, y, w, h = box
    d.rounded_rectangle((x, y, x + w, y + h), 16, fill=CARD)
    text(d, (x + 20, y + 14), title, 19, WHITE, True)

    clock = progress * times[-1]
    r, dist = interp_row(rows, times, clock)

    left = x + 36; right = x + w - 36; scale = (right - left) / MAX_DIST
    def sx(v): return right - v * scale

    road_y = y + 148
    d.rectangle((sx(29), road_y - 26, sx(21), road_y + 30), fill='#20564e')
    d.line((right, road_y - 42, right, road_y + 42), fill=WHITE, width=6)
    d.line((left, road_y + 48, right, road_y + 48), fill='#243150', width=2)

    est_d = r.get('estimated_distance'); true_d = r.get('simulator_true_distance')
    recent_glitch = any(0 <= clock - gt < 0.7 for gt in glitch_at)
    if recent_glitch:
        halo = VIOLET
    elif est_d is not None and true_d is not None and abs(est_d - true_d) < 3.0:
        halo = TEAL
    else:
        halo = RED

    cx = sx(max(0., dist))
    if recent_glitch:
        d.ellipse((cx - 66, road_y - 46, cx + 20, road_y + 46), outline=VIOLET, width=4)
    d.rounded_rectangle((cx - 42, road_y - 16, cx, road_y + 16), 5, fill=GOLD)
    d.ellipse((cx - 36, road_y - 22, cx - 22, road_y - 10), fill=MUTED)
    d.ellipse((cx - 36, road_y + 10, cx - 22, road_y + 22), fill=MUTED)

    reading = r.get('reading')
    text(d, (x + 20, y + 206), f"Sensor says: {reading:.1f} cm" if reading is not None else "Sensor says: (rejected)", 15, GOLD, True)
    text(d, (x + 20, y + 232), f"Belief: {est_d:.1f} cm   Truth: {true_d:.1f} cm" if est_d is not None else "Belief: not available", 15, halo, True)
    if recent_glitch:
        text(d, (x + 20, y + 258), 'SENSOR GLITCH: rejected by the sanity check', 15, VIOLET, True)
    else:
        err = abs(est_d - true_d) if est_d is not None and true_d is not None else None
        text(d, (x + 20, y + 258), f"Gap from the truth: {err:.1f} cm" if err is not None else '', 14, MUTED)
    text(d, (x + 20, y + h - 30), f"Time: {clock:.1f}s of {times[-1]:.1f}s   \u2022   action: {r['intended_option']}", 13, MUTED)
    return r


def ref_jig(d, box):
    x, y, w, h = box
    d.rounded_rectangle((x, y, x + w, y + h), 16, fill=CARD)
    text(d, (x + 24, y + 18), 'THE REFERENCE CHECK', 19, GOLD, True)
    rx0, rx1, ry = x + 60, x + w - 60, y + 150
    d.line((rx0, ry, rx1, ry), fill=WHITE, width=4)
    d.polygon([(rx0, ry), (rx0 + 14, ry - 8), (rx0 + 14, ry + 8)], fill=WHITE)
    d.polygon([(rx1, ry), (rx1 - 14, ry - 8), (rx1 - 14, ry + 8)], fill=WHITE)
    text(d, ((rx0 + rx1) // 2 - 85, ry - 36), 'Known distance: 50 cm', 16, WHITE, True)
    cx0 = (rx0 + rx1) / 2
    offsets = [-32, -14, 3, 17, 34]
    xs = [cx0 + o for o in offsets]
    for i, px in enumerate(xs):
        d.ellipse((px - 7, ry + 40 - 7, px + 7, ry + 40 + 7), fill=TEAL)
        text(d, (px - 5, ry + 58), str(i + 1), 13, MUTED)
    mean_x = sum(xs) / len(xs)
    d.line((mean_x, ry + 30, mean_x, ry + 90), fill=GOLD, width=3)
    lines(d, (x + 24, y + h - 70), '5 readings taken at a KNOWN distance, once before\nthe approach begins (5 extra decisions, about 0.75 seconds).', 15, WHITE, 6)
    text(d, (x + 24, y + h - 30), 'Average of the 5 readings, minus 50 cm, gives the sensor\'s bias estimate.', 15, TEAL)


def frame(t):
    if t < 15:
        im, d = base('Two things look identical from decisions alone',
                      'A robot that reads 5 cm short, and a robot that is simply a little slow.', '1 / 7')
        lines(d, (65, 155),
              'THE PROBLEM\nEvery earlier milestone estimated distance purely from\n'
              'the ultrasonic reading itself. A constant sensor offset\n'
              'and a genuinely different speed both just look like\n'
              '"the numbers came in a bit different than expected."',
              24, WHITE, 13)
        lines(d, (65, 355),
              'WHY IT MATTERS\nAn earlier test already showed the real cost: success fell\n'
              'from about 97-98 percent (normal conditions) to 86 percent\n'
              'under a steady 5cm sensor bias, and to 53 percent when\n'
              'that bias changed randomly every trial. The robot was\n'
              'never told the bias was there.',
              22, TEAL, 13)
        lines(d, (65, 590), 'The fix needs information the sensor alone cannot give: a known distance.', 20, GOLD, 13)
    elif t < 32:
        im, d = base('An explicit reference check, taken once', 'A short detour to a known distance before the real approach starts.', '2 / 7')
        ref_jig(d, (140, 140, 1000, 330))
        text(d, (160, 500), 'This is new ground truth the system never had before: not "trust the sensor",', 18, WHITE)
        text(d, (160, 528), 'but "check the sensor against something we already know."', 18, WHITE)
        text(d, (160, 575), 'That check is applied to every later reading in the approach,', 16, MUTED)
        text(d, (160, 598), 'correcting the robot\'s distance and speed estimate as it moves.', 16, MUTED)
    elif t < 62:
        im, d = base('Constant bias: without the fix, and with it', 'Same steady 5cm sensor offset in both cases. Watch the belief reading, not the car, drift on the left.', '3 / 7')
        p = min(1, (t - 32) / 28)
        car_panel(d, (25, 150, 605, 340), 'Without the fix (ext1)', 'bias_ext1', p)
        car_panel(d, (650, 150, 605, 340), 'With the fix (ext1_bias_ref)', 'bias_ext1_bias_ref', p)
        text(d, (65, 660), '100 trials: success rises from 86% to 99%. The belief on the left stays about 5cm off the whole time, which is not random noise.', 15, GOLD)
    elif t < 97:
        im, d = base('Random bias: the harder case', 'Each trial gets its own fixed offset somewhere between -8 and +8 cm, so no two trials match.', '4 / 7')
        p = min(1, (t - 62) / 33)
        car_panel(d, (25, 150, 605, 340), 'Without the fix (ext1)', 'bias_random_ext1', p)
        car_panel(d, (650, 150, 605, 340), 'With the fix (ext1_bias_ref)', 'bias_random_ext1_bias_ref', p)
        text(d, (65, 660), '100 trials: success rises from 53% to 99%. Without the reference check, random bias is close to a coin flip.', 15, GOLD)
    elif t < 110:
        im, d = base('Milestone 4: freeze everything, then look at new data', 'Nothing shown so far was tuned using what you are about to see.', '5 / 7')
        lines(d, (65, 165),
              'THE DISCIPLINE\nEvery internal setting used above, how fast the robot reacts\n'
              'to change, how much it trusts memory, how the reference check\n'
              'works, was written down and locked in place before this test\n'
              'ran. None of it was adjusted afterward.',
              23, WHITE, 13)
        lines(d, (65, 380),
              'THE TEST\nA fresh batch of 100 random test cases that nobody had\n'
              'seen during three milestones of development. Same 9\n'
              'strategies, same 10 test scenarios, same code, only the\n'
              'randomness is new.',
              23, TEAL, 13)
    elif t < 140:
        im, d = base('New test: a sensor that occasionally lies', 'A reading that shows up and looks plausible, but is badly wrong. Different from a dropout, where no reading arrives.', '6 / 7')
        p = min(1, (t - 110) / 30)
        car_panel(d, (330, 150, 620, 340), 'Standard version facing a bad reading (ext1)', 'outlier_ext1', p, glitch_at=(7.19, 8.07))
        text(d, (160, 510), 'Two sudden errors, each 15 to 20cm off, hit this trial. The robot\'s own', 17, WHITE)
        text(d, (160, 536), 'sanity check catches both, and the belief barely moves. Reported honestly, not just the win:', 17, WHITE)
        text(d, (160, 580), 'Across 100 trials, most strategies, including the memory-based ones,', 15, GOLD)
        text(d, (160, 604), 'stay at 97-98% success. The bias-corrected one dips slightly to 95%', 15, GOLD)
        text(d, (160, 628), '(it aborts 5% of the time versus 2%), since being more confident after', 15, GOLD)
        text(d, (160, 652), 'calibration makes it quicker to reject a reading, even a real one.', 15, GOLD)
    else:
        im, d = base('What Milestones 3-4 established', 'All six items from the original improvement plan are now addressed.', '7 / 7')
        lines(d, (65, 160),
              'REPLICATION: ORIGINAL TEST CASES vs A FRESH, UNSEEN BATCH\n'
              'The efficient strategy still uses about half as many moves (54%)\n'
              'as the basic one, in both tests.\n'
              'Strategies with no active information-seeking: 100% success, in both tests.\n'
              'Memory with fast recognition needs about 3.2-3.3 decisions on repeat\n'
              'visits versus 4.6-4.9 without it, in both tests.\n'
              'The bias fix recovers success from 52-86% up to 99-100%, in both tests.',
              18, TEAL, 8)
        lines(d, (65, 400),
              'THE HONEST PART\nEvery headline claim held up on data never used to\n'
              'tune anything. The new sensor-glitch test is purely\n'
              'descriptive, including the one place the bias fix does\n'
              'slightly worse, not just where it wins.',
              22, WHITE, 12)
        lines(d, (65, 580), 'Still entirely open: testing on a real, physical robot. See the companion presentation for that plan.', 18, GOLD, 12)
    return im


fps = 12; duration = 170
writer = imageio_ffmpeg.write_frames(str(OUT / 'EXT1_BiasHeldout_Explanation_EN.mp4'), (1280, 720), fps=fps,
                                      codec='libx264', pix_fmt_in='rgb24', pix_fmt_out='yuv420p',
                                      quality=7, macro_block_size=16)
writer.send(None)
for i in range(duration * fps):
    im = frame(i / fps)
    writer.send(im.tobytes())
    if i in (60, 240, 480, 780, 1140, 1500, 1860):
        im.save(OUT / f'preview_biasheldout_EN_{i // fps}s.png')
    if i % (fps * 30) == 0:
        print(f'Video: {i // fps}/{duration}s', flush=True)
writer.close()

source_files = [ROOT / 'cognitive/model.py', ROOT / 'cognitive/controller.py', ROOT / 'experiments/run_simulation.py',
                ROOT / 'docs/FROZEN_PARAMETERS.md']
manifest = {
    'duration_seconds': duration, 'fps': fps, 'resolution': [1280, 720],
    'source_sha256': {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in source_files},
    'traces_used': TRACE_NAMES,
    'notes': ('Silent English-captioned desktop simulation covering Milestones 3 (explicit '
              'sensor-bias reference) and 4 (frozen held-out evaluation + outlier scenario). '
              'Revised for an investor/reviewer audience: no em-dashes or double-hyphens in '
              'captions, and code-level identifiers (policy names, file paths, internal variable '
              'names) appear only as small secondary labels next to a plain-English description, '
              'never as the primary phrase. The robot\'s on-screen position is driven by '
              'simulator_true_distance/simulator_time from seed-10000 traces (unmodified); the '
              'belief halo (red/teal/violet) reports estimated_distance vs simulator_true_distance, '
              'which is where the bias/reference story actually lives. The outlier glitch times '
              "(7.19s, 8.07s) are the real 'unexpected_outcome' events in trace_outlier_ext1.json, "
              'not added for effect. Every aggregate number spoken in captions (success rates, the '
              '54% move ratio, reconvergence decisions, bias estimate errors, the dev-vs-held-out '
              'replication figures) is read from results_ext1/{summary,reconvergence_summary,'
              'bias_reference_summary,outlier_summary}.csv and results_ext1_heldout/ via '
              'experiments/compare_heldout.py, not read off the single illustrative trial shown. '
              'No physical robot data or hardware validation is presented.')
}
(OUT / 'manifest_biasheldout_EN.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print('EXT1 bias/held-out video complete', flush=True)

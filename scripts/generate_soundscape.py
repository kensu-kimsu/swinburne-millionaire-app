"""Generate the original Cyber Dungeon sound set using only Python stdlib."""

import math
import random
import struct
import wave
from pathlib import Path

RATE = 22050
OUT = Path(__file__).resolve().parents[1] / "static" / "assets" / "audio"
random.seed(404)


def env(t, duration, attack=0.02, release=0.18):
    return min(1, t / max(attack, 0.001), (duration - t) / max(release, 0.001))


def tone(freq, duration, volume=.35, kind="sine", sweep=0, attack=.02, release=.18):
    data = []
    phase = 0.0
    for i in range(int(RATE * duration)):
        t = i / RATE
        f = max(20, freq + sweep * (t / duration))
        phase += 2 * math.pi * f / RATE
        if kind == "square":
            value = 1 if math.sin(phase) >= 0 else -1
        elif kind == "saw":
            value = 2 * ((phase / (2 * math.pi)) % 1) - 1
        else:
            value = math.sin(phase)
        data.append(value * volume * max(0, env(t, duration, attack, release)))
    return data


def noise(duration, volume=.25, release=.15, lowpass=0.16):
    data, previous = [], 0.0
    for i in range(int(RATE * duration)):
        t = i / RATE
        raw = random.uniform(-1, 1)
        previous += (raw - previous) * lowpass
        data.append(previous * volume * max(0, env(t, duration, .005, release)))
    return data


def silence(duration):
    return [0.0] * int(RATE * duration)


def mix(*tracks):
    length = max(map(len, tracks))
    result = [0.0] * length
    for track in tracks:
        for i, value in enumerate(track):
            result[i] += value
    peak = max(1.0, max(abs(v) for v in result) / .92)
    return [v / peak for v in result]


def sequence(*tracks):
    result = []
    for track in tracks:
        result.extend(track)
    return result


def delayed(track, seconds):
    return silence(seconds) + track


def write(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(RATE)
        file.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v)) * 32767)) for v in data))


def midi(number):
    return 440 * (2 ** ((number - 69) / 12))


def add_at(target, track, start):
    offset = int(start * RATE)
    for index, value in enumerate(track):
        if offset + index < len(target):
            target[offset + index] += value


def adventure_theme(chords, melody, bpm=120, intensity=1.0, wave="square"):
    """Build a seamless cyber-fantasy battle loop from original note patterns."""
    beat = 60 / bpm
    duration = len(chords) * 4 * beat
    score = [0.0] * int(duration * RATE)
    for bar, chord in enumerate(chords):
        start = bar * 4 * beat
        for note_number in chord:
            add_at(score, tone(midi(note_number), 4 * beat, .035 * intensity, "sine", attack=.08, release=.28), start)
        for step in range(8):
            note_number = chord[step % len(chord)] + (12 if step >= 4 else 0)
            add_at(score, tone(midi(note_number), beat * .43, .05 * intensity, wave, release=.08), start + step * beat / 2)
    for step, note_number in enumerate(melody):
        add_at(score, tone(midi(note_number), beat * .78, .075 * intensity, "saw" if intensity > 1.1 else "sine", release=.12), step * beat)
    for step in range(len(chords) * 4):
        add_at(score, tone(52 if step % 4 == 0 else 65, beat * .22, .12 * intensity, "sine", sweep=-20, release=.12), step * beat)
        if step % 2:
            add_at(score, noise(beat * .12, .045 * intensity, .08, .5), step * beat)
    peak = max(1.0, max(abs(value) for value in score) / .86)
    return [value / peak for value in score]


def main():
    write("ui_select", mix(tone(520, .09, .2, "square", sweep=130, release=.035), delayed(tone(780, .08, .12), .035)))
    write("ui_confirm", mix(tone(420, .18, .25, sweep=260, release=.08), delayed(tone(840, .16, .18), .08)))
    write("lock_in", mix(tone(105, .48, .32, "saw", sweep=-25), tone(210, .38, .18, sweep=80), noise(.22, .16)))
    write("correct", mix(tone(523, .55, .23), delayed(tone(659, .45, .23), .11), delayed(tone(784, .42, .2), .22)))
    write("wrong", mix(tone(190, .7, .3, "saw", sweep=-100), delayed(tone(125, .55, .25), .08), noise(.32, .2)))
    write("player_attack", mix(noise(.34, .42, .22, .35), tone(190, .42, .25, "saw", sweep=650, release=.08)))
    write("enemy_attack", mix(noise(.48, .5, .3, .24), tone(150, .5, .34, "saw", sweep=-95), delayed(tone(70, .35, .35), .12)))
    write("defend", mix(tone(280, .65, .25, sweep=-80), delayed(tone(560, .45, .2), .04), noise(.18, .32, .4)))
    write("exploit", mix(tone(72, 1.25, .36, "saw", sweep=1050), delayed(tone(880, .62, .28), .32), delayed(tone(1320, .38, .18), .53), delayed(noise(.7, .55, .35, .46), .42)))
    write("warning", sequence(mix(tone(245, .18, .32, "saw"), tone(490, .18, .12)), silence(.08), mix(tone(190, .24, .34, "saw"), tone(380, .24, .12))))
    write("fatal", sequence(*[mix(tone(freq, .22, .38, "saw"), tone(freq / 2, .22, .22)) for freq in (180, 135, 90)]))
    write("heal", mix(tone(392, .85, .2, sweep=180), delayed(tone(659, .62, .18), .18), delayed(tone(988, .42, .12), .36)))
    write("item", mix(tone(330, .7, .2, sweep=330), delayed(tone(990, .25, .16), .35), noise(.12, .12)))
    write("loot", mix(tone(440, .8, .18), delayed(tone(660, .65, .2), .12), delayed(tone(880, .5, .22), .24), delayed(tone(1320, .3, .13), .38)))
    victory = sequence(
        mix(tone(262, .55, .19), tone(330, .55, .16), tone(392, .55, .16)),
        mix(tone(349, .55, .19), tone(440, .55, .16), tone(523, .55, .16)),
        mix(tone(392, 1.3, .21), tone(494, 1.3, .18), tone(587, 1.3, .17), delayed(tone(784, .8, .13), .2)),
    )
    write("victory", victory)
    write("defeat", mix(tone(220, 2.1, .24, "saw", sweep=-150, release=.7), delayed(tone(110, 1.7, .23), .25), delayed(noise(.5, .12, .4), .2)))

    # Enemy techniques each have a unique elemental audio signature.
    write("skill_heavy", mix(tone(62, .9, .52, "saw", sweep=-28), delayed(noise(.55, .6, .35, .52), .12), delayed(tone(35, .65, .45), .2)))
    write("skill_fortify", mix(tone(240, .9, .25, sweep=-80), tone(480, .7, .18), delayed(noise(.16, .42, .12, .7), .06)))
    write("skill_heal", mix(tone(350, 1.0, .18, sweep=520), delayed(tone(700, .65, .2), .2), delayed(tone(1050, .35, .15), .48)))
    write("skill_drain", mix(tone(620, .75, .22, "square", sweep=-480), delayed(tone(180, .7, .25, "saw"), .2), noise(.22, .16)))
    write("skill_jam", mix(tone(110, .9, .28, "square", sweep=900), delayed(noise(.7, .45, .2, .7), .1), delayed(tone(70, .5, .3, "saw"), .42)))
    write("skill_encrypt", mix(tone(880, .85, .2, sweep=-620), delayed(tone(1320, .45, .18), .06), delayed(noise(.35, .38, .18, .6), .3)))
    write("skill_root_lock", mix(tone(48, 1.35, .45, "saw", sweep=-15), delayed(tone(96, 1.0, .3, "square"), .15), delayed(noise(.55, .38, .4), .42)))

    # Adaptive grand-adventure score. Tracks share a motif but gain tempo,
    # percussion and dissonance as the dungeon becomes more dangerous.
    write("music_menu", adventure_theme([(48, 55, 60), (46, 53, 58), (43, 50, 55), (47, 54, 59)], [60, 62, 63, 67, 65, 63, 62, 60, 55, 58, 60, 62, 63, 62, 60, 55], 88, .72, "sine"))
    write("music_explore", adventure_theme([(50, 57, 62), (48, 55, 60), (53, 60, 65), (45, 52, 57)], [62, 64, 65, 69, 67, 65, 64, 62, 57, 60, 62, 64, 65, 64, 62, 57], 104, .78))
    write("music_easy", adventure_theme([(50, 57, 62), (48, 55, 60), (53, 60, 65), (45, 52, 57)], [62, 65, 69, 67, 65, 64, 62, 57, 62, 64, 65, 69, 67, 65, 64, 62], 118, .86))
    write("music_medium", adventure_theme([(48, 55, 60), (46, 53, 58), (51, 58, 63), (43, 50, 55)], [60, 63, 67, 65, 63, 62, 60, 55, 60, 62, 63, 67, 70, 67, 65, 63], 128, .98))
    write("music_hard", adventure_theme([(45, 52, 57), (43, 50, 55), (46, 53, 58), (41, 48, 53)], [57, 60, 64, 63, 60, 58, 57, 52, 57, 58, 60, 64, 65, 64, 60, 58], 138, 1.08, "saw"))
    write("music_elite", adventure_theme([(43, 50, 55), (44, 51, 56), (41, 48, 53), (46, 53, 58)], [55, 58, 62, 61, 58, 55, 53, 50, 55, 58, 61, 65, 63, 61, 58, 55], 145, 1.18, "saw"))
    write("music_boss", adventure_theme([(41, 48, 53), (42, 49, 54), (38, 45, 50), (43, 50, 55)], [53, 56, 60, 59, 56, 53, 51, 48, 53, 56, 59, 63, 62, 59, 56, 53], 150, 1.25, "saw"))
    write("music_major_boss", adventure_theme([(38, 45, 50), (39, 46, 51), (36, 43, 48), (41, 48, 53)], [50, 53, 57, 56, 53, 51, 50, 45, 50, 53, 56, 60, 62, 60, 57, 53], 158, 1.35, "saw"))
    write("music_final_boss", adventure_theme([(36, 43, 48), (37, 44, 49), (33, 40, 45), (38, 45, 50)], [48, 51, 55, 54, 51, 48, 46, 43, 48, 51, 54, 58, 60, 58, 55, 51], 168, 1.5, "saw"))
    pulse = []
    for _ in range(4):
        pulse += mix(tone(55, .55, .12, release=.3), delayed(tone(110, .3, .06), .05)) + silence(.95)
    write("dungeon_pulse", pulse)


if __name__ == "__main__":
    main()

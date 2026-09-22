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


def main():
    write("ui_confirm", mix(tone(420, .18, .25, sweep=260, release=.08), delayed(tone(840, .16, .18), .08)))
    write("lock_in", mix(tone(105, .48, .32, "saw", sweep=-25), tone(210, .38, .18, sweep=80), noise(.22, .16)))
    write("correct", mix(tone(523, .55, .23), delayed(tone(659, .45, .23), .11), delayed(tone(784, .42, .2), .22)))
    write("wrong", mix(tone(190, .7, .3, "saw", sweep=-100), delayed(tone(125, .55, .25), .08), noise(.32, .2)))
    write("player_attack", mix(noise(.34, .42, .22, .35), tone(190, .42, .25, "saw", sweep=650, release=.08)))
    write("enemy_attack", mix(noise(.48, .5, .3, .24), tone(150, .5, .34, "saw", sweep=-95), delayed(tone(70, .35, .35), .12)))
    write("defend", mix(tone(280, .65, .25, sweep=-80), delayed(tone(560, .45, .2), .04), noise(.18, .32, .4)))
    write("exploit", mix(tone(95, 1.0, .27, "saw", sweep=760), delayed(tone(880, .45, .22), .35), delayed(noise(.4, .36, .2, .4), .45)))
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
    pulse = []
    for _ in range(4):
        pulse += mix(tone(55, .55, .12, release=.3), delayed(tone(110, .3, .06), .05)) + silence(.95)
    write("dungeon_pulse", pulse)


if __name__ == "__main__":
    main()

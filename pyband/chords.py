# Copyright 2019 Nicholas Samson
# This file is part of pyband.
#
# pyband is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyband is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyband.  If not, see <https://www.gnu.org/licenses/>.

import enum
from collections import deque
from typing import Optional, Iterable, Union, List, MutableSequence
from music21.interval import Interval
from music21.note import Note
from music21.chord import Chord
from music21.pitch import Pitch
from music21 import stream, midi
from heapq import heappush, heappop
from copy import deepcopy
from functools import partial

PitchInit = Union[str, Pitch]


class ChordQuality(enum.Enum):

    @property
    def interval(self) -> str:
        raise NotImplementedError()


class ThirdQuality(ChordQuality):
    MAJOR = "maj"
    MINOR = "min"
    SUS4 = "sus4"
    SUS2 = "sus2"

    @property
    def interval(self) -> str:
        if self == ThirdQuality.MAJOR:
            return "M3"
        elif self == ThirdQuality.MINOR:
            return "m3"
        elif self == ThirdQuality.SUS4:
            return "P4"
        else:
            return "M2"


class FifthQuality(ChordQuality):
    @property
    def interval(self) -> str:
        if self == self.PERFECT:
            return "P5"
        elif self == self.DIMINISHED:
            return "d5"
        else:
            return "A5"

    PERFECT = "perfect"
    DIMINISHED = "dim"
    AUGMENTED = "aug"


class UpperQuality(ChordQuality):
    @property
    def interval(self) -> str:
        if self == self.SIXTH:
            return "M6"
        elif self == self.DOMINANT_SEVENTH:
            return "m7"
        elif self == self.MAJOR_SEVENTH:
            return "M7"
        else:
            return "dd7"

    SIXTH = "6"
    DOMINANT_SEVENTH = "b7"
    MAJOR_SEVENTH = "7"
    MINOR_SEVENTH = "b7"
    DIMINISHED_SEVENTH = "bb7"


class Harmony(ChordQuality):
    @property
    def interval(self) -> str:
        if self == self.MINOR_THIRTEENTH:
            return "m13"
        elif self == self.MAJOR_THIRTEENTH:
            return "M13"
        elif self == self.MINOR_NINTH:
            return "m9"
        elif self == self.MAJOR_NINTH:
            return "M9"
        elif self == self.SHARP_NINTH:
            return "A9"
        elif self == self.ELEVENTH:
            return "P11"
        elif self == self.SHARP_ELEVENTH:
            return "A11"

    MINOR_NINTH = "b9"
    SHARP_NINTH = "#9"
    MAJOR_NINTH = "9"
    SHARP_ELEVENTH = "#11"
    ELEVENTH = "11"
    MINOR_THIRTEENTH = "b13"
    MAJOR_THIRTEENTH = "13"


def pitch_center(chord: Chord) -> float:
    return sum(pitch.midi for pitch in chord.pitches) / len(chord)


def chord_mad(chord: Chord, pitch: Pitch) -> float:
    """
    Returns the mean absolute deviation of the chord's MIDI notes from the given pitch
    :param chord:
    :param pitch:
    :return:
    """
    return sum(abs(p.midi - pitch.midi) for p in chord.pitches) / len(chord)


def chord_mean_distance(chord: Chord, pitch: Pitch) -> float:
    return sum(p.midi - pitch.midi for p in chord.pitches) / len(chord)


def move_chord(chord: Chord, pitch: Pitch) -> Chord:
    while abs(chord_mean_distance(chord, pitch)) > 12.0:
        dist = chord_mean_distance(chord, pitch)
        if dist < 0:
            chord = chord.transpose(12)
        else:
            chord = chord.transpose(-12)

    return chord


def move_pitch(note: Pitch, pitch: Pitch) -> Note:
    while abs(note.midi - pitch.midi) > 6:
        dist = note.midi - pitch.midi
        if dist < 0:
            note = note.transpose(12)
        else:
            note = note.transpose(-12)

    return note


def all_inversions(chord: Chord) -> List[Chord]:
    pitches: deque[Pitch] = deque(chord.pitches)
    out = []
    for i in range(len(chord)):
        last = pitches.pop()
        last = last.transpose(-12)
        pitches.appendleft(last)
        out.append(Chord(pitches))

    return out


class ChordType(object):

    def __init__(self, third_qual: ThirdQuality, fifth_qual: FifthQuality = FifthQuality.PERFECT,
                 upper_qual: Optional[UpperQuality] = None,
                 harmonies: Optional[Iterable[Harmony]] = None):
        if harmonies is None:
            harmonies: Iterable[Harmony] = []

        self._harmonies = frozenset(harmonies)
        self._third_qual = third_qual
        self._fifth_qual = fifth_qual
        self._upper_qual = upper_qual

    @property
    def third_quality(self) -> ThirdQuality:
        return self._third_qual

    @property
    def fifth_quality(self) -> FifthQuality:
        return self._fifth_qual

    @property
    def upper_quality(self) -> Optional[UpperQuality]:
        return self._upper_qual

    @property
    def harmonies(self) -> Iterable[Harmony]:
        return self._harmonies

    def with_harmonies(self, harmonies: Union[Harmony, Iterable[Harmony]]):
        if isinstance(harmonies, Harmony):
            harmonies = [harmonies]
        return ChordType(self.third_quality, self.fifth_quality, self.upper_quality, self._harmonies.union(harmonies))

    def with_upper_quality(self, upper_qual: UpperQuality):
        return ChordType(self.third_quality, self.fifth_quality, upper_qual, self.harmonies)

    def add_dom7(self):
        return self.with_upper_quality(UpperQuality.DOMINANT_SEVENTH)

    def add_maj7(self):
        return self.with_upper_quality(UpperQuality.MAJOR_SEVENTH)

    def add_min7(self):
        return self.add_dom7()

    def add_dim7(self):
        return self.with_upper_quality(UpperQuality.DIMINISHED_SEVENTH)

    def add_s9(self):
        return self.with_harmonies(Harmony.SHARP_NINTH)

    def add_min9(self):
        return self.with_harmonies(Harmony.MINOR_NINTH)

    def add_maj9(self):
        return self.with_harmonies(Harmony.MAJOR_NINTH)

    def add_s11(self):
        return self.with_harmonies(Harmony.SHARP_ELEVENTH)

    def add_11(self):
        return self.with_harmonies(Harmony.ELEVENTH)

    def add_min13(self):
        return self.with_harmonies(Harmony.MINOR_THIRTEENTH)

    def add_maj13(self):
        return self.with_harmonies(Harmony.MAJOR_THIRTEENTH)

    def generate_closed_chord(self,
                              root_note: PitchInit,
                              anchor_note: PitchInit = "C4",
                              max_notes: int = 5,
                              bass_note: Optional[PitchInit] = None,
                              include_root: bool = True):

        if isinstance(root_note, str):
            root_note = Pitch(root_note)

        if isinstance(anchor_note, str):
            anchor_note = Pitch(anchor_note)

        if isinstance(bass_note, str):
            bass_note = Pitch(bass_note)

        if max_notes < 2:
            raise ValueError("Not really a chord with only one or no notes.")

        chord_heap = []

        third = root_note.transpose(self.third_quality.interval)
        fifth = root_note.transpose(self.fifth_quality.interval)
        harmonies = [root_note.transpose(harm.interval) for harm in self.harmonies]

        heappush(chord_heap, (9, third))
        for harmony in harmonies:
            heappush(chord_heap, (7, harmony))

        heappush(chord_heap, (1, fifth))
        if include_root:
            heappush(chord_heap, (3, root_note))

        if self.upper_quality is not None:
            heappush(chord_heap, (9, (root_note.transpose(self.upper_quality.interval))))

        while len(chord_heap) > max_notes:
            heappop(chord_heap)

        chord_base = Chord(note for _, note in chord_heap)

        chord_base.sortDiatonicAscending(inPlace=True)

        chord_base = move_chord(chord_base, anchor_note)
        chord_base = chord_base.closedPosition()
        inversions = all_inversions(chord_base)
        inversions = [move_chord(c, anchor_note) for c in inversions]

        best_option = min(inversions, key=lambda x: chord_mad(x, anchor_note))

        if bass_note is not None:
            bass_note = move_pitch(bass_note, anchor_note.transpose(-12))
            best_option.add(bass_note, runSort=True)

        return best_option


MAJOR = ChordType(ThirdQuality.MAJOR)
MINOR = ChordType(ThirdQuality.MINOR)
DIMINISHED = ChordType(ThirdQuality.MINOR, FifthQuality.DIMINISHED)
SUS2 = ChordType(ThirdQuality.SUS2)
SUS4 = ChordType(ThirdQuality.SUS4)

MAJOR_SEVENTH = MAJOR.add_maj7()
MINOR_SEVENTH = MINOR.add_min7()
DIMINISHED_SEVENTH = DIMINISHED.add_dim7()
DOMINANT_SEVENTH = MAJOR.add_dom7()
SUS4_SEVENTH = SUS4.add_dom7()


def __main():
    chord = MAJOR_SEVENTH.add_maj9()
    V_chord = DOMINANT_SEVENTH.add_maj13()
    ii_chord = MINOR_SEVENTH.add_maj9()

    ii_val = ii_chord.generate_closed_chord("D4", include_root=False, bass_note="D4")
    V_val = V_chord.generate_closed_chord("G4", include_root=False, bass_note="G4")
    tonic = chord.generate_closed_chord("C4", include_root=False, bass_note="C4")
    ii_val.duration.type = "whole"
    V_val.duration.type = "whole"
    tonic.duration.type = "whole"

    print(ii_val, V_val, tonic)

    print(all_inversions(tonic))

    m = stream.Measure()
    m.append(ii_val)
    m.append(V_val)
    m.append(tonic)
    part = stream.Part()
    part.append(m)

    score = stream.Score()
    score.insert(0, part)
    score.write(fp="iiVI.xml")


if __name__ == '__main__':

    __main()

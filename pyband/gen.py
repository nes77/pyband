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

from typing import Union

from music21 import note, chord

from pyband.chords import ChordType


def generate_voicing(bass_note: Union[str, note.Note],
                     chord_quality: ChordType,
                     anchor_note: Union[str, note.Note] = note.Note("C4"),
                     omit_root: bool = False) -> chord.Chord:
    pass

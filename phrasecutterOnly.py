import mido
from mido import MidiFile
from mido import MidiTrack
from mido import Message
from mido import MetaMessage
import os
import random

longPhrases = {}
shortPhrases = {}


# msgs list of note messages (non-meta)
def toFile(msgs, key_sig, time_sig, tempo, saveYN):
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    track.append(MetaMessage('key_signature', key=key_sig, time=0))
    t = time_sig.split()
    num = int(t[0])
    den = int(t[2])
    track.append(MetaMessage('time_signature', numerator=num, denominator=den, clocks_per_click=24, notated_32nd_notes_per_beat=8, time=0))
    track.append(MetaMessage('set_tempo', tempo=tempo, time=0))
    track.append(Message('program_change', program=12, time=0))
    for i in msgs:
        track.append(i)

    # print(track)
    if saveYN:
        mid.save('new_song.mid')
    return mid


def main():
    # key sig-time pairs
    global shortPhrases
    global longPhrases

    directory = input("Please enter a path to the desired directory: ")

    for filename in os.listdir(directory):
        if filename.endswith(".midi") or filename.endswith(".mid"):
            # print("FileName: ", filename)
            mid = MidiFile("MidiDataset/"+filename)
            key_sig = ''
            time_sig = ''
            numTicksBerBeat = 0
            shortPhraseList = []
            longPhraseList = []
            ticksSoFar = 0
            numerator = 0   # will be numerator of time signature
            denominator = 0 # will be denominator of time signature
            for i, track in enumerate(mid.tracks):
                for msg in track:
                    if msg.is_meta and msg.type == 'key_signature':
                        key_sig = msg.key
                    if msg.is_meta and msg.type == 'time_signature':
                        numerator = msg.numerator
                        # print("Numerator:", numerator)
                        denominator = msg.denominator
                        # print("denominator:", denominator)
                        # clocks per click = midi clock ticks per metronome beat
                        clocks_per_click = msg.clocks_per_click
                        notated_32nd_notes_per_beat = msg.notated_32nd_notes_per_beat
                        time_sig = str(numerator) + " / " + str(denominator)
                        numTicksBerBeat = clocks_per_click * notated_32nd_notes_per_beat
                    if key_sig != '' and time_sig != '':
                        keyTimePair = (key_sig, time_sig)
                        # print("KeyTimePair: ", keyTimePair)
                        if keyTimePair not in shortPhrases:
                            shortPhrases[keyTimePair] = []
                        if keyTimePair not in longPhrases:
                            longPhrases[keyTimePair] = []
                    if msg.is_meta == False and numerator != 0 and numTicksBerBeat != 0:
                        # generating phrases
                        if msg.type == "note_on" or msg.type == "note_off":
                            time = msg.time
                            ticksSoFar += int(time)
                            shortPhraseList.append(msg)
                            longPhraseList.append(msg)
                            if ticksSoFar % (numTicksBerBeat * int(numerator) * 4) == 0: # long phrase
                                ticksSoFar = 0
                                # print("Long Phrase:", longPhraseList)
                                # print()
                                longPhrases[keyTimePair].append(longPhraseList)
                                longPhraseList.clear()
                            # if ticksSoFar % (numTicksBerBeat * int(numerator)) == 0: # short phrases
                            if ticksSoFar % (numTicksBerBeat * int(numerator)) == 0:  # short phrases
                                # print("Short Phrase:", shortPhraseList)
                                # print()
                                shortPhrases[keyTimePair].append(shortPhraseList)
                                shortPhraseList.clear()
            # print("Short Phrases Dict: ", len(shortPhrases))
            # print("Long Phrases Dict: ", len(longPhrases))

    # test plays random long phrase (supposed to be 4 bars) in the key of C, 4/4 time
    rndLong = random.randrange(len(longPhrases[('C', '4 / 4')]))
    output = mido.open_output('IAC Driver Bus 1')
    test = toFile(longPhrases[('C', '4 / 4')][rndLong], 'C', '4 / 4', 375000, False)
    for msg in test.play():
        print(msg)
        output.send(msg)


main()








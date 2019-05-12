import os
from mido import MidiFile
from mido import MidiTrack
from mido import Message
from mido import MetaMessage
import random

shortPhrases = {}
longPhrases = {}
phrases = {}


# msgs list of note messages (non-meta)
def toFile(msgs, key_sig, time_sig, tempo):
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
    mid.save('new_song.mid')
    return mid


# size is how many bars long a piece should be
def randomTrack(size, key_sig, time_sig):
    global shortPhrases
    global longPhrases
    global phrases
    bars = 0
    song = []
    while bars < size:
        rndShort = random.randrange(len(shortPhrases[(key_sig, time_sig)]))
        rndLong = random.randrange(len(longPhrases[(key_sig, time_sig)]))
        if size - bars < 4:
            song.extend(shortPhrases[(key_sig, time_sig)][rndShort])
            bars += 1
        else:
            rnd = random.randint(1, 2)
            if rnd == 1:
                song.extend(shortPhrases[(key_sig, time_sig)][rndShort])
                bars += 1
            else:
                song.extend(longPhrases[(key_sig, time_sig)][rndLong])
                bars += 4
    return song


def main():
    # key sig-time pairs
    global shortPhrases
    global longPhrases
    global phrases

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
            messageList = []
            ticksSoFar = 0
            numerator = 0
            denominator = 0
            for i, track in enumerate(mid.tracks):
                # print('Track {}: {}'.format(i, track.name))
                for msg in track:
                    # outport.send(msg)
                    if msg.is_meta and msg.type == 'key_signature':
                        key_sig = msg.key
                    if msg.is_meta and msg.type == 'time_signature':
                        numerator = msg.numerator
                        # print("Numerator:", numerator)
                        denominator = msg.denominator
                        # print("denominator:", denominator)
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
                                longPhraseList = []
                            if ticksSoFar % (numTicksBerBeat * int(numerator)) == 0: # short phrases
                                # print("Short Phrase:", shortPhraseList)
                                # print()
                                shortPhrases[keyTimePair].append(shortPhraseList)
                                shortPhraseList = []
            # print("Short Phrases Dict: ", len(shortPhrases))
            # print("Long Phrases Dict: ", len(longPhrases))
    # rndLong = random.randrange(len(longPhrases[('C', '4 / 4')]))
    # test = toFile(longPhrases[('C', '4 / 4')][rndLong], 'C', '4 / 4', 375000)
    # for msg in test.play():
    #     print(msg)
    testRND = randomTrack(16, 'C', '4 / 4')
    test = toFile(testRND, 'C', '4 / 4', 375000)
    for msg in test.play():
        print(msg)




main()

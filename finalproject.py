import os
import mido
from mido import MidiFile



def main():
    #key sig-time pairs
    shortPhrases = {}
    longPhrases = {}
    phrases = {}

    #directory = input("Please enter a path to the desired directory: ")

    #for filename in os.listdir(directory):
    #    if filename.endswith(".midi") or filename.endswith(".mid"):
            #print("FileName: ", filename)
    mid = MidiFile("MidiDataset/lavender-town-music.midi")
    key_sig = ''
    time_sig = ''
    numTicksBerBeat = 0
    shortPhraseList = []
    longPhraseList = []
    messageList = []
    ticksSoFar = 0
    for i, track in enumerate(mid.tracks):
        #print('Track {}: {}'.format(i, track.name))
        for msg in track:
            # outport.send(msg)
            if msg.is_meta and msg.type == 'key_signature':
                key_sig = msg.key
            if msg.is_meta and msg.type == 'time_signature':
                numerator = msg.numerator
                print("Numerator:", numerator)
                denominator = msg.denominator
                print("denominator:", denominator)
                clocks_per_click = msg.clocks_per_click
                notated_32nd_notes_per_beat = msg.notated_32nd_notes_per_beat
                time_sig = str(numerator) + "/" + str(denominator)
                numTicksBerBeat = clocks_per_click * notated_32nd_notes_per_beat
            if key_sig != '' and time_sig != '':
                keyTimePair = (key_sig, time_sig)
                # print("KeyTimePair: ", keyTimePair)
                shortPhrases[keyTimePair] = []
                longPhrases[keyTimePair] = []
            if msg.is_meta == False and numerator != 0 and numTicksBerBeat != 0:
                #generating phrases
                if msg.type == "note_on" or msg.type == "note_off":
                    time = msg.time
                    ticksSoFar += int(time)
                    shortPhraseList.append(msg)
                    longPhraseList.append(msg)
                    if (ticksSoFar % (numTicksBerBeat * int(numerator) * 4) == 0): #long phrase
                        ticksSoFar = 0
                        print("Long Phrase:", longPhraseList)
                        print()
                        longPhrases[keyTimePair].append(longPhraseList)
                        longPhraseList = []
                    if (ticksSoFar % (numTicksBerBeat * int(numerator)) == 0): #short phrases
                        print("Short Phrase:", shortPhraseList)
                        print()
                        shortPhrases[keyTimePair].append(shortPhraseList)
                        shortPhraseList = []


main()

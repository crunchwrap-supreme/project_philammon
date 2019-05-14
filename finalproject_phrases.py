import os
import mido
from mido import MidiFile
from mido import MidiTrack
from mido import Message
from mido import MetaMessage
import random
import copy
from queue import PriorityQueue

# TODO - fix time_sig - list of important time information? can't just be a metamessage but need more than just '4/4'


# from dataclasses import dataclass, field
# from typing import Any
#
# # Used to be able to re-prioritize items on the queue
# @dataclass(order=True)
# class PrioritizedItem:
#     priority: float
#     count: int=field(compare=False)
#     item: Any=field(compare=False)

class Phrase:
    def __init__(self, MSGS, ticks):
        self.msgs = []
        for i in MSGS:
            self.msgs.append(i)
        self.ticks_per_beat = ticks

    def msgs(self):
        return self.msgs

    def numTicks(self):
        return self.ticks_per_beat

    # returns length of the phrase in beats
    def length(self):
        len = 0.0
        for i in self.msgs:
            if i.type == "note_on" or i.type == "note_off":
                len += int(i.time) / self.ticks_per_beat

        return len



shortPhrases = {}
longPhrases = {}
phrases = {}


# unfinished!!!
def genetic(popSize, size, key_sig, time_sig, tempo, desired):
    population = []
    output = mido.open_output('IAC Driver Bus 1')
    for i in range(popSize):
        population.append(randomTrack(size, key_sig, time_sig, desired))
    done = False
    while not done:
        pop = copy.deepcopy(population)
        for i in range(popSize):
            rndA = random.randrange(len(population))
            rndB = random.randrange(len(population))
            if population[rndA] != population[rndB]:
                A, B = crossover(population[rndA], population[rndB], size, time_sig, desired)
                pop.append(A)
                pop.append(B)
            rndC = random.randrange(len(population))
            C = mutation(population[rndC], time_sig)
            if population[rndC] != C:
                pop.append(C)
        popFit = fitnessCheck(pop, key_sig, time_sig, tempo, popSize)
        population = popFit
        repeat = input("Do you want to repeat this process with more songs? Y/N: ")
        if repeat == "N" or repeat == "no" or repeat == "no":
            done = True
        else:
            # FIX THIS!! if user quits one population set too early
            # there's no population for the next iteration of the loop
            continue
    return popFit


# user input!!!
# rewards -- rate on a scale 1-10
def fitnessCheck(population, key_sig, time_sig, tempo, popSize):
    output = mido.open_output('IAC Driver Bus 1')
    q = PriorityQueue()
    tiebreaker = 0
    for i in population:
        mid = toFile(i, key_sig, time_sig, tempo, False)
        for msg in mid.play():
            output.send(msg)
        # user input - do you want to play this again?
        done = False
        rating = 0
        superDone = False
        while not done:
            j = input("Please rate this song between 1-10, type 'play' to play the song again,  type 'save' to save the song file, or type 'q' to quit: ")
            if j == "play":
                for msg in mid.play():
                    output.send(msg)
            elif j == "save":
                name = input("Please name the song: ")
                mid.save(name)
            elif j == "q":
                done = True
                superDone = True    # to be able to break out of the for loop after the while loop
            elif j.isdigit() and (int(j) < 11 and int(j) > 0):
                done = True
                rating = int(j)
            else:
                continue
        if superDone:
            break
        q.put((rating * -1, tiebreaker, i))
        tiebreaker+=1
    pop = []
    if popSize > q.qsize():
        popSize = q.qsize()
    for i in range(popSize):
        item = q.get()
        pop.append(item)
    return pop


def ticksPerBeatConversion(phrase, desired_TPB):
    change = 1
    if (desired_TPB == phrase.ticks_per_beat):
        change = 1
    else:
        change = (desired_TPB - phrase.ticks_per_beat) / phrase.ticks_per_beat
    print("CHANGE: ", change)
    print()
    # going through each message and changing ticks to fit desired TPB
    # Must be an INTEGER

    list = []
    for i in phrase.msgs:
        print("Original Message: ", i)
        if i.type == "note_on":
            newTime = int(round((change * int(i.time))))
            newmsg = Message("note_on", note=i.note, velocity=i.velocity, time=newTime)
            print("New Message: ", newmsg)
            list.append(newmsg)
        elif i.type == "note_off":
            newTime = int(round((change * int(i.time))))
            newmsg = Message("note_off", note=i.note, velocity=i.velocity, time=newTime)
            print("New Message: ", newmsg)
            list.append(newmsg)
        print()
    newPhrase = Phrase(list, desired_TPB)
    return newPhrase


# THERE IS A PROBLEM HERE
# timing with tickssofar is BROKE and we're getting very short and very long pieces instead of uniform length
def crossover(A, B, bars, time_sig, desired):
    ticksPerBeat = desired
    crossPoint = random.randrange(bars) + 1
    childA = []
    childB = []

    ticksSoFar = 0
    ticks2 = 0
    timesig = time_sig.split()
    tickCheck = ticksPerBeat * int(timesig[0]) * bars

    parentA = ticksPerBeatConversion(A, desired)
    parentB = ticksPerBeatConversion(B, desired)

    # Child A
    for i in parentA.msgs:
        time = i.time
        ticksSoFar += int(time)
        childA.append(i)
        if ticksSoFar >= (ticksPerBeat * int(timesig[0]) * crossPoint):
            break
    for i in parentB.msgs:
        time = i.time
        ticks2 += int(time)
        if ticks2 >= tickCheck:
            break
        if ticks2 >= ticksSoFar:
            childA.append(i)

    ticks = 0
    for i in childA:
        time = i.time
        ticks += time
    if ticks != tickCheck:
        print("ChildA is not the right length. Goal: "+ str(tickCheck) +" Actual Length: "+str(ticks))

    ticksSoFar = 0
    ticks2 = 0
    # Child B
    for i in parentB.msgs:
        time = i.time
        ticksSoFar += int(time)
        childB.append(i)
        if ticksSoFar >= (ticksPerBeat * int(timesig[0]) * crossPoint):
            break
    for i in parentA.msgs:
        time = i.time
        ticks2 += int(time)
        if ticks2 >= tickCheck:
            break
        if ticks2 >= ticksSoFar:
            childB.append(i)

    ticks = 0
    for i in childB:
        time = i.time
        ticks += time
    if ticks != tickCheck:
        print("ChildB is not the right length. Goal: "+ str(tickCheck) +" Actual Length: "+str(ticks))

    return Phrase(childA, desired), Phrase(childB, desired)


# what kind of mutation?
# --switch around phrases implemented
# potentially also change notes, volume, etc
def mutation(parent, time_sig):
    child = []
    # rnd = random.randrange(1, 3)
    # if rnd == 1:    # phrase swap
    temp = []
    ticksSoFar = 0
    phrase = []
    timesig = time_sig.split()

    for i in parent.msgs:
        time = i.time
        ticksSoFar += int(time)
        phrase.append(i)
        if ticksSoFar == parent.ticks_per_beat * int(timesig[0]):
            temp.append(phrase)
            phrase = []
    if len(temp) != 0:
        rndPhrase1 = random.randrange(len(temp))
        rndPhrase2 = random.randrange(len(temp))
        t = temp[rndPhrase1]
        temp[rndPhrase1] = temp[rndPhrase2]
        temp[rndPhrase2] = t
        for i in temp:
            child.extend(i)
        p = Phrase(child, parent.ticks_per_beat)
        return p
    else:
        return parent


# msgs list of note messages (non-meta)
def toFile(phrase, key_sig, time_sig, tempo, saveYN):
    mid = MidiFile()
    mid.ticks_per_beat = phrase.ticks_per_beat
    track = MidiTrack()
    mid.tracks.append(track)
    timesig = time_sig.split()

    track.append(MetaMessage('key_signature', key=key_sig, time=0))
    track.append(MetaMessage('time_signature', numerator=int(timesig[0]), denominator=int(timesig[1]),
                             clocks_per_click=int(timesig[2]), notated_32nd_notes_per_beat=int(timesig[3]), time=0))
    track.append(MetaMessage('set_tempo', tempo=tempo, time=0))
    track.append(Message('program_change', program=12, time=0))
    for i in phrase.msgs:
        track.append(i)

    #print(track)
    if saveYN:
        mid.save('new_song.mid')
    return mid


# size is how many bars long a piece should be
def randomTrack(size, key_sig, time_sig, desired):
    global shortPhrases
    global longPhrases
    global phrases
    bars = 0
    song = []
    while bars < size:
        rndShort = random.randrange(len(shortPhrases[(key_sig, time_sig)]))
        rndLong = random.randrange(len(longPhrases[(key_sig, time_sig)]))
        if size - bars < 4:
            p = ticksPerBeatConversion(shortPhrases[(key_sig, time_sig)][rndShort], desired)
            song.extend(p.msgs)
            bars += 1
        else:
            rnd = random.randint(1, 2)
            if rnd == 1:
                p = ticksPerBeatConversion(shortPhrases[(key_sig, time_sig)][rndShort], desired)
                song.extend(p.msgs)
                bars += 1
            else:
                p = ticksPerBeatConversion(longPhrases[(key_sig, time_sig)][rndLong], desired)
                song.extend(p.msgs)
                bars += 4
    p = Phrase(song, desired)
    return p


def main():
    # key sig-time pairs
    global shortPhrases
    global longPhrases
    global phrases

    directory = input("Please enter a path to the desired directory: ")

    testkey = ''
    testtime = ''
    print("LOADING...")
    for filename in os.listdir(directory):
        if filename.endswith(".midi") or filename.endswith(".mid"):
            #print("FileName: ", filename)
            mid = MidiFile(directory +"/"+filename)
            key_sig = ''
            time_sig = ''
            shortPhraseList = []
            longPhraseList = []
            ticksSoFar = 0
            numerator = 0
            denominator = 0
            shortCount = 0
            longCount = 0
            tempo = 0
            duration = 0
            ugh = 0
            for i, track in enumerate(mid.tracks):
                ticksSoFar = 0
                # print('Track {}: {}'.format(i, track.name))
                for msg in track:
                    # outport.send(msg)
                    # print(msg)
                    if msg.is_meta and msg.type == "set_tempo":
                        tempo = msg.tempo
                    if msg.is_meta and msg.type == 'key_signature':
                        key_sig = msg.key
                    if msg.is_meta and msg.type == 'time_signature':
                        numerator = msg.numerator
                        # print("Numerator:", numerator)
                        denominator = msg.denominator
                        # print("denominator:", denominator)
                        clocks_per_click = msg.clocks_per_click
                        notated_32nd_notes_per_beat = msg.notated_32nd_notes_per_beat
                        # UGH MetaMessage not hashable - time_sig list of important information instead?
                        time_sig = str(numerator)+" "+str(denominator)+" "+str(clocks_per_click)+" "+str(notated_32nd_notes_per_beat)
                    if key_sig != '' and len(time_sig) != 0:
                        keyTimePair = (key_sig, time_sig)
                        # print("KeyTimePair: ", keyTimePair)
                        if keyTimePair not in shortPhrases:
                            shortPhrases[keyTimePair] = []
                        if keyTimePair not in longPhrases:
                            longPhrases[keyTimePair] = []
                    if msg.is_meta == False and numerator != 0 and tempo !=0:
                        # generating phrases
                        if msg.type == "note_on" or msg.type == "note_off" and tempo != 0 and mid.ticks_per_beat != 0:
                            # time = mido.second2tick(int(msg.time), mid.ticks_per_beat, tempo)
                            time = int(msg.time)
                            ticksSoFar += time
                            shortCount += time
                            longCount += time
                            if int(msg.note) == 44 and msg.type == "note_on":
                                ugh +=1
                            newmsg = Message("note_on", note=msg.note, velocity=msg.velocity, time=time)
                            shortPhraseList.append(newmsg)
                            longPhraseList.append(newmsg)
                            if longCount != 0 and longCount == (mid.ticks_per_beat * int(numerator) * 4): # long phrase
                                # print("Long Phrase:", longPhraseList)
                                # print()
                                if len(longPhraseList) != 0:
                                    p = Phrase(longPhraseList, mid.ticks_per_beat)
                                    longPhrases[keyTimePair].append(p)
                                    longPhraseList = []
                                longCount = 0
                            if shortCount != 0 and shortCount ==  (mid.ticks_per_beat * int(numerator)):  # short phrases
                                # print("Short Phrase:", shortPhraseList)
                                # print()
                                shortCount = 0
                                if len(shortPhraseList) != 0:
                                    p = Phrase(shortPhraseList, mid.ticks_per_beat)
                                    # print("Short Phrase Length: ", p.length())
                                    shortPhrases[keyTimePair].append(p)
                                    shortPhraseList = []



            # print("Short Phrases Dict: ", len(shortPhrases))
            # print("Long Phrases Dict: ", len(longPhrases))
    #rndLong = random.randrange(len(longPhrases[('C', '4 4 24 8')]))
   # print(longPhrases)
    #print(ugh)
    #print(longPhrases['G', ('4 4 24 8')])

    output = mido.open_output('IAC Driver Bus 1')
    #testRND = randomTrack(16, 'E', '4 4 24 8', 480)
    #test = toFile(testRND, 'E', '4 4 24 8', 700000, True)
    #for msg in test.play():
     #   output.send(msg)
      #  print(msg)

    pop = genetic(3, 16, 'C', '4 4 24 8', 700000, 480)





main()

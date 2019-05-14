import os
import mido
from mido import MidiFile
from mido import MidiTrack
from mido import Message
from mido import MetaMessage
import random
import copy
from queue import PriorityQueue


# from dataclasses import dataclass, field



shortPhrases = {}
longPhrases = {}
phrases = {}


# unfinished!!!
# do we want this recursive or do we while loop wherever we call this
def genetic(popSize, size, key_sig, time_sig, tempo):
    population = []
    output = mido.open_output('IAC Driver Bus 1')
    for i in range(popSize):
        population.append(randomTrack(size, key_sig, time_sig))
        mid = toFile(population[i], key_sig, time_sig, tempo, False)
        print("Now playing randomly generated track ", i)
        for msg in mid.play():
            output.send(msg)
    done = False
    while not done:
        pop = copy.deepcopy(population)
        for i in range(popSize):
            rndA = random.randrange(len(population))
            rndB = random.randrange(len(population))
            if population[rndA] != population[rndB]:
                A, B = crossover(population[rndA], population[rndB], size, time_sig)
                pop.append(A)
                pop.append(B)
            rndC = random.randrange(len(population))
            C = mutation(population[rndC], time_sig, key_sig)
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


# user input!!! saving files for replay?
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
                superDone = True
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


# THERE IS A PROBLEM HERE
# timing with tickssofar is BROKE and we're getting very short and very long pieces instead of uniform length
def crossover(parentA, parentB, bars, time_sig):
    crossPoint = random.randrange(bars) + 1
    childA = []
    childB = []

    ticksSoFar = 0
    ticks2 = 0
    tickCheck = 192 * int(time_sig.split()[0]) * bars

    # Child A
    for i in parentA:
        time = i.time
        ticksSoFar += int(time)
        childA.append(i)
        if ticksSoFar >= (192 * int(time_sig.split()[0]) * crossPoint):
            break
    for i in parentB:
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
    for i in parentB:
        time = i.time
        ticksSoFar += int(time)
        childB.append(i)
        if ticksSoFar >= (192 * int(time_sig.split()[0]) * crossPoint):
            break
    for i in parentA:
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

    return childA, childB


# what kind of mutation?
# --switch around phrases implemented
# potentially also change notes, volume, etc
def mutation(parent, time_sig, key_sig):
    child = []
    # rnd = random.randrange(1, 3)
    # if rnd == 1:    # phrase swap
    temp = []
    ticksSoFar = 0
    phrase = []
    for i in parent:
        time = i.time
        ticksSoFar += int(time)
        phrase.append(i)
        if ticksSoFar % (192 * int(time_sig.split()[0])) == 0:
            temp.append(phrase)
            phrase = []
    rndPhrase1 = random.randrange(len(temp))
    rndPhrase2 = random.randrange(len(temp))
    t = temp[rndPhrase1]
    temp[rndPhrase1] = temp[rndPhrase2]
    temp[rndPhrase2] = t
    for i in temp:
        child.extend(i)
    return child


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
                            if ticksSoFar % (192 * int(numerator) * 4) == 0: # long phrase
                                ticksSoFar = 0
                                # print("Long Phrase:", longPhraseList)
                                # print()
                                longPhrases[keyTimePair].append(longPhraseList)
                                longPhraseList.clear()
                            # if ticksSoFar % (numTicksBerBeat * int(numerator)) == 0: # short phrases
                            if ticksSoFar % (192 * int(numerator)) == 0:  # short phrases
                                # print("Short Phrase:", shortPhraseList)
                                # print()
                                shortPhrases[keyTimePair].append(shortPhraseList)
                                shortPhraseList.clear()
            # print("Short Phrases Dict: ", len(shortPhrases))
            # print("Long Phrases Dict: ", len(longPhrases))
    # rndLong = random.randrange(len(longPhrases[('C', '4 / 4')]))
    # test = toFile(longPhrases[('C', '4 / 4')][rndLong], 'C', '4 / 4', 375000)
    # for msg in test.play():
    #     print(msg)
    # testRND = randomTrack(16, 'E', '4 / 4')
    # test = toFile(testRND, 'E', '4 / 4', 800000, True)
    # for msg in test.play():
    #     print(msg)
    pop = genetic(3, 16, 'C', '4 / 4', 375000)






main()

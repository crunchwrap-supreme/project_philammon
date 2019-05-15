# CSCI 364 AI FINAL PROJECT
# A-STARS - MUSIC GENERATION
# Max Addae, Jack Bens, Adam Good, McKenzie Maurer
# Spring 2019

import os
import mido
from mido import MidiFile
from mido import MidiTrack
from mido import Message
from mido import MetaMessage
import random
import time
import copy
from queue import PriorityQueue


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


# global dictionaries for both lengths of phrases (1 bar/measure and 4 bars/measures), key is key_sig, time_sig pair
shortPhrases = {}
longPhrases = {}

# global dict, mood -> (key_sig, time_sig, tempo)
moods = {}


# creates initial population from randomly generated tracks in the given key and time signatures
# then calls crossover and mutation functions to add to the population
# finally calls fitness check to return the most fit population
# repeats until user decides to end
# returns the most fit population from the most recent loop
def genetic(popSize, size, key_sig, time_sig, tempo, desired):
    population = []
    output = mido.open_output('IAC Driver Bus 1')
    for i in range(popSize):
        population.append(randomTrack(size, key_sig, time_sig, desired))
    popFit = population
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
            # problem: if user quits one population set too early
            # then there's no population for the next iteration of the loop
            # Don't Do That
            continue
    return popFit


# user input!!!
# rewards -- rate on a scale 1-10
# puts population members into a priority queue based on user ratings
# returns popSize population members from the priority queue
def fitnessCheck(population, key_sig, time_sig, tempo, popSize):
    output = mido.open_output('IAC Driver Bus 1')
    q = PriorityQueue()
    tiebreaker = 0
    for i in population:
        mid = toFile(i, key_sig, time_sig, tempo, False)
        startTime = time.process_time()
        for msg in mid.play():
            output.send(msg)
        endTime = time.process_time()
        print("Actual Time: ", endTime - startTime)
        print()
        # user input - do you want to play this again?
        done = False
        rating = 0
        superDone = False
        while not done:
            j = input("Please rate this song between 1-10, type 'play' to play the song again, "
                      "type 'save' to save the song file, or type 'q' to quit: ")
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
        tiebreaker += 1
    pop = []
    if popSize > q.qsize():
        popSize = q.qsize()
    for i in range(popSize):
        item = q.get()[2]
        pop.append(item)
    return pop


# This exists because not every phrase has the same ticks per beat and that's part of why all our time stamps were
# wildly different. In order to maintain the desired amount of beats in a phrase when combining different phrases,
# this changes the time stamp in the note on/off message so that it will take up the same amount of beats in the new
# bpm. Returns a new phrase object.
def ticksPerBeatConversion(phrase, desired_TPB):
    # new time Must be an INTEGER
    list = []
    for i in phrase.msgs:
        if i.type == "note_on":
            newTime = int(round(desired_TPB * (int(i.time) / phrase.ticks_per_beat)))
            newmsg = Message("note_on", note=i.note, velocity=i.velocity, time=newTime)
            list.append(newmsg)
        elif i.type == "note_off":
            newTime = int(round(desired_TPB * (int(i.time) / phrase.ticks_per_beat)))
            newmsg = Message("note_off", note=i.note, velocity=i.velocity, time=newTime)
            list.append(newmsg)
    newPhrase = Phrase(list, desired_TPB)
    return newPhrase


# picks a random crossover point and creates two children by swapping at that point
# still having slight issues w/ pieces/phrases that are too long/too short, but not necessarily limited to this function
def crossover(A, B, bars, time_sig, desired):
    ticksPerBeat = desired
    crossPoint = random.randrange(bars) + 1
    childA = []
    childB = []

    ticksSoFar = 0
    ticks2 = 0
    timesig = time_sig.split()
    tickCheck = ticksPerBeat * int(timesig[0]) * bars

    # converts phrases to the same ticks per beat so that we can keep track of equivalent time
    # (and therefore beats/phrases)
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

    return Phrase(childA, desired), Phrase(childB, desired)

    # CROSSOVER END


# what kind of mutation?
# --switch around phrases implemented
# potentially also change notes, volume, etc (for future work??)
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


# creates a midi file from the given phrase, using other passed in values for important meta messages
# saveYN is a bool, determines whether to actually save the file to the computer or not
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

    # print(track)
    if saveYN:
        mid.save('new_song.mid')
    return mid


# creates a randomized track by pulling from the dictionary entry for the given key signature-time signature pair
# size is how many bars long a piece should be
# desired is the desired value for ticks per beat
# returns a phrase object containing the full list of messages for the song and its desired ticks per beat
def randomTrack(size, key_sig, time_sig, desired):
    global shortPhrases
    global longPhrases
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


# reinforcement learning!
# We were not able to flesh out or implement our ideas for a less user-dependant algorithm, so this takes up
# a lot of the user's time when left as-is.
# cap_size is the rough estimate of how long the piece should end up being
def q_learning(cap_size, key_sig, time_sig, tempo, desiredTPB, alpha, gamma):
    global shortPhrases
    global longPhrases

    phrases = []    # combines list of phrases together

    # use this for the Full Version
    phrases.extend(shortPhrases[(key_sig, time_sig)])
    phrases.extend(longPhrases[(key_sig, time_sig)])

    # use this version below for testing (way smaller dataset for tester/user convenience....)
    # for i in range(2):
    #     rndShort = random.randrange(len(shortPhrases[(key_sig, time_sig)]))
    #     rndLong = random.randrange(len(longPhrases[(key_sig, time_sig)]))
    #     phrases.append(shortPhrases[(key_sig, time_sig)][rndShort])
    #     phrases.append(longPhrases[(key_sig, time_sig)][rndLong])

    initialStates = len(phrases)
    initialQ_Table = [[0 for x in range (initialStates)] for y in range(initialStates)]
    output = mido.open_output('IAC Driver Bus 1')

    dict = {}
    maxRating = 0
    maxPhrase = None
    maxLocation = 0

    # INITIALIZE Q TABLE
    # with user ratings for each phrase!
    # states (previous phrases) are functionally absent right now, so each row contains the same col (action) values

    for col in range(initialStates):
        # save the highest rated phrase to be selected as the starting point
        phrase = phrases[col]
        rating = 0
        # for msg in phrase.msgs:
        #     output.send(msg)
        # print("Phrase length: ", phrase.length())
        rating = int(input("Please rate this phrase from 1-10 (worst to best): "))
        if maxRating < rating:
            maxRating = rating
            maxPhrase = phrases[col]
            maxLocation = col
        for row in range(initialStates):
            initialQ_Table[row][col] = rating

    # END INITIALIZATION

    totalBars = 0

    # print()
    # print("Single phrases DONE")
    # print()

    # FIRST ITERATION - CREATE """"future utility"""" TABLE
    # states (last phrases) now exist!
    # gets user rating for each possible phrase pair
    # calculates Q values, but without future rewards yet

    for row in range(initialStates):
        for col in range(initialStates):
            p1 = ticksPerBeatConversion(phrases[row], desiredTPB)
            p2 = ticksPerBeatConversion(phrases[col], desiredTPB)

            combined_msgs = []
            combined_msgs.extend(p1.msgs)
            combined_msgs.extend(p2.msgs)

            p = Phrase(combined_msgs, desiredTPB)
            dict[(p1, p2)] = p

            rating = 0
            mid = toFile(p, key_sig, time_sig, tempo, False)
            # for msg in mid.play():
            #     output.send(msg)
            done = False
            while not done:
                j = input(
                    "Please rate this phrase combination between 1-10, type 'play' to play the song again: ")
                if j == "play":
                    for msg in mid.play():
                        output.send(msg)
                elif j.isdigit() and (int(j) < 11 and int(j) > 0):
                    done = True
                    rating = int(j)
                else:
                    continue

            newQVal = ((1 - alpha) * initialQ_Table[row][col]) + (alpha * rating)

            initialQ_Table[row][col] = newQVal

    maxQSA = copy.deepcopy(initialQ_Table) # save this to use as permanent future utility estimate
    # use as permanent future utility estimate based on these values being for specific phrase combos---
    # which are what the Q table keeps track of in the state-action pairs, rather than a full song so far for state

    # FIRST ITERATION END

    songSoFar = maxPhrase
    lastPhraseLocation = maxLocation
    # update total bars based on length of songSoFar
    totalBars = songSoFar.length() / int(time_sig[0])
    # print("cap:", cap_size, "bars so far:", totalBars)

    # ITERATION START

    while totalBars < cap_size:
        # lastPhraseLocation starts as col, use to find row for corresponding phrase
        # iterate through row to find the col (and corresponding phrase) with highest Q value --will be next used phrase
        max = 0
        loc = 0
        for i in range(len(phrases)):
            if initialQ_Table[lastPhraseLocation][i] > max:
                max = initialQ_Table[lastPhraseLocation][i]
                loc = i

        # add phrase corresponding to loc to songSoFar
        msgs = songSoFar.msgs
        msgs.extend(ticksPerBeatConversion(phrases[loc], desiredTPB).msgs)
        temp = Phrase(msgs, desiredTPB)
        songSoFar = temp

        # play songSoFar for user, ask for rating of addition to song, update Q table accordingly
        song = toFile(songSoFar, key_sig, time_sig, tempo, False)
        rating = 0
        for msg in song.play():
            output.send(msg)
        done = False
        while not done:
            j = input("Please rate the updated song between 1-10, or type 'play' to play the song again: ")
            if j == "play":
                for msg in song.play():
                    output.send(msg)
            elif j.isdigit() and (int(j) < 11 and int(j) > 0):
                done = True
                rating = int(j)
            else:
                continue

        old = initialQ_Table[lastPhraseLocation][loc]
        initialQ_Table[lastPhraseLocation][loc] = ((1 - alpha) * old) + (alpha * (rating + (gamma * maxQSA[lastPhraseLocation][loc])))

        # update lastPhraseLocation
        lastPhraseLocation = loc

        # use songSoFar length (number of beats) + key sig numerator (beats per measure) to calculate totalBars
        totalBars = songSoFar.length() / int(time_sig[0])
        # print("cap:", cap_size, "bars so far:", totalBars)

    # ITERATION END

    # okay so we're out of the loop, got a full song, what now (just return the song)
    return songSoFar

    # Q LEARNING END


# theoretically goes through all the keys in the phrase dictionaries and asks the user to-----
# (either assign them a mood OR provides a list of moods and asks which one fits best)
# populates moods (scenario?) dictionary (mood -> list of (key_sig, time_sig, tempo?)((will likely assume standard TPB))
# theoretical use - provide the user the list of moods, ask which one they want to listen to while testing algorithms
# then pick a (key_sig, time_sig, tempo) from the given mood (key) and pass that in to the algorithms
def assign_mood():
    global shortPhrases
    global longPhrases
    global moods
    # standard tempos in beats per min
    # actually stored as microseconds per beat
    std_tempos = [mido.bpm2tempo(60), mido.bpm2tempo(90), mido.bpm2tempo(100), mido.bpm2tempo(115), mido.bpm2tempo(120),
                  mido.bpm2tempo(130), mido.bpm2tempo(135), mido.bpm2tempo(140), mido.bpm2tempo(150),
                  mido.bpm2tempo(160), mido.bpm2tempo(170), mido.bpm2tempo(180), mido.bpm2tempo(190), mido.bpm2tempo(200)]
    superDone = False
    while not superDone:
        for key in shortPhrases:
            for tempo in std_tempos:
                # using 480 ticks per beat as a standard (for now?)
                r = randomTrack(12, key[0], key[1], 480)
                output = mido.open_output('IAC Driver Bus 1')
                mid = toFile(r, key[0], [1], tempo, False)
                for msg in mid.play():
                    output.send(msg)
                done = False
                while not done:
                    j = input(
                        "Please enter a word describing the mood of this song, type 'play' to play the song again, "
                        "type 'save' to save the song file, or type 'q' to quit: ")
                    if j == "play":
                        for msg in mid.play():
                            output.send(msg)
                    elif j == "save":
                        name = input("Please name the song: ")
                        mid.save(name)
                    elif j == "q":
                        done = True
                        superDone = True
                    elif j == '':
                        continue
                    else:
                        j = j.upper()
                        moods[j] = moods[j].append((key[0], key[1], tempo))
        superDone = True
    return 0


def main():
    # key sig-time pairs
    global shortPhrases
    global longPhrases

    # PHRASE CUTTING

    directory = input("Please enter a path to the desired directory: ")

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
            for i, track in enumerate(mid.tracks):
                ticksSoFar = 0
                for msg in track:
                    if msg.is_meta and msg.type == "set_tempo":
                        tempo = msg.tempo
                    if msg.is_meta and msg.type == 'key_signature':
                        key_sig = msg.key
                    if msg.is_meta and msg.type == 'time_signature':
                        numerator = msg.numerator
                        denominator = msg.denominator
                        clocks_per_click = msg.clocks_per_click
                        notated_32nd_notes_per_beat = msg.notated_32nd_notes_per_beat
                        # time_sig is a string containing the pertinent time sig info since meta messages not hashable
                        time_sig = str(numerator)+" "+str(denominator)+" "+str(clocks_per_click)+" "+str(notated_32nd_notes_per_beat)
                    if key_sig != '' and len(time_sig) != 0:
                        keyTimePair = (key_sig, time_sig)
                        if keyTimePair not in shortPhrases:
                            shortPhrases[keyTimePair] = []
                        if keyTimePair not in longPhrases:
                            longPhrases[keyTimePair] = []
                    if msg.is_meta == False and numerator != 0 and tempo !=0:
                        # generating phrases
                        if msg.type == "note_on" or msg.type == "note_off" and tempo != 0 and mid.ticks_per_beat != 0:
                            time = int(msg.time)
                            ticksSoFar += time
                            shortCount += time
                            longCount += time
                            newmsg = Message("note_on", note=msg.note, velocity=msg.velocity, time=time)
                            shortPhraseList.append(newmsg)
                            longPhraseList.append(newmsg)
                            if longCount != 0 and longCount == (mid.ticks_per_beat * int(numerator) * 4): # long phrase
                                if len(longPhraseList) != 0:
                                    p = Phrase(longPhraseList, mid.ticks_per_beat)
                                    longPhrases[keyTimePair].append(p)
                                    longPhraseList = []
                                longCount = 0
                            if shortCount != 0 and shortCount ==  (mid.ticks_per_beat * int(numerator)):  # short phrases
                                shortCount = 0
                                if len(shortPhraseList) != 0:
                                    p = Phrase(shortPhraseList, mid.ticks_per_beat)
                                    shortPhrases[keyTimePair].append(p)
                                    shortPhraseList = []

    # PHRASE CUTTING END

    # couldn't figure out a good way to delete dictionary entries where the value was an empty list :(

    # EXAMPLES

    print()
    print("Here's an example of a randomized track!")
    print()

    output = mido.open_output('IAC Driver Bus 1')
    testRND = randomTrack(16, 'C', '4 4 24 8', 480)
    test = toFile(testRND, 'C', '4 4 24 8', False)
    for msg in test.play():
        output.send(msg)
    print("That was 16 bars in the key of C, 4/4 time.")
    q = input("Would you like to save this file? y/n: ")
    if q == "y":
        name = input("What would you like to name this file? (please include .mid or .midi extension): ")
        test.save(name)
    print()

    print("Genetic Algorithm Time")
    print()
    tempo = 500000
    numBars = 16
    s = input("What's your sample size? ")
    pop = genetic(int(s), numBars, 'C', '4 4 24 8', tempo, 480)
    # what do i do with this now

    print()
    print("Reinforcement Learning Takes Super Long!")
    song = q_learning(16, 'E', '4 4 24 8', 500000, 480, 0.5, 0.2)
    s = toFile(song, 'E', '4 4 24 8')
    print()
    done = False
    while not done:
        q = input("Press 'p' to play the full song again, 's' to save the song to a file, or 'q' to stop: ")
        if q == 'p':
            for msg in s.play():
                output.send(msg)
        elif q == 's':
            name = input("Please name the file (including .mid or .midi extension): ")
            s.save(name)
        elif q == 'q':
            done = True
        else:
            continue


main()








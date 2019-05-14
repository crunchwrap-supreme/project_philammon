import os
import mido
from mido import MidiFile
from queue import PriorityQueue








def main():

    directory = input("Please enter a path to the desired directory: ")

    q = PriorityQueue()

    for filename in os.listdir(directory):
        if filename.endswith(".midi") or filename.endswith(".mid"):
            print("FileName: ", filename)
            mid = MidiFile("MidiDataset/"+filename)

            count = 0

            for i, track in enumerate(mid.tracks):
                print('Track {}: {}'.format(i, track.name))
                for msg in track:
                    # outport.send(msg)
                    count+=1
                    print(msg)
                    q.put((int(msg.time), count, msg))
            break

    print()
    print("OKAY HERE'S THE QUEUE: ")
    print()

    while not q.empty():
        item = q.get()
        print(item)

    mido.second2tick()

main()













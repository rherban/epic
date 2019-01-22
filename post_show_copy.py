#!/usr/bin/python
import sys
import json
import os
import shutil 
from subprocess import call, check_output
from datetime import datetime
DATE=str(datetime.now().month) + "-" + str(datetime.now().day) + "-" + str(datetime.now().strftime('%y'))
MONTHYEAR=str(datetime.now().strftime('%B')) + " " + str(datetime.now().year)

volumes_to_check = {"/Volumes/ROLAND": "M-400/SONGS",
                    "/Volumes/Kingston": "RSS",
                    "/Volumes/H2SD":"FOLDER01"
                    }

#Get Dropbox dir from settings, then set destination dir
HOME = os.path.expanduser("~")
DROPBOX_CONFIG=HOME + "/.dropbox/info.json" 
with open(DROPBOX_CONFIG) as f:
    dropbox = json.load(f)
try:
    DROPBOX=dropbox["business"]["path"] 
except:
    DROPBOX=dropbox["personal"]["path"]
DEST=DROPBOX + "/Sunday Sermons - Epic Website/" + MONTHYEAR






class audio_file:
    def __init__(self, file):
        self.filename = file
        self.size = os.path.getsize(file)
        self.timestamp = os.path.getmtime(file)
        self.basedir = os.path.split(file)[0]
        self.ext = os.path.splitext(file)[1]
        self.new_filename = ""
        self.copied = False
        #sys.stdout.write(self.file + " - " + os.path.splitext(file)[0][-1:] + " ")
        if int(os.path.splitext(file)[0][-1:]) == 0:
            self.service = 'a'
        elif int(os.path.splitext(file)[0][-1]) == 1:
            self.service = 'b'
        else:
            self.service = '-1'
        #sys.stdout.write(str(self.service) + "\n")
        #sys.stdout.flush()

    def convert(self, speaker, title):
        last_digit = os.path.splitext(self.filename)[0][-1:]
        if last_digit.isdigit():
            self.service = chr(97 + int(last_digit))
        else:
            self.service = '?'

        self.new_filename = DATE + self.service + " - " + speaker + " - " + title + self.ext

    def __str__(self):
        return "\n" + "-"*30 + "\nInside audio_file \n filename \t " + self.filename + "\n size \t" + str(self.size) + "\n timestamp \t" + str(self.timestamp) + "\n basedir \t" + self.basedir + "\n ext \t" + self.ext + "\n new \t" + self.new_filename + "\n service\t" + self.service + "\n" + "-"*30
        

def check_for_volumes():
    audio_files = []
    skipped = []

    # run initial scan to get recording count per directory (singleton is probably bogus)
    dir_count = {} 
    for volume, dir in volumes_to_check.iteritems():
        # should check to make sure volume/dir is accessible
        for root, dirs, files in os.walk(os.path.join(volume,dir)):
            for file in files:
                if file.lower().endswith(".wav") or file.lower().endswith(".mp3"):
                     x = audio_file(os.path.join(root, file))
                     # check for zero-byte
                     if x.size == 0:
                         continue
                     try:
                         dir_count[x.basedir] += 1
                     except:
                         dir_count[x.basedir] = 1


    # do actual scans
    print("Checking these volumes:")
    for volume, dir in volumes_to_check.iteritems():
        print os.path.join(volume, dir)

    print
    print("Valid recordings:")
    for volume, dir in volumes_to_check.iteritems():
        for root, dirs, files in os.walk(os.path.join(volume,dir)):
            for file in files:
                if file.lower().endswith(".wav") or file.lower().endswith(".mp3"):
                     x = audio_file(os.path.join(root, file))
                     if x.size == 0:
                         skipped.append(x.filename + " - zero byte file")
                         continue
                     if dir_count[x.basedir] == 1:
                         skipped.append(x.filename + " - single recording, assuming bogus")
                         continue

                     #if dir_count[x.basedir] > 2:
                         #skipped.append(x.filename + " - too many recordings, assuming bogus")
                         #continue
                     call(["ls","-las",x.filename])
                     audio_files.append(x)

    print
    print("Skipping these recordings:")
    for each in skipped:
        print each

    return audio_files


def main():
    audio_files = check_for_volumes()
    print
    print
    speaker = raw_input("Who was the speaker? ")
    #speaker = "mike test"
    title = raw_input("Title of the message? ")
    #title = "best title"
    #check for invalid chars


    print 
    print("Destination directory:\n" + DEST)
    print
    print("Trying to copy the following recordings:")
    for i in audio_files:
        i.convert(speaker, title)
        sys.stdout.write(i.filename + " ==> " + os.path.join(DEST, i.new_filename))
        if os.path.isfile(os.path.join(DEST,i.new_filename)):
            # make this red
            sys.stdout.write("  **File already exists!!**")
        sys.stdout.write("\n")
        sys.stdout.flush()

    print
    confirm = raw_input("Ready to copy to Dropbox? (y/n) ")
    if confirm == "N" or confirm == "n":
        print("Exiting with no changes made")
        sys.exit()
    print
    print
    print

    try:
        os.makedirs(DEST, 0755)
        print("Creating destination directory: " + DEST)
    except:
        pass


    print("Copying recordings...")
    for i in audio_files:
        if not(os.path.isfile(os.path.join(DEST, i.new_filename))):
            print(i.filename + " ==> " + os.path.join(DEST, i.new_filename))
            shutil.copy2(i.filename, os.path.join(DEST, i.new_filename))
            i.copied = True
        else:
            print("Skipping " + i.filename)
    print("Done")



    # confirm md5sum
    print
    print("Verifying transfers...")
    for i in audio_files:
        if not(i.copied):
            continue
        md5sum1 = check_output(["md5",i.filename]).split('=')[1]
        md5sum2 = check_output(["md5",os.path.join(DEST,i.new_filename)]).split('=')[1]
        if md5sum1 != md5sum2:
            print("MD5 checksums don't match!")
            print(str(md5sum1).rstrip() + " " + i.filename)
            print(str(md5sum2).rstrip() + " " + os.path.join(DEST, i.new_filename))


         call(["ls","-las",i.filename])
         call(["ls","-las",os.path.join(DEST, i.new_filename)])
         print
    print("Done")


    sys.exit()

    # delete old files
    print
    confirm = raw_input("Ready to delete the original files? (y/n) ")
    if confirm == "N" or confirm == "n":
        print("Exiting with no changes made")
        sys.exit()
    for i in audio_files:
        if i.copied:
            print("Would remove " + i.filename)

    print
    print("Done!")

main()

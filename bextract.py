from struct import *
import typer
import codecs
import os
import shutil
import math


from typing_extensions import Annotated

app = typer.Typer()

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])


def inject_updateoffsets(
    origin_file,
    new_file,
    new_file_size,
    prev_file_size,
    origin_file_offset
):
    if new_file_size > prev_file_size:
        with open('inject.tmp', "rb+") as file:
            buffer = int.from_bytes(file.read(4), "big", signed=False)
            amount_of_files = buffer
            file.seek(8, os.SEEK_CUR)
            size = int.from_bytes(file.read(4), "big", signed=False)
            for i in range(amount_of_files):
                buf = file.read(4)
                offset = int.from_bytes(file.read(4), "big", signed=False)
                new_size_diff = new_file_size - prev_file_size

                if offset > origin_file_offset:
                    new_data = offset + new_size_diff

                    file.seek(-4, os.SEEK_CUR)
                    file.write((new_data).to_bytes(4, byteorder='big', signed=False))
                    file.seek(8, os.SEEK_CUR)
                    continue

                if offset == origin_file_offset:
                    file.write((new_file_size).to_bytes(4, byteorder='big', signed=False))
                    file.seek(4, os.SEEK_CUR)
                else:
                    file.seek(8, os.SEEK_CUR)
                    
                    
def get_file_name(
    file: str,
    name: int
):
    currentString = ""
    with open(file, "rb+") as f:
        f.seek(name)
        data_byte = f.read(1)
        if len(data_byte) != 1:
            exit()
        else:
            currentString += codecs.decode(data_byte, errors='ignore')

            while (byte := f.read(1)):
                if byte == b'\x00':
                    break
                currentString += codecs.decode(byte, errors='ignore')
    return currentString


@app.command()
def inject(
    file: str,
    inject_file: str,
):
    data = []
    new_data = []
    fileIndex = None
    
    checkFile = os.path.isfile(inject_file)
    if checkFile == False:
        print("not a valid file")
        exit()
        
    with open(file, "rb+") as f:
        data_byte = f.read(16)
        if len(data_byte) != 16:
            print("your file is broken")
            exit()
        else:
            items, buffer, dataOffset = unpack('>IxxxxII', data_byte)
            print(f"[!] found the data buffer offset at {hex(dataOffset)}")
            stopLine = (items+1) * 16
            sanityCheck = False

            while (byte := f.read(16)):
                current_line = f.tell()
                if current_line > stopLine:
                    break
                fileNameOffset, itemOffset, size = unpack('>IIIxxxx', byte)
                name = fileNameOffset + stopLine
                offset = itemOffset + dataOffset
                file_name = get_file_name(file, name)
                data.append([offset, size, file_name])
                new_data.append([itemOffset, size, file_name, fileNameOffset])
                if file_name == inject_file:
                    fileIndex = len(data) - 1
                    sanityCheck = True
            if sanityCheck == False:
                print("[!!!!] can't find the file to inject")
                exit()
            else:
                # get file size
                new_size = os.path.getsize(inject_file)
                
                
                checkFile = os.path.isfile("inject.tmp")
                if checkFile == True:
                    os.remove("inject.tmp")
                test = open("inject.tmp", "x")
                
                with open(file, "rb+") as origin:
                    with open(inject_file, "rb+") as new:
                        with open("inject.tmp", "rb+") as tmp:
                            start = origin.read(data[fileIndex][0])
                            tmp.write(start)
                            new_file = new.read()
                            tmp.write(new_file)
                            if new_size >= data[fileIndex][1]:
                                origin.seek(data[fileIndex][0] + data[fileIndex][1])
                                other_data = origin.read()
                                tmp.write(other_data)
                            else:
                                print('lesser size is in wip!')
                                exit()
                inject_updateoffsets(file, inject_file, new_size, data[fileIndex][1], new_data[fileIndex][0])
    shutil.copy('inject.tmp', f"INJECTED_{file}")
    print(f"[!] Successfully injected {inject_file} into {file}")
    os.remove('inject.tmp')
    pass

@app.command()
def info(
    file: str
):
    print('[?] pulling bpm info')
    new_size = os.path.getsize(file)
    arrays = []
    with open(file, "rb+") as f:
        data_byte = f.read(16)
        if len(data_byte) != 16:
            exit()
        else:
            items, buffer, dataOffset = unpack('>IxxxxII', data_byte)
            print(f"[!] found the data buffer offset at {hex(dataOffset)}")
                
                
            # evil bexide file list pulling level hacking
            # what the fuck?
            stopLine = (items+1) * 16

            while (byte := f.read(16)):
                current_line = f.tell()
                if current_line > stopLine:
                    break
                items, itemOffset, size = unpack('>IIIxxxx', byte)
                name = items + stopLine
                file_name = get_file_name(file, name)

                offset = itemOffset + dataOffset
                print(f"File: {file_name}, Offset w/ Data Buffer: {offset}, Offset w/o: {itemOffset}, Size: {convert_size(size)}")
                arrays.append([offset, size, file_name])
    lastElement = len(arrays) - 1
    add = arrays[lastElement][0] + arrays[lastElement][1]
    if add ==  new_size:
        print("[!] This BPM can work ingame")
    else:
        print("[!] This BPM cannot work ingame, something went wrong!")


@app.command()
def extract(
    file: str,
):
    arrays = []
    with open(file, "rb+") as f:
        data_byte = f.read(16)
        if len(data_byte) != 16:
            exit()
        else:
            items, buffer, dataOffset = unpack('>IxxxxII', data_byte)
            print(f"[!] found the data buffer offset at {hex(dataOffset)}")
                
                
            # evil bexide file list pulling level hacking
            # what the fuck?
            stopLine = (items+1) * 16
            
            while (byte := f.read(16)):
                current_line = f.tell()
                if current_line > stopLine:
                    break
                items, itemOffset, size = unpack('>IIIxxxx', byte)
                name = items + stopLine
                file_name = get_file_name(file, name)

                offset = itemOffset + dataOffset
                arrays.append([offset, size, file_name])
                print(f"[-] {file_name} at offset {offset} with {convert_size(size)} bytes")
    extract_file(file, arrays)

def extract_file(file, arrays):
    for index, item in enumerate(arrays):
        currentFile = None
        if "/" not in item[2]:
            currentFile = item[2]
        else:
            splitted = item[2].split("/")
            if len(splitted) != 2:
                directory_path = os.path.dirname(item[2])
                if not os.path.exists(directory_path):
                    os.makedirs(directory_path)

                currentFile = item[2]
            else:
                # YIPPEE!!!!!
                if not os.path.exists(splitted[0]):
                    os.makedirs(splitted[0])
                currentFile = os.path.join(splitted[0], splitted[1])
        with open(file, 'rb') as infile, open(currentFile, 'wb') as outfile:
            infile.seek(item[0])
            # get all the bytes listed since im lazy,,,
            end = item[0] + item[1]
            trimmed_data = infile.read(end - item[0])
            # write our data
            outfile.write(trimmed_data)

if __name__ == "__main__":
    app()

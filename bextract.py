from struct import *
import typer
import codecs
import os
from typing_extensions import Annotated
app = typer.Typer()

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
            currentString += codecs.decode(data_byte, 'utf-8')

            while (byte := f.read(1)):
                if byte == b'\x00':
                    break
                currentString += codecs.decode(byte, 'utf-8')
    return currentString


@app.command()
def inject(
    file: str,
    inject_file: str,
):
    with open(file, "rb+") as f:
        data_byte = f.read(16)
        if len(data_byte) != 16:
            exit()
        else:
            items, buffer, dataOffset = unpack('>IxxxxII', data_byte)
            print(f"[!] found the data buffer offset at {hex(dataOffset)}")
            stopLine = int(((dataOffset - buffer) / 16)) * 16
            sanityCheck = False

            while (byte := f.read(16)):
                current_line = f.tell()
                if current_line > stopLine:
                    break
                items, itemOffset, size = unpack('>IIIxxxx', byte)
                name = items + stopLine
                offset = itemOffset + dataOffset
                file_name = get_file_name(file, name)
                if file_name == inject_file:
                    sanityCheck = True
            if sanityCheck == False:
                print("[!!!!] can't find the file to inject")
                exit()
            else:
                pass

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
            stopLine = int(((dataOffset - buffer) / 16)) * 16
            
            while (byte := f.read(16)):
                current_line = f.tell()
                if current_line > stopLine:
                    break
                items, itemOffset, size = unpack('>IIIxxxx', byte)
                name = items + stopLine
                file_name = get_file_name(file, name)

                offset = itemOffset + dataOffset
                arrays.append([offset, size, file_name])
                print(f"[-] {file_name} at offset {offset} with {size} bytes")
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

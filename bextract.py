from struct import *
import typer
from typing_extensions import Annotated


def main(
    file: str,
    extract: Annotated[bool, typer.Option(help="Extract a BPM file.")] = True
):
    if extract:
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
                    items, itemOffset, size, uselessBtw = unpack('>IIxxHl', byte)
                    # print(items, size)
                    offset = itemOffset + dataOffset
                    arrays.append([offset, size])
                    print(f"[-] item at offset {offset} with {size} bytes")
        extract_file(file, arrays)
    else:
        print('uh, you can only extract btw for now lol')
        exit()

def extract_file(file, arrays):
    for index, item in enumerate(arrays):
        with open(file, 'rb') as infile, open(f"{index}.extracted", 'wb') as outfile:
            infile.seek(item[0])
            # get all the bytes listed since im lazy,,,
            end = item[0] + item[1]
            trimmed_data = infile.read(end - item[0])
            # write our data
            outfile.write(trimmed_data)

if __name__ == "__main__":
    typer.run(main)

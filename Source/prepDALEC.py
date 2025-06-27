"""
    Split long DALEC files (e.g., dailies) into hourly raw files for HyperCP

    Args Needed To Run:
        -f, --file (str)  : The path to the text file that you want to split into hourly files
        -o, --output (str): The path to the directory that you want the hourly files to be placed in. 

    Example Run Command:
        python prepDALEC.py -f path/to/file.TXT -o dir/to/place/files

    *** NOTE : The output directory path should NOT end with a '/' ***
    *** NOTE : Currently only works with DALEC Raw data file! ***
"""

import argparse
import pandas as pd


def find_line_number(file_path):
    """
    Reads a text file and returns the line number of the first occurrence of the data in order to skip the header.

    Args:
        file_path (str): The path to the text file.

    Returns:
        int: The line number (starting from 1) if the text is found, otherwise None.
        str: The header text at the beginning of the raw data files.
    """
    try:
        header = ""
        with open(file_path, 'r', encoding="utf-8") as file:
            for line_number, line in enumerate(file, 1):
                header += line
                if "---------OUTPUT FORMAT---------" in line:
                    return line_number, header
        return None  # Target text not found
    except FileNotFoundError:
        return None


def split_csv_hourly(input_file, output_prefix):
    """
    Splits a large TXT file into hourly TXT files based on a timestamp column. 
    NOTE: TimeStamp needs to be the 4th value in each row in the data file. 

    Args:
        input_file (str): Path to the input TXT file.
        output_prefix (str): Path to output file directory 
    """

    #step 0: Initialization
    print("---- Initializing Data...")
    output_prefix += f"/{input_file.split('/')[-1][0:8]}"
    csv_data_line_number, header = find_line_number(input_file)
    if csv_data_line_number is None:
        return


    # Step 1: Read original file as raw text lines
    print("---- Reading Input File...")
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()


    # Step 2: Parse each line and extract timestamp for grouping
    print("---- Processing Data...")
    data=[]
    counter = 0
    percent = 0
    total_lines = len(lines) // 20

    for line in lines:
        if counter > csv_data_line_number:

            ##Progress Bar
            if counter % total_lines == 0:
                print(f"... {percent}%")
                percent += 5
            ##

            parts = line.split(",")
            if len(parts) > 1: #Skips over empty rows
                try:
                    timestamp = pd.to_datetime(parts[3])
                    hour_group = timestamp.floor('h')  # round down to the hour
                    if hour_group.tz is None:
                        print(f'Timezone naive timestamp found at {timestamp}. Converting to UTC.')
                        hour_group = timestamp.floor('h').tz_localize(tz='UTC')
                    date_group = timestamp.date()
                    data.append((date_group, hour_group, line.strip()))
                except ValueError as err:
                    print(f'Bad datetime data in raw file row {counter}: {err}')

        #Using the counter to skip over header/Configuration Info
        counter+=1

    print("Procesing: 100%") ##Progress Bar

    # Step 3: Load into DataFrame for grouping
    df = pd.DataFrame(data, columns=["date_group", "hour_group", "original_line"])

    # Step 4: Group by date and hour, and write to separate CSV files
    print("---- Writing Data to new files...")
    for (_, hour), group in df.groupby(["date_group", "hour_group"]):
        # Format filenames: one for date and one for hour
        # date_str = date.strftime("%Y-%m-%d")
        hour_str = hour.strftime("%Y-%m-%d_%H00")
        filename = f"{output_prefix}_{hour_str}.TXT"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(header)
            for line in group["original_line"]:
                f.write(line + "\n")

        print(f"Created: {filename}")



def setupParser():
    parser = argparse.ArgumentParser(description='NRCS Posting Script')

    parser.add_argument('-f', '--file', required=True, help='File you want to Parse into hourly files')
    parser.add_argument('-o', '--output', required=True, help='Output Directory for hourly files')

    return parser



if __name__ == '__main__':

    args = setupParser().parse_args()

    split_csv_hourly(args.file, args.output)

# added to the end of Utilities.py as Utilities member functions. They are presented separately here because I made
# other, unrelated changes to Utilities.py

import os
from HDFRoot import HDFRoot


class Utilities:

    @staticmethod
    def getline(sstream, delimiter: str = '\n') -> str:
        """replicates C++ getline functionality - reads a string until delimiter character is found
        :sstream: string stream, reference to an open file in 'read' mode
        :delimiter: the newline delimiter used in the file being read - default = '\n' Newline
        :return type: string"""
        def _gen():
            while True:
                line = sstream.readline()
                if delimiter in line:
                    yield line[0:line.index(delimiter)]
                    break
                elif line:
                    yield line
                else:
                    break

        return "".join(_gen())

    @staticmethod
    def parseLine(line: str, ds) -> None:
        """parses a line of data to a HDFDataset depending on the index attribute. This attribute must be called 'INDEX'
        and have length equal to the split line of data
        :line: string - line of data to be read
        :ds: HDFDataset
        """
        index = ds.attributes['INDEX']
        for i, x in enumerate(line.split('\t')):
            if index[i] not in ds.columns.keys():
                ds.columns[index[i]] = []
            try:
                ds.columns[index[i]].append(float(x))
            except ValueError:
                ds.columns[index[i]].append(x)

    @staticmethod
    def read(filepath: str, gp) -> None:
        """Reads in L1/L2 data using the header to organise the data storage object
            :filepath: - the full path to the file to be opened, requires a file to have begin_data and end_data before
            and after the main data body
            :gp: HDFGroup object - Input data is stored as HDFDatasets and appended to this group.

            return type: None - may be changed to bool for better error handling
            """
        begin_data = False  # set up data flag
        attrs = {}
        end_flag = 0

        with open(filepath, 'r') as f:  # open file
            key = None; index = None
            while True:  # start loop
                line = Utilities.getline(f, '\n')  # reads the file until a '\n' character is reached
                if end_flag == 0:  # end condition not met
                    if 'END_' in line:  # end conditions met
                        begin_data = False  # set to not collect data
                        ds.columnsToDataset()  # convert read data to dataset
                        end_flag = 1

                    elif line.startswith('!'):  # first lines start with '!' so can be used to determine which file is being read
                        if 'FRM' in line:
                            gp.attributes['INSTRUMENT_CAL_TYPE'] = line[1:]

                        else:
                            if 'CAL_FILE' not in gp.attributes.keys():
                                gp.attributes['CAL_FILE'] = []
                            gp.attributes['CAL_FILE'].append(line[1:])

                    elif begin_data:
                        Utilities.parseLine(line, ds)  # add the data

                    else:  # part of header
                        if 'DATA' in line:  # begin reading data
                            begin_data = True
                            name = gp.attributes['CAL_FILE'][-1] if 'CAL' in line else line[1:-1]  # name is last added Cal_file else current line
                            ds = gp.addDataset(name)
                            ds.attributes['INDEX'] = index  # populate ds attributes with column names
                            index = None
                            # populate ds attributes with header data
                            for k, v in attrs.items():
                                ds.attributes[k] = v  # set the attributes
                            attrs.clear()

                        else:  # part of header, check if attribute or column names
                            if line.startswith('['):  # if line has '[ ]' then take the next line as the attribute
                                key = line[1:-1]
                            elif key is not None:
                                attrs[key] = line
                                key = None
                            else:  # only blank lines and comments get here
                                if index is None and len(line.split(',')) > 3:  # if comma separated then must be column names!
                                    index = list(line[1:].split(','))

                else:  # check for end condition
                    # this will skip the first real line after 'END_OF_XXXXDATA', however this is always a comment so ignored.
                    if end_flag >= 3:
                        break  # end if empty lines found after [END_DATA], else more data to be read
                    elif not line:
                        end_flag += 1
                    else:
                        end_flag = 0


if __name__ == '__main__':
    # for testing purposes
    root = HDFRoot()
    root.id = "/"
    root.addGroup("UNCERTAINTY_BUDGET")
    gp = root.getGroup("UNCERTAINTY_BUDGET")
    gp.attributes['FrameType'] = 'NONE'

    inpath = r'C:\Users\ar17\in\Latest_PML_Data\raw_Stations\Cast1\Uncertainties'  # replace with path to uncertainty files
    Utilities.read(os.path.join(inpath, r'angular.txt'), gp)
    Utilities.read(os.path.join(inpath, r'thermal.txt'), gp)
    Utilities.read(os.path.join(inpath, r'polar.txt'), gp)
    Utilities.read(os.path.join(inpath, r'radcal.txt'), gp)
    print(gp.id)

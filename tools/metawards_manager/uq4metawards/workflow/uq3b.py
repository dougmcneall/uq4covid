#
# Perform step 3B of the workflow: Transform a scaled design to disease parameters
#

import sys
import argparse
import numpy as np
from typing import List
from uq4metawards.utils import transform_epidemiological_to_disease
from uq4metawards.utils import load_csv


def main():
    argv = main_parser()

    # Query the parser - is getattr() safer?
    in_location = argv.input
    out_location = argv.output
    mode_str = "x"
    if argv.force:
        mode_str = "w"
        print("force option passed, disease matrix will be over-written if it exists")

    # Touch the file system
    try:
        with open(in_location) as epidemiology_file, \
             open(out_location, mode_str) as disease_file:

            epidemiology_file, epidemiology_header_names = load_csv(epidemiology_file)

            # Only pass the first three fields to the disease builder
            # TODO: Do this by name rather than assuming order?
            disease_matrix = np.zeros((epidemiology_file.shape[0], 8))
            for i, _ in enumerate(disease_matrix):
                row = epidemiology_file[i]
                new_row = np.zeros(8)
                new_row[0:5] = np.asarray(transform_epidemiological_to_disease(row[0], row[1], row[2]))

                # Pass scale rates and repeats through from epidemiology file
                new_row[5] = row[3]
                new_row[6] = row[4]
                new_row[7] = row[5]
                disease_matrix[i] = new_row

            head_names: List[str] = ["beta[2]", "beta[3]", "progress[1]", "progress[2]", "progress[3],.scale_rate[1],.scale_rate[2],repeats"]
            header = ','.join(head_names)
            np.savetxt(fname=disease_file, X=disease_matrix, fmt="%f", delimiter=",", header=header, comments='')

            # TODO: Extra design variables need to go somewhere


    except FileExistsError:
        print("Output already exists, use -f to force overwriting")
        sys.exit(1)
    except FileNotFoundError as error:
        print(str(error.filename) + " not found.")
        sys.exit(1)
    except IOError as error:
        print("File system error: " + str(error.msg) + " when operating on " + str(error.filename))
        sys.exit(1)

    print("Done! See output at " + str(out_location))
    sys.exit(0)


#
# This arg parser is wrapped in a function for testing purposes
#
def main_parser(main_args=None):
    parser = argparse.ArgumentParser("UQ3B")
    parser.add_argument('input', metavar='<input file>', type=str, help="Input epidemiology matrix")
    parser.add_argument('output', metavar='<output file>', type=str, help="Output disease matrix")
    parser.add_argument('-f', '--force', action='store_true', help="Force over-write")
    return parser.parse_args(main_args)


if __name__ == '__main__':
    main()

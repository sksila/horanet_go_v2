#!/usr/bin/env python

"""
Rearrange content in sphinx-apidoc generated .rst files.

* Move "Module Contents" section to the top.
* Remove headers for "Module Contents", "Submodules" and "Subpackages",
  including their underlines and the following blank line.
"""

import argparse
import glob
import os


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def argument_parser():
    """Define command line arguments."""
    parser = argparse.ArgumentParser(
        description='''
        Rearrange content in sphinx-apidoc generated .rst files.
        '''
    )

    parser.add_argument(
        '-v', '--verbose',
        dest='verbose',
        default=False,
        action='store_true',
        help="""
            show more output.
            """
    )

    parser.add_argument(
        'input_file',
        metavar="INPUT_FILE",
        nargs='+',
        help="""
            file.
            """
    )

    parser.add_argument(
        '-o', '--output',
        dest='output',
        default=False,
        help="""
            folder to create new files.
            """
    )
    return parser


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def main():  # noqa: C901
    """Main program entry point."""
    global args
    parser = argument_parser()
    args = parser.parse_args()

    filenames = [glob.glob(x) for x in args.input_file]
    if len(filenames) > 0:
        filenames = reduce(lambda x, y: x + y, filenames)

    for filename in set(filenames):

        # line_num was going to be for some consistency checks, never
        # implemented but left in place.
        found = {
            'Subpackages': {'contents': False, 'line_num': None},
            'Submodules': {'contents': False, 'line_num': None},
            'Module contents': {'contents': True, 'line_num': None},
        }

        replace = [
            (' package', ' module'),
            (':undoc-members:', False)
        ]

        in_module_contents = False
        line_num = 0
        reordered = []
        module_contents = []

        if args.output:
            if not os.path.exists(args.output):
                os.makedirs(args.output)
        new_filename = '/'.join([args.output, os.path.basename(filename)])

        with open(filename, 'r') as fptr:

            for line in fptr:
                line = line.rstrip()
                discard = False

                line_num += 1

                if (
                        in_module_contents
                        and len(line) > 0
                        and line[0] not in ['.', '-', ' ']
                ):  # pylint: disable=bad-continuation
                    in_module_contents = False

                for sought in found:

                    if line.find(sought) == 0:

                        found[sought]['line_num'] = line_num
                        if found[sought]['contents']:
                            in_module_contents = True

                        discard = True
                        # discard the underlines and a blank line too
                        # _ = fptr.next()
                        # _ = fptr.next()

                if any(terms[0] in line for terms in replace):
                    for old, new in [terms for terms in replace if terms[0] in line]:
                        if not new:
                            discard = True
                            break
                        line = line.replace(old, new)

                if in_module_contents and not discard:
                    module_contents.append(line)

                elif not discard:
                    reordered.append(line)

                # print '{:<6}|{}'.format(len(line), line)

        with open(new_filename, 'w') as fptr:
            fptr.write('\n'.join(reordered[:3]))
            fptr.write('\n')
            if module_contents:
                fptr.write('\n'.join(module_contents))
                fptr.write('\n')
                if len(module_contents[-1]) > 0:
                    fptr.write('\n')
            if reordered[3:]:
                fptr.write('\n'.join(reordered[3:]))
                fptr.write('\n')


if __name__ == "__main__":
    main()

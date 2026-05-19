from pathlib import Path
import subprocess

def python_sort(file_in: Path, file_out: Path) -> None:
    """
    Sort tsv file using python built-in sort
    :param file_in: tsv file to read from
    :param file_out: tsv file to write to
    """
    with open(file_in, 'r') as input, open(file_out, 'w') as output:
        lines = input.readlines()
        for zn in sorted(lines, key=lambda x: (int(x.split('\t')[1]), x.split('\t')[0])):
            output.write(zn)


def util_sort(file_in: Path, file_out: Path) -> None:
    """
    Sort tsv file using sort util
    :param file_in: tsv file to read from
    :param file_out: tsv file to write to
    """
    subprocess.run(['sort', '-k2,2n', file_in, '-o', file_out], check = True)

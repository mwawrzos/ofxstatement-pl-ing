import csv
import itertools
import ofxstatement.tool as tool
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('CSV')
args = parser.parse_args()


def assert_header(reader, column):
    row = next(reader)
    if row[0] == column:
        return row
    else:
        raise RuntimeError(f'\n'
                           f"Expected row:   '{column}'\n"
                           f" instead found: '{row[0]}'\n"
                           f' in input file: {self.fin}')


with open(args.CSV, encoding='cp1250') as f:
    reader = csv.reader(f, delimiter=';')
    header = list(itertools.islice(reader, 0, 7))
    rachunki = assert_header(reader, "Wybrane rachunki:")
    accounts = {}
    rows = {}
    while True:
        row = next(reader)
        if row == []:
            break
        accout_type, _, account_no, _ = row
        accounts[f"""'{account_no.replace(" ", "")} '"""] = row
        rows[f"""'{account_no.replace(" ", "")} '"""] = []
    middle = list(itertools.islice(reader, 0, 8))
    transakcje = assert_header(reader, 'Data transakcji')
    rows = {}
    for line in reader:
        if line == []:
            break

        name = line.pop(14)
        row = rows.get(name, [])
        row.append(line)
        # print(name, line)
        rows[name] = row
    footter = [[]] + list(reader)

for account in rows:
    if len(rows[account]) == 0:
        print(account)
    fname = f'''{account}'''
    with open(f'{fname}.csv', 'w', encoding='cp1250') as f:
        writer = csv.writer(f, delimiter=';')
        print(len(rows[account]))
        writer.writerows(itertools.chain(
            header,
            [rachunki], [[account, '', account, ''],[]],
            middle,
            [transakcje], rows[account],
            footter,
        ))
    tool.convert(tool.argparse.Namespace(type='ingpl', input=f'{fname}.csv', output=f'{fname}.ofx'))

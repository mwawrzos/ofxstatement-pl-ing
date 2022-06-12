import csv
import itertools

from ofxstatement import statement
from ofxstatement.plugin import Plugin
from ofxstatement.parser import CsvStatementParser
from ofxstatement.parser import StatementParser
from ofxstatement.statement import StatementLine

class IngPlPlugin(Plugin):
    """ING Poland Plugin
    """

    def get_parser(self, filename):
        f = open(filename, 'r', encoding=self.settings.get("charset", "cp1250"))
        parser = IngPlParser(f)
        return parser

class IngPlParser(CsvStatementParser):

    date_format = "%Y-%m-%d"
    mappings = {
        'check_no': 4,
        'date': 0,
        'payee': 2,
        'memo': 3,
        'amount': 8,
    }

    currency = None
    reader = None

    def assert_header(self, column):
        row = next(self.reader)
        if row[0] != column:
            raise RuntimeError(f'\n'
                               f"Expected row:   '{column}'\n"
                               f" instead found: '{row[0]}'\n"
                               f' in input file: {self.fin}')

    def parse(self):
        """Main entry point for parsers

        super() implementation will call to split_records and parse_record to
        process the file.
        """
        self.reader = csv.reader(self.fin, delimiter=';')


        bank_id = next(self.reader)[5]
        self.reader = itertools.islice(self.reader, 6, None)
        self.assert_header("Wybrane rachunki:")
        

        account_type, _, account_id, _ = next(self.reader)

        row = next(self.reader)
        if row != []:
            raise RuntimeError(f'Only an export of one account supported.'
                         f' Found a second account in the export: {row}')

        self.reader = itertools.islice(self.reader, 8, None)
        self.assert_header('Data transakcji')

        stmt = super(IngPlParser, self).parse()
        stmt.account_type = "SAVINGS" if "Oszczędnościowe" in account_type or "Saver" in account_type else "CHECKING"
        stmt.currency = account_type[-4:-1]
        stmt.bank_id = bank_id

        statement.recalculate_balance(stmt)

        return stmt

    def split_records(self):
        """Return iterable object consisting of a line per transaction
        """
        
        return self.reader

    def parse_record(self, line):
        """Parse given transaction line and return StatementLine object
        """

        if len(line) < 15 or line[9] == '':
            return

        saldo = line[14]
        saldo_curr = line[15]
        trans_curr = line[9]

        if self.currency is None:
            self.currency = saldo_curr
        
        if self.currency != saldo_curr or self.currency != trans_curr:
            print(line)
            raise ValueError('Different currencies not supported!')

        line[8] = line[8].replace(",", ".")
        line[2] = f'{line[2]} {line[4]}'
        if line[3].strip().startswith('Płatność BLIK'):
            chunks = line[3].split(' ')
            idx = chunks.index('transakcji')
            line[2] = f'{line[2]} {" ".join(chunks[idx+2:])}'

        stmtline = super(IngPlParser, self).parse_record(line)

        stmtline.trntype = 'DEBIT' if stmtline.amount < 0 else 'CREDIT'

        stmtline.id = line[7]

        return stmtline

import json
import re
from enum import Enum, unique


@unique
class CellType(Enum):
    AS = 'AS'
    DOT = 'Dot'
    COMMA = 'Comma'
    EQUALS = 'Equals'
    OPERATOR = 'Operator'
    KEYWORD = 'Key Word'
    IDENTIFIER = 'Identifier'
    OPEN_BRACKET = 'Open Bracket'
    CLOSE_BRACKET = 'Close Bracket'
    COMPLEX_KEYWORD = 'Complex keyword'
    COMBINATION_IDENTIFIER = 'Combination Identifier'


# SQL_HEAD_KEY_WORD = ['ALTER', 'BACKUP', 'CREATE', 'DROP', 'FOREIGN', 'GROUP', 'LEFT', 'INNER', 'RIGHT', 'INSERT',
#                      'IS', 'OUTER', 'ORDER', 'PRIMARY', 'TRUNCATE', 'UNION']
#


def _decompose_special_characters(item) -> [str]:
    result = []
    current_word = ''

    for c in item:
        if 0x28 <= ord(c) <= 0x2f or 0x3a < ord(c) <= 0x3f:
            if len(current_word) > 0:
                result.append(current_word)
                current_word = ''

            result.append(c)
        else:
            current_word += c

    if len(current_word) > 0:
        result.append(current_word)

    return result


class Item(object):
    def __init__(self, content=None, ct=None):
        self._content = content
        self._type = ct

    def to_json(self):
        return str(self._content)

    def __str__(self):
        return self.to_json()


class Group(object):
    def __init__(self):
        pass


class Cell(object):
    def __init__(self, content=None, v_type=None):
        self._content = content
        self._type = v_type

    def __str__(self):
        return json.dumps(self.to_json())

    def to_json(self):
        if isinstance(self._content, list):
            return {self._type.value: [item.to_json() for item in self._content]}
        else:
            return {self._type.value: str(self._content)}


class Bracket(Cell):
    def __init__(self):
        super().__init__(v_type=CellType.OPEN_BRACKET)

    def insert(self, item: Cell):
        if self._content is None:
            self._content = [item]
        else:
            self._content.append(item)

    def to_json(self):
        if isinstance(self._content, list):
            return {'Bracket': [item.to_json() for item in self._content]}
        else:
            return {'Bracket': '()'}


class Parser(object):
    def __init__(self, keyword: dict):
        self._keyword = keyword
        self._words = []
        self._now = self._count = 0

    def _cell_type(self, w: str):
        if w.upper() in self._keyword['SQL_KEY_WORD']:
            return CellType.KEYWORD

        match w.upper():
            case '(':
                return CellType.OPEN_BRACKET
            case ')':
                return CellType.CLOSE_BRACKET
            case '.':
                return CellType.DOT
            case ',':
                return CellType.COMMA
            case '=':
                return CellType.EQUALS
            case '+' | '-' | '*' | '/':
                return CellType.OPERATOR

        return CellType.IDENTIFIER

    def mark_keyword(self) -> Cell:
        full_name = self._words[self._now]
        self._now += 1

        while self._now < self._count:
            word = full_name + ' ' + self._words[self._now]
            if self._cell_type(word) == CellType.KEYWORD:
                full_name = word
                self._now += 1
            else:
                break

        return Cell(full_name, CellType.KEYWORD)

    def mark_identifier_dot(self) -> Cell:
        full_name = ''
        dot = True

        while self._now < self._count:
            word_type = self._cell_type(self._words[self._now])
            if word_type == CellType.IDENTIFIER and dot:
                full_name += self._words[self._now]
                dot = False
                self._now += 1

            elif word_type == CellType.DOT and not dot:
                full_name += self._words[self._now]
                dot = True
                self._now += 1

            else:
                break

        return Cell(full_name, CellType.IDENTIFIER)

    def mark_identifier(self) -> Cell:
        result = []
        over = False
        while not over and self._now < self._count:
            word_type = self._cell_type(self._words[self._now])
            match word_type:
                case CellType.IDENTIFIER:
                    result.append(self.mark_identifier_dot())

                case CellType.OPEN_BRACKET:
                    result.append(self.mark_bracket())

                case CellType.EQUALS | CellType.OPERATOR | CellType.IDENTIFIER:
                    result.append(Cell(self._words[self._now], word_type))
                    self._now += 1

                case CellType.KEYWORD:
                    if self._words[self._now].upper() == 'AS':
                        result.append(Cell(self._words[self._now], word_type))
                        self._now += 1
                    else:
                        over = True

                case CellType.COMMA:
                    result.append(Cell(self._words[self._now], word_type))
                    self._now += 1
                    over = True

                case _:
                    over = True

        return Cell(result, CellType.COMBINATION_IDENTIFIER) if len(result) > 1 else result[0]

    def mark_bracket(self) -> Cell:
        mb = Bracket()
        assert self._words[self._now] == '('
        self._now += 1

        finish = False
        while not finish and self._now < self._count:
            word_type = self._cell_type(self._words[self._now])
            match word_type:
                case CellType.CLOSE_BRACKET:
                    self._now += 1
                    finish = True

                case CellType.IDENTIFIER:
                    mb.insert(self.mark_identifier())

                case CellType.OPEN_BRACKET:
                    mb.insert(self.mark_bracket())

                case CellType.KEYWORD:
                    mb.insert(self.mark_keyword())

                case _:
                    mb.insert(Cell(self._words[self._now], word_type))
                    self._now += 1

        return mb

    def mark(self, sql):
        sql = sql.replace('\n', ' ').replace('\t', ' ').replace('\u3000', ' ')
        all_c = re.compile(r'[^()*+,\-./:;<=>?]+')

        self._words = []
        for item in [a for a in sql.split(' ') if a != '']:
            if all_c.fullmatch(item):
                self._words.append(item)
            else:
                self._words += _decompose_special_characters(item)

        self._count = len(self._words)
        self._now = 0

        result = []
        while self._now < self._count:
            word_type = self._cell_type(self._words[self._now])
            if word_type == CellType.IDENTIFIER:
                result.append(self.mark_identifier())

            elif word_type == CellType.KEYWORD:
                result.append(self.mark_keyword())

            elif word_type == CellType.OPEN_BRACKET:
                result.append(self.mark_bracket())

            elif word_type == CellType.CLOSE_BRACKET:
                raise TypeError(f"Invalid close bracket at {self._now}.")

            else:
                result.append(Cell(self._words[self._now], word_type))
                self._now += 1

        return result


def decompose_string(keyword, sql):
    parser = Parser(keyword)
    return parser.mark(sql)
    # return mark_member(result)


def main():
    print("Begin...")
    with open('keyword.json', 'rt') as fp:
        keyword = json.load(fp)

    with open("sample.sql", 'rt') as fp:
        sql = fp.read()

    result = [item.to_json() for item in decompose_string(keyword, sql)]
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    exit(main())

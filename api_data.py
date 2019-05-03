import codecs
import json
from collections import defaultdict, OrderedDict
from lxml import etree

from entry_data import word_dict
from entry import EntryEncoder


NANORI = etree.XPath('./reading_meaning//nanori')
ON_READINGS = etree.XPath('./reading_meaning//reading[@r_type="ja_on"]')
KUN_READINGS = etree.XPath('./reading_meaning//reading[@r_type="ja_kun"]')
MEANINGS = etree.XPath('./reading_meaning//meaning[not(@m_lang)]')
GRADE = etree.XPath('./misc/grade')
STROKE_COUNT = etree.XPath('./misc/stroke_count')
CODEPOINT = etree.XPath('.//cp_value[@cp_type="ucs"]')
JLPT = etree.XPath('./misc/jlpt')
LITERAL = etree.XPath('literal')


def nanori(character):
    readings = NANORI(character)
    return [reading.text for reading in readings]


def on_readings(character):
    readings = ON_READINGS(character)
    return [reading.text for reading in readings]


def kun_readings(character):
    readings = KUN_READINGS(character)
    return [reading.text for reading in readings]


def meanings(character):
    meanings = MEANINGS(character)
    return [meaning.text for meaning in meanings]


def grade(character):
    try:
        return int(GRADE(character)[0].text)
    except (AttributeError, IndexError):
        return None


def stroke_count(character):
    return int(STROKE_COUNT(character)[0].text)


def unicode_codepoint(character):
    return CODEPOINT(character)[0].text


def jlpt(character):
    try:
        return int(JLPT(character)[0].text)
    except (AttributeError, IndexError):
        return None


def literal(character):
    return LITERAL(character)[0].text


def kanji_data(character):
    return OrderedDict([
        ('kanji', literal(character)),
        ('grade', grade(character)),
        ('stroke_count', stroke_count(character)),
        ('meanings', meanings(character)),
        ('kun_readings', kun_readings(character)),
        ('on_readings', on_readings(character)),
        ('name_readings', nanori(character)),
        ('jlpt', jlpt(character)),
        ('unicode', unicode_codepoint(character)),
        ])


def reading_data(kanjis):
    readings = defaultdict(lambda: {'regular': [], 'name': []})

    for kanji in kanjis:
        literal = kanji['kanji']
        for reading in kanji['kun_readings'] + kanji['on_readings']:
            readings[reading]['regular'].append(literal)
        for reading in kanji['name_readings']:
            readings[reading]['name'].append(literal)

    return [OrderedDict([
        ('reading', reading),
        ('main_kanji', data['regular']),
        ('name_kanji', data['name']),
        ]) for reading, data in readings.items()]


def CJK_compatibility(character):
    return u'\uF900' <= literal(character) <= u'\uFAFF'


def dump_json(filename, obj):
    with codecs.open(filename, 'w', 'utf8') as f:
        json.dump(obj, f, ensure_ascii=False, cls=EntryEncoder)


if __name__ == '__main__':
    VERSION_PATH = 'v1'
    KANJI_DIR = 'out/' + VERSION_PATH + '/kanji/'
    WORD_DIR = 'out/' + VERSION_PATH + '/words/'
    READING_DIR = 'out/' + VERSION_PATH + '/reading/'
    JOUYOU_GRADES = [1, 2, 3, 4, 5, 6, 8]
    JINMEIYOU_GRADES = [9, 10]

    kanjidic_root = etree.parse('kanjidic2.xml')
    characters = kanjidic_root.xpath('./character')

    kanjis = [
            kanji_data(character)
            for character in characters
            if not CJK_compatibility(character)
            ]

    jmdict_entries = etree.parse('JMDict').xpath('//entry')
    kanji_to_entries = word_dict(jmdict_entries)

    readings = reading_data(kanjis)

    all_kanji = [kanji['kanji'] for kanji in kanjis]

    jouyou_kanji = [
            kanji['kanji']
            for kanji in kanjis
            if kanji['grade'] in JOUYOU_GRADES
            ]

    jinmeiyou_kanji = [
            kanji['kanji']
            for kanji in kanjis
            if kanji['grade'] in JINMEIYOU_GRADES
            ]

    for kanji in kanjis:
        dump_json(KANJI_DIR + kanji['kanji'], kanji)
        try:
            entries = kanji_to_entries[kanji['kanji']]
            dump_json(WORD_DIR + kanji['kanji'], entries)
        except KeyError:
            continue

    for reading in readings:
        dump_json(READING_DIR + reading['reading'], reading)

    dump_json(KANJI_DIR + 'all', all_kanji)
    dump_json(KANJI_DIR + 'jouyou', jouyou_kanji)
    dump_json(KANJI_DIR + 'joyo', jouyou_kanji)
    dump_json(KANJI_DIR + 'jinmeiyou', jinmeiyou_kanji)
    dump_json(KANJI_DIR + 'jinmeiyo', jinmeiyou_kanji)

    for grade_numeral in JOUYOU_GRADES:
        grade_kanji = [
                kanji['kanji']
                for kanji in kanjis
                if kanji['grade'] == grade_numeral
                ]

        dump_json(KANJI_DIR + 'grade-' + str(grade_numeral), grade_kanji)

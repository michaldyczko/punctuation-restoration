import functools
import glob
import json
import os
import random
from random import randint

import regex as re
import tqdm
from num2words import num2words
from regex.regex import findall, match
from tqdm.contrib.concurrent import process_map

from parsing.cleaners import polish_cleaners

TO_OMMIT = {'"', '„', '”', '(', ')', "'", "»", "«", '…'}

p_dct = {
    "": "O",
    ",": "COMMA",
    "-": "COMMA",
    ":": "COLON",
    ".": "PERIOD",
    "!": "PERIOD",
    ";": "COMMA",
    "[": "COMMA",
    "]": "COMMA",
    "–": "COMMA",
    "?": "QUESTION",
    '...': 'COMMA',
    '..': 'PERIOD',
}


def parse(sentence):
    ls = []
    for part in sentence.split():
        if part in TO_OMMIT:
            continue
        if part in p_dct:
            try:
                ls[-1][1] = p_dct[part]
            except IndexError as e:
                pass
        else:
            ls.append([part, "O"])
    return ls


def random_with_N_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    return randint(range_start, range_end)


def convert_scientific_notation(match_obj):
    number = re.sub('[\t ]', '', match_obj.group(1)).replace(',', '.')
    if number == "":
        return match_obj.group(0)
    else:
        if float(number) % 1 == 0:
            number = str(int(float(number)))
    exponent = int(match_obj.group(3))
    if exponent > 0:
        return f" {number} razy dziesięć do {exponent}"
    return str(exponent)


def convert_less_more_than(match_obj):
    less_more = match_obj.group(1)
    number = int(match_obj.group(2))
    if number > 0:
        return f"{less_more} niż {number}"
    return f"{less_more} niż {number}"


def convert_in(match_obj):
    number = int(match_obj.group(1))
    if number > 0:
        number = num2words(number, ordinal=True, lang="pl")
        if number.endswith('y'):
            number = number[:-1] + "u"
        return f"w ciągu {number}"
    return f"w ciągu {number}"


def fix_parentheses(match_obj):
    first_part = match_obj.group(1)
    second_part = match_obj.group(2)
    return "(" + re.sub('\n', '', first_part) + re.sub('\n', '', second_part) + ")"


def fix_ranges(match_obj):
    part1 = match_obj.group(1)
    part2 = match_obj.group(2)
    part3 = match_obj.group(3)
    part4 = match_obj.group(4)
    part5 = match_obj.group(5)
    part6 = match_obj.group(6)

    part2 = re.sub(' ', '', part2)
    part2 = re.sub('.', ',', part2)
    part5 = re.sub(' ', '', part2)
    part5 = re.sub('.', ',', part2)

    return f"{part1}{part2}{part3}-{part4}{part5}{part6}"


def fix_numbers(match_obj):
    part1 = match_obj.group(1)
    part2 = match_obj.group(2)
    part4 = match_obj.group(4)

    part2 = re.sub(' ', '', part2)

    return f"{part1} {part2} {part4}"


def change_suffix(string, suffix):
    if suffix is None:
        return string
    words = []
    for word in string.split():
        if word[-1] == 'i' and suffix == "ego":
            words.append(word + suffix)
        elif word[-1] == 'i' and suffix == "m":
            words.append(word + suffix)
        elif word[-1] == 'y' and suffix == "ego":
            words.append(word[:-1] + suffix)
        elif word[-1] == 'y' and suffix == "m":
            words.append(word + suffix)
        else:
            words.append(word)
    return " ".join(words)


def convert_full_date(match_obj):
    month = match_obj.group(3)
    replacements = {
        'stycznai': 'stycznia',
        'stycznie': 'stycznia',
        'stycza': 'stycznia',
        'styczna': 'stycznia',
        'styczen': 'styczeń',
        'kwiecien': 'kwiecień',
        'sierpnie': 'sierpnia',
        'sierpien': 'sierpień',
        'siwerpnia': 'sierpnia',
        'wrzesien': 'wrzesień',
        'pazdziernika': 'października',
        'pazdziernik': 'pazdziernik',
        'grudzien': 'grudzień',
        'grudfnia': 'grudnia',
        'grudni': 'grudnia',
        'june': 'czerwiec',
        'november': 'listopad',
        'vii': 'lipiec',
        'viii': 'sierpień',
    }
    if month.lower() in [
        'stycznia',
        'stycznai',
        'styczniu',
        'stycznie',
        'stycza',
        'styczna',
        'styczeń',
        'styczen',
        'lutego',
        'lutym',
        'luty',
        'marca',
        'marzec',
        'kwietnia',
        'kwiecień',
        'kwiecien',
        'kwietniu',
        'maja',
        'majem',
        'maj',
        'maju',
        'czerwca',
        'czerwiec',
        'czerwcem',
        'lipiec',
        'lipca',
        'sierpnia',
        'sierpnie',
        'sierpień',
        'sierpien',
        'siwerpnia',
        'września',
        'wrzesnia',
        'wrzesień',
        'wrzesien',
        'października',
        'paździenika',
        'październiku',
        'październik',
        'pazdziernika',
        'pazdziernik',
        'listopad',
        'listopada',
        'listopadzie',
        'grudnia',
        'grudzień',
        'grudzien',
        'grudniu',
        'grudni',
        'grudfnia',
        'june',
        'november',
        'vii',
        'viii',
    ]:
        if month in replacements:
            month = replacements[month]
        prefix = match_obj.group(1)
        day = num2words(match_obj.group(2), to='ordinal', lang='pl')
        day = change_suffix(day, suffix='ego')
        year = num2words(match_obj.group(4), to='ordinal', lang='pl')
        year = change_suffix(year, suffix='ego')
        return f"{prefix} {day} {month} {year} roku "
    else:
        return match_obj.group(0)


def convert_full_time(match_obj):
    prefix = f"{match_obj.group(1)}{match_obj.group(2)}"
    if prefix in ['o', 'po']:
        form = "godzinie"
        suffix = "ej"
    elif prefix in ['na']:
        form = "godzinę"
        suffix = "ą"
    elif prefix in ['przed']:
        form = "godziną"
        suffix = "ą"
    elif prefix in ['do']:
        form = "godziny"
        suffix = "ej"
    else:
        form = "godzina"
        suffix = "a"
    hours = change_suffix(
        num2words(
            int(match_obj.group(4)),
            to=('ordinal' if int(match_obj.group(4)) != 0 else 'cardinal'),
            lang='pl',
        ),
        suffix=suffix,
    )
    if match_obj.group(5) is not None:
        minutes = ('zero ' if int(match_obj.group(5)[1:]) < 10 else '') + (
            num2words(int(match_obj.group(5)[1:]), lang='pl')
        )
    else:
        minutes = ''
    if match_obj.group(6) is not None:
        seconds = ('zero ' if int(match_obj.group(6)[1:]) < 10 else '') + (
            num2words(int(match_obj.group(6)[1:]), lang='pl')
        )
    else:
        seconds = ''
    if minutes == '' and match_obj.group(3) is None:
        result = match_obj.group(0)
    else:
        result = f"{prefix} {form} {hours} {minutes} {seconds} "
    return result


def clean_text_parsed(txt):
    # remove lines not ending with .
    txt = "\n".join((l for l in txt.splitlines() if l.endswith('.')))
    # move matched parentheses to one line
    txt = re.sub(r'\(([^)]+?)\n([^(]+?)\)', fix_parentheses, txt)
    # remove matched parentheses
    while True:
        txt, n = re.subn(r'\(.*?\)', '', txt)
        if n == 0:
            break
    # remove lines without matching parentheses
    txt = re.sub(r'^.*\([^)\n]*$\n', '', txt, flags=re.M)
    # remove lines with capital letter inside
    # txt = re.sub(r'^(.+)([A-Z]+)(.+)$\n', '', txt, flags=re.M)
    # remove lines without first capital letter
    txt = re.sub(r'^[^A-ZĄĆĘŁŃÓŚŹŻ]+.*$\n', '', txt, flags=re.M)
    # remove lines with http
    txt = re.sub(r'^(.+)http(.+)$\n', '', txt, flags=re.M)
    # remove lines with 
    txt = re.sub(r'^(.+)(.+)$\n', '', txt, flags=re.M)
    # remove lines with "Reproduction is authorised"
    txt = re.sub(r'^(.*)Reproduction is authorised(.*)$\n', '', txt, flags=re.M)
    txt = re.sub(r'^[^(\n]*\).*$\n', '', txt, flags=re.M)
    txt = re.sub(
        r'[ \t]?(\p{P})[ \t]?', r' \g<1> ', txt
    )  # add whitespace next to punctuation
    txt = re.sub(
        r'^.*w ciągu [0-9]+.*$\n', '', txt, flags=re.M
    )  # remove lines with "w ciągu {liczba}"
    txt = re.sub(r'([ \t]+)', ' ', txt)  # remove whitespace multiplication
    txt = re.sub(r'(\D)1[\t ]?[°º]C', r'\g<1> stopnia Celsjusza', txt)  # 1° -> stopień
    txt = re.sub(r'(\D)1\?[°º]F', r'\g<1> stopnia Fahrenheita', txt)
    txt = re.sub(r'(\D)1\?[°º]', r'\g<1> stopnia', txt)
    txt = re.sub(r'([0-9]+)[\t ]?°C', r'\g<1> stopni Celsjusza', txt)  # ° -> stopni
    txt = re.sub(r'([0-9]+)[\t ]?°F', r'\g<1> stopni Fahrenheita', txt)
    txt = re.sub(r'([0-9]+)[\t ]?°', r'\g<1> stopni', txt)
    txt = re.sub(r'\.? ?•', ',', txt)  # • -> ,
    txt = re.sub(r':[\t ]*,', ':', txt)  # : , -> :
    txt = re.sub(r'·', 'razy', txt)  # · , -> razy
    txt = re.sub(
        r'^[\d[\t ]\p{S}\p{P}]+[\t ]+', '', txt, flags=re.M
    )  # remove digits, whitespace, punctuation oand symbols from the beginning of the line
    txt = re.sub(r'im \.', r"domięśniowo", txt)
    txt = re.sub(r'i \. m \.', r"domięśniowo", txt)
    txt = re.sub(r'sc \.', r"podskórnie", txt)
    txt = re.sub(r's \. c \.', r"podskórnie", txt)
    txt = re.sub(r'iv \.', r"dożylnie", txt)
    txt = re.sub(r'p \. o \.', r"doustnie", txt)
    txt = re.sub(r'q \. d \.', r"codziennie", txt)
    txt = re.sub(r'tj \.', r"to jest", txt)
    txt = re.sub(r't \. j \.', r"to jest", txt)
    txt = re.sub(r'j \. m \.', r" jednostek", txt)
    txt = re.sub(r' j \.?', r" jednostek ", txt)
    txt = re.sub(r'[\t ]?½[\t ]?', r" pół ", txt)
    txt = re.sub(r'[\t ]?²[\t ]?', r" kwadratowych ", txt)
    txt = re.sub(r'[\t ]?³[\t ]?', r" sześciennych ", txt)
    txt = re.sub(r'm \. in \.', r"między innymi", txt)
    txt = re.sub(r'm \. c \.?', r"masy ciała", txt)
    txt = re.sub(r'np \.', r"na przykład", txt)
    txt = re.sub(r'nt \.', r"na temat", txt)
    txt = re.sub(r'tzn \.', r"to znaczy", txt)
    txt = re.sub(r'tys \.', r"tysięcy", txt)
    txt = re.sub(r'obj \.', r"objętość", txt)
    txt = re.sub(r'dot \.', r"dotyczących", txt)
    txt = re.sub(r'itp \.', r"i tym podobne", txt)
    txt = re.sub(r'ok \.', r"około", txt)
    txt = re.sub(r' godz \.', r" godzina", txt)
    txt = re.sub(
        r'tzw \.',
        lambda match_obj: random.choice(['tak zwany', 'tak zwaną', 'tak zwanym']),
        txt,
    )
    txt = re.sub(r'ds \.', 'do spraw', txt)
    txt = re.sub(r'mc \.', r"masy ciała", txt)
    txt = re.sub(r'p \. c \.?', r"powierzchni ciała", txt)
    txt = re.sub(r'pow \. ciała', r"powierzchni ciała", txt)
    txt = re.sub(r'pc \.?', r"powierzchni ciała", txt)
    txt = re.sub(r'p \. m - r \.', r"płyn mózgowo-rdzeniowy", txt)
    txt = re.sub(r'e - mail', r"imejl", txt)
    txt = re.sub(r'rodków', r"środków", txt)  # missing letters
    txt = re.sub(r'mo e', r"może", txt)
    txt = re.sub(r'dotycz ce', r"dotyczące", txt)
    txt = re.sub(r'(N|n)ale y', r"g<1>ależy", txt)
    txt = re.sub(r'(J|j)e li', r"g<1>eśli", txt)
    txt = re.sub(r'(T|t)ak e', r"g<1>akże", txt)
    txt = re.sub(r' si ', r" się ", txt)
    txt = re.sub(r', e', r", że", txt)
    while True:
        txt, n = re.subn(r' [ąćęńóśźż] ', '', txt)
        if n == 0:
            break
    txt = re.sub(r'^[^a-zA-Z]+$\n', '', txt, flags=re.M)  # remove lines without letters
    txt = re.sub(
        r'^.*\p{S}.*$\n', '', txt, flags=re.M
    )  # remove lines with special symbols
    txt = re.sub(
        r'^.*(d \. o \. o \.).*$\n', '', txt, flags=re.M
    )  # remove lines with d . o . o .
    txt = re.sub(
        r'^.*(s \. r \. o \.).*$\n', '', txt, flags=re.M
    )  # remove lines with s . r . o .
    txt = re.sub(r'^.*(Kύπρος).*$\n', '', txt, flags=re.M)  # remove lines with Kύπρος
    txt = re.sub(
        r'^.*((\. ){4}).*$\n', '', txt, flags=re.M
    )  # remove lines with too many dots
    txt = re.sub(r'([ \t]+)', ' ', txt)  # reformatting
    txt = re.sub(r',[\t ]*(-|–)', ';', txt)
    txt = re.sub(r';,', ';', txt)
    txt = re.sub(r'([0-9,]+?)[\t ]*(-|–)[\t ]*([0-9,]+?)', r'\g<1>-\g<3>', txt)
    txt = re.sub(r'[^[\t ]](-|–)[\t ]', r'-', txt)
    txt = re.sub(r'[\t ]*/[\t ]*', r'/', txt)
    txt = re.sub(
        r'(\d)[\t ]*,[\t ]*(\d+)([\t ]*(mg|zł|ha|m[^a-z]|hm|mln|metra|punktów|km|cm|mm|dm|os\.|\%|miliona|tysięcy))',
        r'\g<1>,\g<2>\g<3>',
        txt,
    )
    txt = re.sub(r'( ? - ?)?([0-9]+)( ? - ?)([^\d\p{P}])', r'\g<1>\g<2>-\g<4>', txt)
    while True:
        txt, n = re.subn(
            r'([^ \d,]+) (\d+) , (\d+) ((?!i|lub)[^ \d,/]+)',
            r'\g<1> \g<2>,\g<3> \g<4>',
            txt,
        )
        if n == 0:
            break
    txt = re.sub(r'([0-9]+)([\. ]+)([0-9]+)-([0-9]+)([\. ]+)([0-9]+)', fix_ranges, txt)
    txt = re.sub(r'(\D) (([0-9]+ ?)+) (\D)', fix_numbers, txt)
    txt = re.sub(r'(\D)[\t ]-[\t ](\D)', r'\g<1>-\g<2>', txt, flags=re.M)
    while True:
        txt, n = re.subn(r'(\d) \. ((\d ?)\.?)', r'\g<1>.\g<3>', txt)
        if n == 0:
            break
    txt = re.sub(r'(\. )+', '. ', txt)
    txt = re.sub(r'\. ,', ',', txt)
    txt = re.sub(r', \.', ',', txt)
    txt = re.sub(r'„', '"', txt)
    txt = re.sub(r'”', '"', txt)
    txt = re.sub(r'–', '-', txt)
    txt = re.sub(
        r'(\D) \. ([^$])', r'\g<1> . \n\g<2>', txt, flags=re.M
    )  # split lines in dots
    txt = re.sub(r'([ \t]+)', ' ', txt)  # remove whitespace multiplication
    txt = re.sub(
        r'([\t ]?)([^.[\t ]])[\t ]*$', r'\g<1>\g<2> . ', txt, flags=re.M
    )  # add periods
    txt = "\n".join(
        (l for l in txt.splitlines() if len(l.split()) >= 10)
    )  # keep lines with at least 5 words
    txt = re.sub(r'^.*(--).*$\n', '', txt, flags=re.M)  # remove lines with --
    txt = re.sub(r'[ \t]?([.,])', r'\g<1>', txt)  # remove whitespace before punctuation
    txt = re.sub(
        r'([.,])[ \t]+', r'\g<1> ', txt
    )  # remove whitespace next to punctuation
    txt = re.sub(r'"[\t ]*(.*?)[\t ]*"', lambda m: f'"{m.group(1).strip()}"', txt)
    txt = re.sub(r'[\t ]+:[\t ]*', r': ', txt)
    txt = re.sub(r'[\t ]+;[\t ]*', r'; ', txt)
    txt = re.sub(r',+', r',', txt)
    txt = re.sub(r',\.', r'.', txt)
    txt = re.sub(r'([0-9]+)[\t ]*:[\t ]*([0-9]+)', r'\g<1>:\g<2>', txt)
    return txt


def clean_text_tts(txt):
    txt = re.sub(
        r'([0-9 ]+(, [0-9]+)?)[\t ]?x[\t ]?10([0-9]+)', convert_scientific_notation, txt
    )  # convert scientific notation to text
    txt = re.sub(
        r'(mniej|więcej) niż ([0-9]+)', convert_less_more_than, txt
    )  # convert "mniej|więcej {liczba}" to "mniej|więcej {liczebnik} dni"
    txt = re.sub(r'[\t ]?/[\t ]*m2 ', ' na metr kwadratowy ', txt)  # / -> na
    txt = re.sub(r'[\t ]?/[\t ]*[lL]', ' na litr', txt)
    txt = re.sub(r'[\t ]?/[\t ]*dl', ' na decylitr', txt)
    txt = re.sub(r'[\t ]?/[\t ]*ml', ' na mililitr', txt)
    txt = re.sub(r'[\t ]?/[\t ]*h', ' na godzinę', txt)
    txt = re.sub(r'[\t ]?/[\t ]*kg', ' na kilogram', txt)
    txt = re.sub(r'[\t ]?/[\t ]*g', ' na gram', txt)
    txt = re.sub(r'[\t ]?/[\t ]*dobę', ' na dobę', txt)
    txt = re.sub(r'[\t ]?/[\t ]*mikrol', ' na mikrolitr', txt)
    txt = re.sub(r'[\t ]?/[\t ]*min( ?)\.?', r' na minutę\g<1>', txt)
    txt = re.sub(r'mmol', "milimol", txt)  # abbreviations
    txt = re.sub(r'([0-9]|[\t ]+)ml([^a-z])', r"\g<1> mililitr \g<2>", txt)
    txt = re.sub(r'([0-9]|[\t ]+)cm([^a-z])', r"\g<1> centymetr \g<2>", txt)
    txt = re.sub(r'([0-9]|[\t ]+)mg([^a-z])', r'\g<1> miligramów \g<2>', txt)
    txt = re.sub(r'([0-9]|[\t ]+)wg([^a-z])', r"\g<1> według \g<2>", txt)
    txt = re.sub(r'([0-9]|[\t ]+)kg([^a-z])', r"\g<1> kilogram \g<2>", txt)
    txt = re.sub(r'([0-9]|[\t ]+)μg([^a-z])', r"\g<1> mikrogram \g<2>", txt)
    txt = re.sub(r'([0-9]|[\t ]+)ng([^a-z])', r"\g<1> nanogram \g<2>", txt)
    txt = re.sub(r'([0-9]|[\t ]+)dl([^a-z])', r"\g<1> decylitr \g<2>", txt)
    txt = re.sub(r'([0-9]|[\t ]+)KM([^a-z])', r"\g<1> koni mechanicznych \g<2>", txt)
    txt = re.sub(r'1[\t ]+l([^a-z])', r' litr\g<1>', txt)
    txt = re.sub(r'(2|3|4)[\t ]+l([^a-z])', r' litry\g<1>', txt)
    txt = re.sub(r'\d[\t ]+l([^a-z])', r' litrów\g<1>', txt)
    txt = re.sub(r'([0-9]|[\t ]+)min([^a-z])', r"\g<1> minut ", txt)
    txt = re.sub(r'([0-9]|[\t ]+)g([^a-z])', r"\g<1> gram ", txt)
    txt = re.sub(r'([0-9]|[\t ]+)h([^a-z])', r"\g<1> godzin ", txt)
    txt = re.sub(r'[\t ]x[\t ]', r" razy ", txt)
    txt = re.sub(r'[\t ]?±[\t ]?', ' plus minus ', txt, flags=re.M)
    txt = re.sub(r'[\t ]?\+[\t ]?', ' plus ', txt, flags=re.M)
    txt = re.sub(r'[\t ]?%(\. )?', " procent", txt)
    txt = re.sub(r'ww \.', r" wyżej wymienionych", txt)
    txt = re.sub(r'w/w', r" wyżej wymienionych", txt)
    txt = re.sub(r'[\t ]?xdz \.', " razy dziennie", txt)
    txt = re.sub(r'α', 'alfa', txt)  # greek letters
    txt = re.sub(r'β|ß', 'beta', txt)
    txt = re.sub(r'γ', 'gamma', txt)
    txt = re.sub(r'µ', 'mikro', txt)
    txt = re.sub(r'([ \t]+)', ' ', txt)  # remove whitespace multiplication
    txt = re.sub(r'1/2', r' pół', txt)
    txt = re.sub(r'3/4', r' trzy czwarte', txt)
    txt = re.sub(r'1/4', r' jedna czwarta', txt)
    txt = re.sub(r'(\d)x(\d)', r'\g<1> po \g<2>', txt)
    txt = re.sub(r'(\d)/(\d)', r'\g<1> na \g<2>', txt)
    txt = re.sub(r'[\t ]0[\t ]?,[\t ]?5[\t ]', r' pół ', txt)
    txt = re.sub(r'(\d[\t ]?),[\t ]?5[\t ]', r'\g<1> i pół ', txt)
    txt = re.sub(
        r'(^|[\t ]+)(\d{1,2})[\t ]+(\w{4,}?)[\t ]+([0-9]{4}[\t ]*)',
        convert_full_date,
        txt,
        flags=re.I | re.M,
    )
    txt = re.sub(
        r'w([\t ]\w+)[\t ]([0-9]{4}[\t ]?)(r |r\.|roku)',
        lambda match_obj: f"w{match_obj.group(1)} {change_suffix(num2words(match_obj.group(2), to='ordinal', lang='pl'), suffix='m')} roku ",
        txt,
        flags=re.I,
    )
    txt = re.sub(
        r'(^|[\t ]+)w[\t ]([0-9]{4})([\t .,]?)',
        lambda match_obj: f"{match_obj.group(1)}w {change_suffix(num2words(match_obj.group(2), to='ordinal', lang='pl'), suffix='m')}{match_obj.group(3)}",
        txt,
        flags=re.I | re.M,
    )
    txt = re.sub(
        r'(^|[\t ]+)w[\t ](r |r\.|roku)[\t ]([0-9]{4})([\t .,]?)',
        lambda match_obj: f"{match_obj.group(1)}w roku {change_suffix(num2words(match_obj.group(3), to='ordinal', lang='pl'), suffix='m')}{match_obj.group(4)}",
        txt,
        flags=re.I | re.M,
    )
    txt = re.sub(
        r'przed[\t ]([0-9]{4}[\t ]?)(r |r\.|rokiem)',
        lambda match_obj: f"przed {change_suffix(num2words(match_obj.group(1), to='ordinal', lang='pl'), suffix='m')} rokiem ",
        txt,
        flags=re.I,
    )
    txt = re.sub(
        r'(^|[\t ]+)przed[\t ]([0-9]{4})([\t .]?)',
        lambda match_obj: f"{match_obj.group(1)}przed {change_suffix(num2words(match_obj.group(2), to='ordinal', lang='pl'), suffix='m')}{match_obj.group(3)}",
        txt,
        flags=re.I | re.M,
    )
    txt = re.sub(
        r'(od|do|z)[\t ]([0-9]{4}[\t ]?)(r |r\.|roku)',
        lambda match_obj: f"{match_obj.group(1)} {change_suffix(num2words(match_obj.group(2), to='ordinal', lang='pl'), suffix='ego')} roku ",
        txt,
        flags=re.I,
    )
    txt = re.sub(
        r'(^|[\t ]+)(od|do)([\t ]\w+)?[\t ]([0-9]{4})([\t .]?)',
        lambda match_obj: f"{match_obj.group(1)}{match_obj.group(2)}{match_obj.group(3)} {change_suffix(num2words(match_obj.group(4), to='ordinal', lang='pl'), suffix='ego') if int(match_obj.group(4)) != 0 else match_obj.group(4)}{match_obj.group(5)}",
        txt,
        flags=re.I | re.M,
    )
    txt = re.sub(
        r'(^|[\t ]+)(w połowie|od|na początek|na początku|do|(do [^\d\t ]+)|(w [^\d\t ]+)|(we [^\d\t ]+))([\t ]\w+)?[\t ]([0-9]{4}[\t ]?)(r |r\.|roku)',
        lambda match_obj: f"{match_obj.group(1)}{match_obj.group(5)}{match_obj.group(6)} {change_suffix(num2words(match_obj.group(7), to='ordinal', lang='pl'), suffix='ego')} roku ",
        txt,
        flags=re.I | re.M,
    )
    txt = re.sub(
        r'(^|[\t ]+)(o|po|na|przed|do)[\t ]*(godz\.?|godzinie|godziny|godziną|godzinę)?[\t ]*(\d{1,2})(:\d{2})?(:\d{2})?',
        convert_full_time,
        txt,
        flags=re.I | re.M,
    )
    txt = polish_cleaners(txt)
    return txt


def clean_text_parsed_tts(txt):
    parsed = clean_text_parsed(txt)
    tts = clean_text_tts(parsed)
    return parsed, tts


def add_lines(lines):
    ends = [i for i, (_, p) in enumerate(lines) if p == "PERIOD"]
    starts = [0] + [i + 1 for i in ends[:-1]]
    sentences = list(zip(starts, ends))
    no_of_sentences = len(sentences)
    random.shuffle(sentences)
    train_sentences = sentences[: no_of_sentences * 3 // 5]
    dev_sentences = sentences[no_of_sentences * 3 // 5 : no_of_sentences * 4 // 5]
    test_sentences = sentences[no_of_sentences * 4 // 5 :]
    for start, end in train_sentences:
        for line in lines[start : end + 1]:
            print(*line, file=train, sep="\t")
    for start, end in dev_sentences:
        for line in lines[start : end + 1]:
            print(*line, file=dev, sep="\t")
    for start, end in test_sentences:
        for line in lines[start : end + 1]:
            print(*line, file=test, sep="\t")


# train = open("data/pl/train", 'w')
# dev = open("data/pl/dev", 'w')
# test = open("data/pl/test", 'w')

print("=" * 40, "PARSE MED", "=" * 40)

with open('data/pl/med/pl.txt', 'r') as med, open(
    'data/pl/med/pl_parsed.txt', 'w'
) as med_parsed, open('data/pl/med/pl_tts.txt', 'w') as med_tts:
    parsed, tts = clean_text_parsed_tts(med.read())
    med_parsed.write(parsed)
    med_tts.write(tts)

print("=" * 40, "PARSE WIKI", "=" * 40)

with open('data/pl/wiki/corpus_wikipedia_2020-03-01_all_lines.txt', 'r') as wiki, open(
    'data/pl/wiki/corpus_wikipedia_2020-03-01_all_lines_parsed.txt', 'w'
) as wiki_parsed, open(
    'data/pl/wiki/corpus_wikipedia_2020-03-01_all_lines_tts.txt', 'w'
) as wiki_tts:
    while True:
        chunks = ["".join([next(wiki, "") for _ in range(1000)]) for _ in range(1000)]
        chunks = [ch for ch in chunks if len(ch) != 0]
        if len(chunks) == 0:
            break
        chunks = process_map(clean_text_parsed_tts, chunks)
        for chunk_parsed, chunk_tts in chunks:
            wiki_parsed.write(chunk_parsed)
            wiki_tts.write(chunk_tts)

print("=" * 40, "PARSE OSCAR", "=" * 40)

with open('data/pl/oscar/corpus_oscar_2020-04-10_128M_lines.txt', 'r') as oscar, open(
    'data/pl/oscar/corpus_oscar_2020-04-10_128M_lines_parsed.txt', 'w'
) as oscar_parsed, open(
    'data/pl/oscar/corpus_oscar_2020-04-10_128M_lines_tts.txt', 'w'
) as oscar_tts:
    while True:
        chunks = ["".join([next(oscar, "") for _ in range(1000)]) for _ in range(1000)]
        chunks = [ch for ch in chunks if len(ch) != 0]
        if len(chunks) == 0:
            break
        chunks = process_map(clean_text_parsed_tts, chunks)
        for chunk_parsed, chunk_tts in chunks:
            oscar_parsed.write(chunk_parsed)
            oscar_tts.write(chunk_tts)

# print("=" * 40, "ADD LINES MED", "=" * 40)

# with open('data/pl/med/pl_parsed.txt', 'r') as f:
#     lines = []
#     for sentence in f.read().splitlines():
#         for part in sentence.split():
#             if part in TO_OMMIT:
#                 continue
#             if part in p_dct:
#                 lines[-1][1] = p_dct[part]
#             else:
#                 lines.append([part, "O"])
#     add_lines(lines)

# print("=" * 40, "ADD LINES WIKI", "=" * 40)

# with open('data/pl/wiki/corpus_wikipedia_2020-03-01_all_lines_parsed.txt', 'r') as f:
#     i = 1
#     sentences = []
#     while True:
#         sentence = f.readline()
#         if sentence:
#             sentences.append(sentence)
#             if i % 1000 == 0:
#                 lines = functools.reduce(
#                     lambda a, b: a + b,
#                     process_map(parse, sentences),
#                 )
#                 add_lines(lines)
#                 i = 1
#                 sentences = []
#             else:
#                 i += 1
#         else:
#             break

# print("=" * 40, "ADD LINES OSCAR", "=" * 40)

# with open('data/pl/oscar/corpus_oscar_2020-04-10_128M_lines_parsed.txt', 'r') as f:
#     i = 1
#     sentences = []
#     while True:
#         sentence = f.readline()
#         if sentence:
#             sentences.append(sentence)
#             if i % 1000 == 0:
#                 lines = functools.reduce(
#                     lambda a, b: a + b,
#                     process_map(parse, sentences),
#                 )
#                 add_lines(lines)
#                 i = 1
#                 sentences = []
#             else:
#                 i += 1
#         else:
#             break

# print("=" * 40, "ADD LINES POLEVAL", "=" * 40)

# lines = []
# for fn in glob.glob('data/pl/json/*.json'):
#     with open(fn) as f:
#         try:
#             words = json.load(f)['words']
#         except Exception as e:
#             print(fn)
#             raise e
#         for word in words:
#             if word['word'] in p_dct:
#                 lines[-1][1] = p_dct[word['word']]
#                 continue
#             elif word['word'] == "%":
#                 lines[-1][0] += "%"
#                 if word['punctuation'] == "--":
#                     lines.pop()
#                     lines.pop()
#                 else:
#                     lines[-1][1] = p_dct.get(word['punctuation'], f"<unk> {word}")
#                 continue
#             elif word['word'] == "r":
#                 lines[-1][0] += "r"
#                 lines[-1][1] = p_dct.get(word['punctuation'], f"<unk> {word}")
#                 continue
#             else:
#                 w = word['word'].lower()
#                 if w in TO_OMMIT:
#                     continue
#                 p = p_dct.get(word['punctuation'], "O")
#                 lines.append([w, p])
#                 if word['punctuation'] == ".-.":
#                     lines.append(
#                         [
#                             f"{random_with_N_digits(2)}.{random_with_N_digits(2)}-{random_with_N_digits(2)}.{random_with_N_digits(2)}",
#                             "O",
#                         ]
#                     )
#                 elif word['punctuation'] == ".,":
#                     lines.append(
#                         [
#                             f"{random_with_N_digits(1)},{random_with_N_digits(1)}",
#                             "O",
#                         ]
#                     )
#                 elif word['punctuation'] == ",,":
#                     lines.append(
#                         [
#                             f"{random_with_N_digits(1)},{random_with_N_digits(1)}",
#                             "O",
#                         ]
#                     )
#                 elif word['punctuation'] == "..":
#                     lines.append(
#                         [
#                             f"{random_with_N_digits(2)}.{random_with_N_digits(2)}",
#                             "O",
#                         ]
#                     )
#                 elif word['punctuation'] == ",-":
#                     lines.append(
#                         [
#                             f"{random_with_N_digits(1)},{random_with_N_digits(1)}-{random_with_N_digits(1)}",
#                             "O",
#                         ]
#                     )
#                 elif word['punctuation'] == ",-,":
#                     lines.append(
#                         [
#                             f"{random_with_N_digits(1)},{random_with_N_digits(1)}-{random_with_N_digits(1)},{random_with_N_digits(1)}",
#                             "O",
#                         ]
#                     )
#                 elif word['punctuation'] == "-,":
#                     lines.append(
#                         [
#                             f"{random_with_N_digits(1)}-{random_with_N_digits(1)},{random_with_N_digits(1)}",
#                             "O",
#                         ]
#                     )
#                 elif word['punctuation'] == '-..':
#                     lines.append(
#                         [
#                             f"{random_with_N_digits(2)}-{random_with_N_digits(2)}.{random_with_N_digits(2)}.{random_with_N_digits(4)}",
#                             "O",
#                         ]
#                     )
#                 elif word['punctuation'] == '--':
#                     lines.append(
#                         [
#                             f"{random_with_N_digits(4)}-{random_with_N_digits(2)}-{random_with_N_digits(2)}",
#                             "O",
#                         ]
#                     )
#                 elif word['punctuation'] == ',.':
#                     lines.append(
#                         [
#                             f"{random_with_N_digits(2)},{random_with_N_digits(3)}.{random_with_N_digits(1)}",
#                             "O",
#                         ]
#                     )
#                 elif word['punctuation'] == '----':
#                     lines.append(
#                         [
#                             f"{random_with_N_digits(3)}-{random_with_N_digits(2)}-{random_with_N_digits(4)}-{random_with_N_digits(3)}-{random_with_N_digits(1)}",
#                             "O",
#                         ]
#                     )
#                 elif word['punctuation'] == '---':
#                     lines.append(
#                         [
#                             f"{random_with_N_digits(1)}-{random_with_N_digits(1)}-{random_with_N_digits(1)}",
#                             "O",
#                         ]
#                     )
#                 elif word['punctuation'] == '..,':
#                     lines.append(
#                         [
#                             f"{random_with_N_digits(2)}.{random_with_N_digits(3)}.{random_with_N_digits(3)},{random_with_N_digits(2)}",
#                             "O",
#                         ]
#                     )
#                 elif word['punctuation'] == '.-..':
#                     lines.append(
#                         [
#                             f"{random_with_N_digits(2)}.{random_with_N_digits(2)}-{random_with_N_digits(2)}.{random_with_N_digits(2)}.{random_with_N_digits(4)}",
#                             "O",
#                         ]
#                     )
# add_lines(lines)


# train.close()
# dev.close()
# test.close()

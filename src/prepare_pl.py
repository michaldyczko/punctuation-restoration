import json
import os
from random import randint
import regex as re
import random
import tqdm
from tqdm.contrib.concurrent import process_map


def random_with_N_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    return randint(range_start, range_end)

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

def convert_scientific_notation(match_obj):
    number = re.sub('\s', '', match_obj.group(1)).replace(',', '.')
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

def clean_text(txt):
    txt = "\n".join((l for l in txt.splitlines() if l.endswith('.')))                               # remove lines not ending with .
    txt = re.sub(r'\(([^)]+?)\n([^(]+?)\)', fix_parentheses, txt)                                   # move matched parentheses to one line
    while True:                                                                                     # remove matched parentheses
        txt, n = re.subn(r'\(.*?\)', '', txt)                                                       #
        if n == 0:                                                                                  #
            break                                                                                   #
    txt = re.sub(r'^.*\([^)\n]*$\n', '', txt, flags=re.M)                                           # remove lines without matching parentheses
    txt = re.sub(r'^(.+)([A-Z]+)(.+)$\n', '', txt, flags=re.M)                                      # remove lines with capital letter inside
    txt = re.sub(r'^[^A-ZĄĆĘŁŃÓŚŹŻ]+.*$\n', '', txt, flags=re.M)                                    # remove lines without first capital letter
    txt = re.sub(r'^(.+)http(.+)$\n', '', txt, flags=re.M)                                          # remove lines with http
    txt = re.sub(r'^(.+)(.+)$\n', '', txt, flags=re.M)                                             # remove lines with 
    txt = re.sub(r'^(.*)Reproduction is authorised(.*)$\n', '', txt, flags=re.M)                    # remove lines with "Reproduction is authorised"
    txt = re.sub(r'^[^(\n]*\).*$\n', '', txt, flags=re.M)                                           #
    txt = re.sub(r'[ \t]?(\p{P})[ \t]?', r' \g<1> ', txt)                                           # add whitespace next to punctuation
    txt = re.sub(r'([ \t]+)', ' ', txt)                                                             # remove whitespace multiplication
    txt = re.sub(r'(\D)1\s?[°º]C', r'\g<1> stopnia Celsjusza', txt)                                 # 1° -> stopień 
    txt = re.sub(r'(\D)1\?[°º]F', r'\g<1> stopnia Fahrenheita', txt)                                # 
    txt = re.sub(r'(\D)1\?[°º]', r'\g<1> stopnia', txt)                                             # 
    txt = re.sub(r'([0-9]+)\s?°C', r'\g<1> stopni Celsjusza', txt)                                  # ° -> stopni
    txt = re.sub(r'([0-9]+)\s?°F', r'\g<1> stopni Fahrenheita', txt)                                # 
    txt = re.sub(r'([0-9]+)\s?°', r'\g<1> stopni', txt)                                             # 
    txt = re.sub(r'\s?/\s*m2 ', ' na metr kwadratowy ', txt)                                        # / -> na
    txt = re.sub(r'\s?/\s*l ', ' na litr ', txt)                                                    # 
    txt = re.sub(r'\s?/\s*ml ', ' na mililitr ', txt)                                               # 
    txt = re.sub(r'\s?/\s*h ', ' na godzinę ', txt)                                                 #
    txt = re.sub(r'\s?/\s*min( ?)\.?', r' na minutę\g<1>', txt)                                     #
    txt = re.sub(r'\s?/\s*([0-9]+)\s*min( ?)\.?', r' na \g<1> minut\g<2>', txt)                     #
    txt = re.sub(r'\.? ?•', ',', txt)                                                               # • -> ,
    txt = re.sub(r':\s*,', ':', txt)                                                                # : , -> :
    txt = re.sub(r'·', 'razy', txt)                                                                 # · , -> razy
    txt = re.sub(r'^[\d\s\p{S}\p{P}]+\s+', '', txt, flags=re.M)                                     # remove digits, whitespace, punctuation oand symbols from the beginning of the line
    txt = re.sub(r'([0-9 ]+(, [0-9]+)?)\s?x\s?10([0-9]+)', convert_scientific_notation, txt)        # convert scientific notation to text
    txt = re.sub(r'(mniej|więcej) niż ([0-9]+)', convert_less_more_than, txt)                       # convert "mniej|więcej {liczba}" to "mniej|więcej {liczebnik} dni"
    txt = re.sub(r'^.*w ciągu [0-9]+.*$\n', '', txt, flags=re.M)                                    # remove lines with "w ciągu {liczba}"
    txt = re.sub(r'mmol', "milimol", txt)                                                           # abbreviations
    txt = re.sub(r'([0-9]|\s+)ml\s', r"\g<1> mililitr ", txt)                                       # 
    txt = re.sub(r'([0-9]|\s+)cm\s', r"\g<1> centymetr ", txt)                                      # 
    txt = re.sub(r'([0-9]|\s+)mg\s', r'\g<1> miligramów ', txt)                                     # 
    txt = re.sub(r'([0-9]|\s+)wg\s', r"\g<1> według ", txt)                                         # 
    txt = re.sub(r'([0-9]|\s+)kg\s', r"\g<1> kilogram ", txt)                                       # 
    txt = re.sub(r'([0-9]|\s+)μg\s', r"\g<1> mikrogram ", txt)                                      # 
    txt = re.sub(r'([0-9]|\s+)ng\s', r"\g<1> nanogram ", txt)                                       # 
    txt = re.sub(r'([0-9]|\s+)dl\s', r"\g<1> decylitr ", txt)                                       # 
    txt = re.sub(r'([0-9]|\s+)l\s', r"\g<1> litr ", txt)                                            # 
    txt = re.sub(r'([0-9]|\s+)min\s', r"\g<1> minut ", txt)                                         # 
    txt = re.sub(r'([0-9]|\s+)g\s', r"\g<1> gram ", txt)                                            # 
    txt = re.sub(r'([0-9]{4}\s?)r \. ', r"\g<1> roku ", txt)                                        # 
    txt = re.sub(r'([0-9]|\s+)h\s', r"\g<1> godzin ", txt)                                          # 
    txt = re.sub(r'im \.', r"domięśniowo", txt)                                                     # 
    txt = re.sub(r'i \. m \.', r"domięśniowo", txt)                                                 # 
    txt = re.sub(r'sc \.', r"podskórnie", txt)                                                      # 
    txt = re.sub(r's \. c \.', r"podskórnie", txt)                                                  # 
    txt = re.sub(r'iv \.', r"dożylnie", txt)                                                        # 
    txt = re.sub(r'p \. o \.', r"doustnie", txt)                                                    #  
    txt = re.sub(r'q \. d \.', r"codziennie", txt)                                                  #
    txt = re.sub(r'tj \.', r"to jest", txt)                                                         # 
    txt = re.sub(r't \. j \.', r"to jest", txt)                                                     # 
    txt = re.sub(r'j \. m \.', r" jednostek", txt)                                                  # 
    txt = re.sub(r' j \.?', r" jednostek ", txt)                                                    # 
    txt = re.sub(r'\sx\s', r" razy ", txt)                                                          # 
    txt = re.sub(r'\s?½\s?', r" pół ", txt)                                                         # 
    txt = re.sub(r'\s?²\s?', r" kwadratowych ", txt)                                                # 
    txt = re.sub(r'\s?³\s?', r" sześciennych ", txt)                                                # 
    txt = re.sub(r'\s?±\s?', ' plus minus ', txt, flags=re.M)                                       # 
    txt = re.sub(r'\s?\+\s?', ' plus ', txt, flags=re.M)                                             # 
    txt = re.sub(r'\s?%(\. )?', " procent", txt)                                                    #
    txt = re.sub(r'm \. in \.', r"między innymi", txt)                                              # 
    txt = re.sub(r'm \. c \.?', r"masy ciała", txt)                                                 # 
    txt = re.sub(r'np \.', r"na przykład", txt)                                                     # 
    txt = re.sub(r'nt \.', r"na temat", txt)                                                        # 
    txt = re.sub(r'tzn \.', r"to znaczy", txt)                                                      # 
    txt = re.sub(r'tys \.', r"tysięcy", txt)                                                        # 
    txt = re.sub(r'obj \.', r"objętość", txt)                                                       # 
    txt = re.sub(r'dot \.', r"dotyczących", txt)                                                    # 
    txt = re.sub(r'itp \.', r"i tym podobne", txt)                                                  # 
    txt = re.sub(r'ok \.', r"około", txt)                                                           # 
    txt = re.sub(r' godz \.', r" godzina", txt)                                                     # 
    txt = re.sub(r'ww \.', r" wyżej wymienionych", txt)                                             # 
    txt = re.sub(r'\s?xdz \.', " razy dziennie", txt)                                               # 
    txt = re.sub(r'tzw \.', lambda match_obj: random.choice(['tak zwany', 'tak zwaną', 'tak zwanym']), txt)# 
    txt = re.sub(r'ds \.', 'do spraw', txt)                                                         # 
    txt = re.sub(r'mc \.', r"masy ciała", txt)                                                      # 
    txt = re.sub(r'p \. c \.?', r"powierzchni ciała", txt)                                          # 
    txt = re.sub(r'pow \. ciała', r"powierzchni ciała", txt)                                        # 
    txt = re.sub(r'pc \.?', r"powierzchni ciała", txt)                                              # 
    txt = re.sub(r'p \. m - r \.', r"płyn mózgowo-rdzeniowy", txt)                                  # 
    txt = re.sub(r'e - mail', r"imejl", txt)                                                        # 
    txt = re.sub(r'rodków', r"środków", txt)                                                        # missing letters
    txt = re.sub(r'mo e', r"może", txt)                                                             # 
    txt = re.sub(r'dotycz ce', r"dotyczące", txt)                                                   # 
    txt = re.sub(r'(N|n)ale y', r"g<1>ależy", txt)                                                  # 
    txt = re.sub(r'(J|j)e li', r"g<1>eśli", txt)                                                    # 
    txt = re.sub(r'(T|t)ak e', r"g<1>akże", txt)                                                    # 
    txt = re.sub(r' si ', r" się ", txt)                                                            # 
    txt = re.sub(r', e', r", że", txt)                                                              # 
    while True:                                                                                     #
        txt, n = re.subn(r' [ąćęńóśźż] ', '', txt)                                                  #
        if n == 0:                                                                                  #
            break                                                                                   #
    txt = re.sub(r'α', 'alfa', txt)                                                                 # greek letters
    txt = re.sub(r'β|ß', 'beta', txt)                                                               # 
    txt = re.sub(r'γ', 'gamma', txt)                                                                # 
    txt = re.sub(r'µ', 'mikro', txt)                                                                # 
    txt = re.sub(r'^[^a-zA-Z]+$\n', '', txt, flags=re.M)                                            # remove lines without letters
    txt = re.sub(r'^.*\p{S}.*$\n', '', txt, flags=re.M)                                             # remove lines with special symbols
    txt = re.sub(r'^.*(d \. o \. o \.).*$\n', '', txt, flags=re.M)                                  # remove lines with d . o . o .
    txt = re.sub(r'^.*(s \. r \. o \.).*$\n', '', txt, flags=re.M)                                  # remove lines with s . r . o .
    txt = re.sub(r'^.*(Kύπρος).*$\n', '', txt, flags=re.M)                                          # remove lines with Kύπρος
    txt = re.sub(r'^.*((\. ){4}).*$\n', '', txt, flags=re.M)                                        # remove lines with too many dots
    txt = re.sub(r'([ \t]+)', ' ', txt)                                                             # reformatting
    txt = re.sub(r'([0-9,]+?)\s+(-|–)\s+([0-9,]+?)', r'\g<1>-\g<3>', txt)                           #
    txt = re.sub(r'( ? - ?)?([0-9]+)( ? - ?)([^\d\p{P}])', r'\g<1>\g<2>-\g<4>', txt)                #
    while True:                                                                                     # 
        txt, n = re.subn(r'([^ \d,]+) (\d+) , (\d+) ((?!i|lub)[^ \d,/]+)', r'\g<1> \g<2>,\g<3> \g<4>', txt)#
        if n == 0:                                                                                  #
            break                                                                                   #
    txt = re.sub(r'([0-9]+)([\. ]+)([0-9]+)-([0-9]+)([\. ]+)([0-9]+)', fix_ranges, txt)             #
    txt = re.sub(r'(\D) (([0-9]+ ?)+) (\D)', fix_numbers, txt)                                      #        
    txt = re.sub(r'(\D)\s-\s(\D)', r'\g<1>-\g<2>', txt, flags=re.M)                                 #
    while True:                                                                                     #
        txt, n = re.subn(r'(\d) \. ((\d ?)\.?)', r'\g<1> kropka \g<3>', txt)                        #
        if n == 0:                                                                                  #
            break                                                                                   #
    txt = re.sub(r'(\d) \. ([^\d\n])', lambda match_obj: f"{match_obj.group(1)}-{random.choice(['ą', 'ego', 'ym'])} {match_obj.group(2)}", txt)# 
    txt = re.sub(r'(\. )+', '. ', txt)                                                              #
    txt = re.sub(r'\. ,', ',', txt)                                                                 #
    txt = re.sub(r', \.', ',', txt)                                                                 #
    txt = re.sub(r'(\D) \. ([^$])', r'\g<1> . \n\g<2>', txt, flags=re.M)                            # split lines in dots      
    txt = re.sub(r'([ \t]+)', ' ', txt)                                                             # remove whitespace multiplication
    txt = re.sub(r'(\s?)([^.\s])\s*$', r'\g<1>\g<2> . ', txt, flags=re.M)                           # add periods
    txt = "\n".join((l for l in txt.splitlines() if len(l.split()) >= 10))                          # keep lines with at least 5 words
    txt = re.sub(r'^.*(--).*$\n', '', txt, flags=re.M)                                              # remove lines with --
    txt = txt.lower()                                                                               # lower
    return txt

lines = []

with open('data/pl/med/pl.txt', 'r') as med:
    txt = clean_text(med.read())
    with open('data/pl/med/pl_parsed.txt', 'w') as f:
        f.write(txt)
    for sentence in txt.splitlines():
        for part in sentence.split():
            if part in TO_OMMIT:
                continue
            if part in p_dct:
                lines[-1][1] = p_dct[part]
            else:
                lines.append([part, "O"])

with open('data/pl/wiki/corpus_wikipedia_2020-03-01_all_lines.txt', 'r') as wiki:
    with open('data/pl/wiki/corpus_wikipedia_2020-03-01_all_lines_parsed.txt', 'w') as f:
        while True:
            chunks = ["".join([next(wiki, "") for _ in range(1000)]) for _ in range(1000)]
            chunks = [ch for ch in chunks if len(ch) != 99]
            if len(chunks) == 0:
                break
            chunks = process_map(clean_text, chunks)
            for chunk in chunks:
                f.write(chunk)
    with open('data/pl/wiki/corpus_wikipedia_2020-03-01_all_lines_parsed.txt', 'r') as f:
        i = 0
        while True:
            sentence = f.readline()
            if sentence and i < 5_000_000:
                for part in sentence.split():
                    if part in TO_OMMIT:
                        continue
                    if part in p_dct:
                        lines[-1][1] = p_dct[part]
                    else:
                        lines.append([part, "O"])
                i += 1
            else:
                break



for (root, dirs, files) in os.walk('data/pl/json'):
    for fn in files:
        if "talks" in fn:
            continue
        with open(f'data/pl/json/{fn}') as f:
            words = json.load(f)['words']
            for word in words:
                if word['word'] in p_dct:
                    lines[-1][1] = p_dct[word['word']]
                    continue
                elif word['word'] == "%":
                    lines[-1][0] += "%"
                    if word['punctuation'] == "--":
                        lines.pop()
                        lines.pop()
                    else:
                        lines[-1][1] = p_dct.get(word['punctuation'], f"<unk> {word}")
                    continue
                elif word['word'] == "r":
                    lines[-1][0] += "r"
                    lines[-1][1] = p_dct.get(word['punctuation'], f"<unk> {word}")
                    continue
                else:
                    w = word['word'].lower()
                    if w in TO_OMMIT:
                        continue
                    p = p_dct.get(word['punctuation'], "O")
                    lines.append([w, p])
                    if word['punctuation'] == ".-.":
                        lines.append(
                            [
                                f"{random_with_N_digits(2)}.{random_with_N_digits(2)}-{random_with_N_digits(2)}.{random_with_N_digits(2)}",
                                "O",
                            ]
                        )
                    elif word['punctuation'] == ".,":
                        lines.append(
                            [f"{random_with_N_digits(1)},{random_with_N_digits(1)}", "O"]
                        )
                    elif word['punctuation'] == ",,":
                        lines.append(
                            [f"{random_with_N_digits(1)},{random_with_N_digits(1)}", "O"]
                        )
                    elif word['punctuation'] == "..":
                        lines.append(
                            [f"{random_with_N_digits(2)}.{random_with_N_digits(2)}", "O"]
                        )
                    elif word['punctuation'] == ",-":
                        lines.append(
                            [
                                f"{random_with_N_digits(1)},{random_with_N_digits(1)}-{random_with_N_digits(1)}",
                                "O",
                            ]
                        )
                    elif word['punctuation'] == ",-,":
                        lines.append(
                            [
                                f"{random_with_N_digits(1)},{random_with_N_digits(1)}-{random_with_N_digits(1)},{random_with_N_digits(1)}",
                                "O",
                            ]
                        )
                    elif word['punctuation'] == "-,":
                        lines.append(
                            [
                                f"{random_with_N_digits(1)}-{random_with_N_digits(1)},{random_with_N_digits(1)}",
                                "O",
                            ]
                        )
                    elif word['punctuation'] == '-..':
                        lines.append(
                            [
                                f"{random_with_N_digits(2)}-{random_with_N_digits(2)}.{random_with_N_digits(2)}.{random_with_N_digits(4)}",
                                "O",
                            ]
                        )
                    elif word['punctuation'] == '--':
                        lines.append(
                            [
                                f"{random_with_N_digits(4)}-{random_with_N_digits(2)}-{random_with_N_digits(2)}",
                                "O",
                            ]
                        )
                    elif word['punctuation'] == ',.':
                        lines.append(
                            [
                                f"{random_with_N_digits(2)},{random_with_N_digits(3)}.{random_with_N_digits(1)}",
                                "O",
                            ]
                        )
                    elif word['punctuation'] == '----':
                        lines.append(
                            [
                                f"{random_with_N_digits(3)}-{random_with_N_digits(2)}-{random_with_N_digits(4)}-{random_with_N_digits(3)}-{random_with_N_digits(1)}",
                                "O",
                            ]
                        )
                    elif word['punctuation'] == '---':
                        lines.append(
                            [
                                f"{random_with_N_digits(1)}-{random_with_N_digits(1)}-{random_with_N_digits(1)}",
                                "O",
                            ]
                        )
                    elif word['punctuation'] == '..,':
                        lines.append(
                            [
                                f"{random_with_N_digits(2)}.{random_with_N_digits(3)}.{random_with_N_digits(3)},{random_with_N_digits(2)}",
                                "O",
                            ]
                        )
                    elif word['punctuation'] == '.-..':
                        lines.append(
                            [
                                f"{random_with_N_digits(2)}.{random_with_N_digits(2)}-{random_with_N_digits(2)}.{random_with_N_digits(2)}.{random_with_N_digits(4)}",
                                "O",
                            ]
                        )

ends = [i for i, (_, p) in enumerate(lines) if p == "PERIOD"]
starts = [0] + [i+1 for i in ends[:-1]]
sentences = list(zip(starts, ends))
no_of_sentences = len(sentences)
random.shuffle(sentences)
train_sentences = sentences[:no_of_sentences * 3 // 5]
dev_sentences = sentences[no_of_sentences * 3 // 5: no_of_sentences * 4 // 5]
test_sentences = sentences[no_of_sentences * 4 // 5:]

with open("data/pl/train", 'w') as train:
    for start, end in train_sentences:
        for line in lines[start:end+1]:
            print(*line, file=train, sep="\t")
with open("data/pl/dev", 'w') as dev:
    for start, end in dev_sentences:
        for line in lines[start:end+1]:
            print(*line, file=dev, sep="\t")
with open("data/pl/test", 'w') as test:
    for start, end in test_sentences:
        for line in lines[start:end+1]:
            print(*line, file=test, sep="\t")
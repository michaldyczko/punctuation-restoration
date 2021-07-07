import json
import os
from random import randint


def random_with_N_digits(n):
    range_start = 10 ** (n - 1)
    range_end = (10 ** n) - 1
    return randint(range_start, range_end)


p_dct = {
    "": "O",
    ",": "COMMA",
    "-": "HYPHEN",
    ":": "COLON",
    ".": "PERIOD",
    "!": "EXCL",
    ";": "SEMICOLON",
    "?": "QUESTION",
    "...": "O",
    ".-": "HYPHEN",
    '.-.': "O",
    '.,': "O",
    ',,': "O",
    '..': "O",
    ',-': "O",
    ',-,': "O",
    '-,': "O",
    '-..': "O",
    '--': "O",
    ',.': "O",
    '----': "O",
    '---': "O",
    '..,': "O",
    '.-..': "O",
}

for (root, dirs, files) in os.walk('data/pl/json'):
    lines = []
    for fn in files:
        with open(f'data/pl/json/{fn}') as f:
            words = json.load(f)['words']
            for word in words:
                if word['word'] == ".":
                    lines[-1][1] = "PERIOD"
                    continue
                if word['word'] == ",":
                    lines[-1][1] = "COMMA"
                    continue
                if word['word'] == "%":
                    lines[-1][0] += "%"
                    lines[-1][1] = p_dct.get(word['punctuation'], f"<unk> {word}")
                    continue
                if word['word'] == "r":
                    lines[-1][0] += "r"
                    lines[-1][1] = p_dct.get(word['punctuation'], f"<unk> {word}")
                    continue
                else:
                    w = word['word'].lower()
                    if w in ['"']:
                        continue
                    p = p_dct.get(word['punctuation'], f"<unk> {word}")
                lines.append([w, p])
                if word['punctuation'] == ".-.":
                    lines.append(
                        [
                            f"{random_with_N_digits(2)}.{random_with_N_digits(2)}-{random_with_N_digits(2)}.{random_with_N_digits(2)}",
                            "O",
                        ]
                    )
                if word['punctuation'] == ".,":
                    lines.append(
                        [f"{random_with_N_digits(1)},{random_with_N_digits(1)}", "O"]
                    )
                if word['punctuation'] == ",,":
                    lines.append(
                        [f"{random_with_N_digits(1)},{random_with_N_digits(1)}", "O"]
                    )
                if word['punctuation'] == "..":
                    lines.append(
                        [f"{random_with_N_digits(2)}.{random_with_N_digits(2)}", "O"]
                    )
                if word['punctuation'] == ",-":
                    lines.append(
                        [
                            f"{random_with_N_digits(1)},{random_with_N_digits(1)}-{random_with_N_digits(1)}",
                            "O",
                        ]
                    )
                if word['punctuation'] == ",-,":
                    lines.append(
                        [
                            f"{random_with_N_digits(1)},{random_with_N_digits(1)}-{random_with_N_digits(1)},{random_with_N_digits(1)}",
                            "O",
                        ]
                    )
                if word['punctuation'] == "-,":
                    lines.append(
                        [
                            f"{random_with_N_digits(1)}-{random_with_N_digits(1)},{random_with_N_digits(1)}",
                            "O",
                        ]
                    )
                if word['punctuation'] == '-..':
                    lines.append(
                        [
                            f"{random_with_N_digits(2)}-{random_with_N_digits(2)}.{random_with_N_digits(2)}.{random_with_N_digits(4)}",
                            "O",
                        ]
                    )
                if word['punctuation'] == '--':
                    lines.append(
                        [
                            f"{random_with_N_digits(4)}-{random_with_N_digits(2)}-{random_with_N_digits(2)}",
                            "O",
                        ]
                    )
                if word['punctuation'] == ',.':
                    lines.append(
                        [
                            f"{random_with_N_digits(2)},{random_with_N_digits(3)}.{random_with_N_digits(1)}",
                            "O",
                        ]
                    )
                if word['punctuation'] == '----':
                    lines.append(
                        [
                            f"{random_with_N_digits(3)}-{random_with_N_digits(2)}-{random_with_N_digits(4)}-{random_with_N_digits(3)}-{random_with_N_digits(1)}",
                            "O",
                        ]
                    )
                if word['punctuation'] == '---':
                    lines.append(
                        [
                            f"{random_with_N_digits(1)}-{random_with_N_digits(1)}-{random_with_N_digits(1)}",
                            "O",
                        ]
                    )
                if word['punctuation'] == '..,':
                    lines.append(
                        [
                            f"{random_with_N_digits(2)}.{random_with_N_digits(3)}.{random_with_N_digits(3)},{random_with_N_digits(2)}",
                            "O",
                        ]
                    )
                if word['punctuation'] == '.-..':
                    lines.append(
                        [
                            f"{random_with_N_digits(2)}.{random_with_N_digits(2)}-{random_with_N_digits(2)}.{random_with_N_digits(2)}.{random_with_N_digits(4)}",
                            "O",
                        ]
                    )
    no_of_lines = len(lines)
    with open("data/pl/train", 'w') as train:
        for line in lines[: no_of_lines * 3 // 5]:
            print(*line, file=train, sep="\t")
    with open("data/pl/dev", 'w') as dev:
        for line in lines[no_of_lines * 3 // 5 : no_of_lines * 4 // 5]:
            print(*line, file=dev, sep="\t")
    with open("data/pl/test", 'w') as test:
        for line in lines[no_of_lines * 4 // 5 :]:
            print(*line, file=test, sep="\t")

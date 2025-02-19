import glob
import random

import pandas as pd

p_dct = {
    ".": "FULLSTOP",
    ",": "COMMA",
    "?": "QUESTION_MARK",
    "!": "EXCLAMATION_MARK",
    "-": "HYPHEN",
    ":": "COLON",
    "...": "ELLIPSIS",
    # ";": "SEMICOLON",
    # '"': "QUOTATION_MARK",
    "": "BLANK",
}

train = open('../data/poleval/train', 'w')
dev = open('../data/poleval/dev', 'w')
test = open('../data/poleval/test', 'w')

lines = []
for filename in glob.glob('../data/poleval/wikitalks/**/*.csv', recursive=True):
    number = random.random()
    output = train if number < 0.8 else (dev if number < 0.9 else test)
    with open(filename, 'r') as f:
        f.readline()
        line = f.readline()
        while line:
            first_semicolon_idx = line.index(';')
            last_semicolon_idx = len(line) - line[::-1].index(';') - 1
            word = line[:first_semicolon_idx]
            punctuation = line[first_semicolon_idx + 1 : last_semicolon_idx]
            space_after = line[last_semicolon_idx + 1 :]
            if word in p_dct:
                if word == '!':
                    while True:
                        line = f.readline()
                        if not line:
                            break
                        first_semicolon_idx = line.index(';')
                        last_semicolon_idx = len(line) - line[::-1].index(';') - 1
                        word = line[:first_semicolon_idx]
                        punctuation = line[first_semicolon_idx + 1 : last_semicolon_idx]
                        space_after = line[last_semicolon_idx + 1 :]
                        if '!' not in [word, punctuation]:
                            break
                else:
                    lines[-1][-2] = p_dct[word]
            else:
                lines.append([word, p_dct.get(punctuation, 'BLANK'), output])
            line = f.readline()
for word, punc, output in lines:
    print(
        word,
        punc,
        sep="\t",
        file=output,
    )
train.close()
dev.close()
test.close()

test_in = pd.read_csv('../data/poleval/test_A.tsv', sep="\t", index_col=0, header=None)
with open('../data/test_poleval_A.tsv', 'w') as f:
    for txt in test_in.iloc[:, 0]:
        print(txt, file=f)
test_in = pd.read_csv('../data/poleval/test_B.tsv', sep="\t", index_col=0, header=None)
with open('../data/test_poleval_B.tsv', 'w') as f:
    for txt in test_in.iloc[:, 0]:
        print(txt, file=f)
test_in = pd.read_csv('../data/poleval/test_C.tsv', sep="\t", index_col=0, header=None)
with open('../data/test_poleval_C.tsv', 'w') as f:
    for txt in test_in.iloc[:, 0]:
        print(txt, file=f)

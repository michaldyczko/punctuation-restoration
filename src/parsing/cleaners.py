""" from https://github.com/keithito/tacotron """

'''
Cleaners are transformations that run over the input text at both training and eval time.

Cleaners can be selected by passing a comma-delimited list of cleaner names as the "cleaners"
hyperparameter. Some cleaners are English-specific. You'll typically want to use:
  1. "english_cleaners" for English text
  2. "transliteration_cleaners" for non-English text that can be transliterated to ASCII using
     the Unidecode library (https://pypi.python.org/pypi/Unidecode)
  3. "basic_cleaners" if you do not want to transliterate (in this case, you should also update
     the symbols in symbols.py to match your data).
'''

import re
from unidecode import unidecode
from .numbers import normalize_numbers, normalize_numbers_pl
from .polish_abbrs import _acronyms_pl


# Regular expression matching whitespace:
_whitespace_re = re.compile(r'\s+')

# List of (regular expression, replacement) pairs for abbreviations:
_abbreviations = [(re.compile('\\b%s\\.' % x[0], re.IGNORECASE), x[1]) for x in [
  ('mrs', 'misess'),
  ('mr', 'mister'),
  ('dr', 'doctor'),
  ('st', 'saint'),
  ('co', 'company'),
  ('jr', 'junior'),
  ('maj', 'major'),
  ('gen', 'general'),
  ('drs', 'doctors'),
  ('rev', 'reverend'),
  ('lt', 'lieutenant'),
  ('hon', 'honorable'),
  ('sgt', 'sergeant'),
  ('capt', 'captain'),
  ('esq', 'esquire'),
  ('ltd', 'limited'),
  ('col', 'colonel'),
  ('ft', 'fort'),
]]

_abbreviations_pl = [(re.compile(rf'\s{x}[\.,]?\s|\s{x}[\.,]?$', re.IGNORECASE), rf' {y} ') for x, y in [
  (r'sz', 'szanowny'),
  (r'dr', 'doktor'),
  (r'gen', 'generał'),
  (r'ks', 'ksiądz'),
  (r'km', 'kilometr'),
  (r'h', 'godzina'),
  (r's', 'sekunda'),
  (r'kg', 'kilogram'),
  (r'm', 'metr'),
  (r'hab', 'habilitowany'),
  (r'r', 'roku'),
  (r'np', 'na przykład:'),
  (r'bł', 'błogosławiony'),
  (r'św', 'święty'),
  (r'szt', 'sztuki'),
  (r'kpt', 'kapitan'),
  (r'kpr', 'kapral'),
  (r'ppłk', 'podpułkownik'),
  (r'mjr', 'major'),
  (r'płk', 'pułkownik'),
  (r'mm', 'milimetr'),
  (r'lek', 'lekarz'),
  (r'med', 'medycyny'),
  (r'abp', 'arcybiskup'),
  (r'prof', 'profesor'),
  (r'zwycz', 'zwyczajny'),
]]


def expand_abbreviations(text):
  for regex, replacement in _abbreviations:
    text = re.sub(regex, replacement, text)
  return text

def expand_abbreviations_pl(text):
  for regex, replacement in _abbreviations_pl:
    text = re.sub(regex, replacement, text)
  return text

def expand_acronyms_pl(text):
  for regex, replacement in _acronyms_pl:
    text = re.sub(regex, replacement, text)
  return text

def expand_numbers(text):
  return normalize_numbers(text)

def expand_numbers_pl(text):
  return normalize_numbers_pl(text)


def lowercase(text):
  return text.lower()


def collapse_whitespace(text):
  return re.sub(_whitespace_re, ' ', text)

def trim_whitespace(text):
  return text.strip()


def convert_to_ascii(text):
  return unidecode(text)


def basic_cleaners(text):
  '''Basic pipeline that lowercases and collapses whitespace without transliteration.'''
  text = lowercase(text)
  text = collapse_whitespace(text)
  text = expand_numbers_pl(text)
  return text

def polish_cleaners(text):
  '''Pipeline for Polish utterances.'''
  text = expand_abbreviations_pl(text)
  text = expand_acronyms_pl(text)
  text = expand_numbers_pl(text)
  text = lowercase(text)
  text = collapse_whitespace(text)
  text = trim_whitespace(text)
  return text


def transliteration_cleaners(text):
  '''Pipeline for non-English text that transliterates to ASCII.'''
  text = convert_to_ascii(text)
  text = lowercase(text)
  text = collapse_whitespace(text)
  return text


def english_cleaners(text):
  '''Pipeline for English text, including number and abbreviation expansion.'''
  text = convert_to_ascii(text)
  text = lowercase(text)
  text = expand_numbers(text)
  text = expand_abbreviations(text)
  text = collapse_whitespace(text)
  return text

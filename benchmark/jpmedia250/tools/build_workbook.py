#!/usr/bin/env python3
"""Create a filterable editorial review workbook using artifact_tool."""
from __future__ import annotations
import json
from pathlib import Path
from artifact_tool import Workbook, SpreadsheetFile
from build import ROOT, SECTIONS

rows = [json.loads(s) for s in (ROOT/'data/build/jpmedia250_gold.jsonl').read_text(encoding='utf-8').splitlines()]
wb = Workbook.create()
corpus = wb.worksheets.add('Corpus')
coverage = wb.worksheets.add('Coverage')
readme = wb.worksheets.add('START HERE')
rubric = wb.worksheets.add('Review rubric')

HEADER = {'fill':'#17324D', 'font': {'bold':True,'color':'#FFFFFF'},
          'row_height':30,'vertical_alignment':'center'}
HEAD2 = {'fill':'#DCE8F2', 'font':{'bold':True,'color':'#17324D'},'row_height':26}

headers = ['ID','Split','Medium style','Genre','Difficulty','Primary challenge',
           'Japanese original','English reference','Context for judge','Translation trap / note',
           'Tags','Acceptable alternate references','Provenance / status']
data = []
for r in rows:
    data.append([r['id'],r['split'],r['medium'],r['genre'],r['difficulty'],
                 r['primary_challenge'],r['japanese'],r['english_reference'],
                 r['scene_context'],r['translation_note'],', '.join(r['tags']),
                 ' | '.join(r['alternate_references']), 'original; native reviewer pending'])
corpus.get_range('A1:M251').values = [headers] + data
corpus.get_range('A1:M1').format = HEADER
corpus.get_range('A2:M251').format.row_height = 38
corpus.get_range('A2:M251').format.wrap_text = True
for col,width in {
    'A':14,'B':10,'C':16,'D':16,'E':11,'F':27,'G':44,'H':42,'I':40,
    'J':45,'K':26,'L':35,'M':29}.items():
    corpus.get_range(f'{col}:{col}').format.column_width = width
corpus.get_range('E2:E251').conditional_formats.add_data_bar({'color':'#447B94', 'gradient':True})
corpus.freeze_panes.freeze_rows(1)
corpus.tables.add('A1:M251', True, 'JP250Corpus')

coverage.get_range('A1:G1').values = [['Challenge','Total','D1','D2','D3','D4','D5']]
coverage.get_range('A1:G1').format = HEADER
for idx,(_,category) in enumerate(SECTIONS,2):
    coverage.get_range(f'A{idx}').values = [[category]]
    coverage.get_range(f'B{idx}').formulas = [[f'=COUNTIF(Corpus!$F$2:$F$251,A{idx})']]
    for diff in range(1,6):
        letter = chr(ord('B') + diff)
        coverage.get_range(f'{letter}{idx}').formulas = [[
            f'=COUNTIFS(Corpus!$F$2:$F$251,$A{idx},Corpus!$E$2:$E$251,{diff})']]
coverage.get_range('A12:G12').values = [['TOTAL',None,None,None,None,None,None]]
for idx,c in enumerate('BCDEFG',1):
    coverage.get_range(f'{c}12').formulas = [[f'=SUM({c}2:{c}11)']]
coverage.get_range('A12:G12').format = HEAD2
coverage.get_range('A15:B15').values = [['Medium style','Count']]
coverage.get_range('A15:B15').format = HEADER
for ix,medium in enumerate(['visual_novel','light_novel','game','anime'],16):
    coverage.get_range(f'A{ix}').values = [[medium]]
    coverage.get_range(f'B{ix}').formulas = [[f'=COUNTIF(Corpus!$C$2:$C$251,A{ix})']]
coverage.get_range('A22:B22').values = [['Split','Count']]
coverage.get_range('A22:B22').format = HEADER
for ix,split in enumerate(['dev','eval'],23):
    coverage.get_range(f'A{ix}').values = [[split]]
    coverage.get_range(f'B{ix}').formulas = [[f'=COUNTIF(Corpus!$B$2:$B$251,A{ix})']]
coverage.get_range('A:A').format.column_width = 33
coverage.get_range('B:G').format.column_width = 12
coverage.get_range('A2:G24').format.row_height = 25
coverage.freeze_panes.freeze_rows(1)

read_lines = [
    ['JP-Media-250','A 250-item draft Japanese-to-English LLM translation benchmark'],
    ['Corpus source','Original Japanese sentences independently authored here. No quoted/anime/game source attributions.'],
    ['Medium style','A counterbalanced scenario/style label only (63 VN, 63 LN, 62 Game, 62 Anime); NOT published provenance.'],
    ['Difficulty','Heuristic 1–5, balanced at 50 each, progressively challenging WITHIN each phenomenon; not JLPT verified.'],
    ['Context','Context can resolve genuine Japanese ambiguity. Compare bare vs contextual evaluation.'],
    ['Reference','One main English translation and optional alternatives; creative yet faithful paraphrases can also be acceptable.'],
    ['Split','50 dev calibration items; 200 evaluation items; exact 1/4 per category × difficulty stratum.'],
    ['Blind files','Use the two blind JSONL files for inference; they exclude English references and annotation notes.'],
    ['Human scoring','Use Review rubric. Automated character overlap is only a weak diagnostic.'],
    ['Validation','250 unique Japanese entries; ten primary categories ×25, 50 per difficulty; source tests pass.'],
    ['Quality status','Editorial draft, NOT independently native-speaker reviewed or psychometrically calibrated.'],
    ['Rights / leakage','Original composition avoids fabricated source attribution; public examples may still be memorized after publication.'],
]
readme.get_range('A1:B12').values = read_lines
readme.get_range('A1:B1').format = HEADER
readme.get_range('A2:A12').format = HEAD2
readme.get_range('A:A').format.column_width = 24
readme.get_range('B:B').format.column_width = 95
readme.get_range('A1:B12').format.row_height = 38
readme.get_range('A1:B12').format.wrap_text = True

rubric_lines = [
    ['Metric','Points','Operational criteria'],
    ['Adequacy', '0–4', '4: correct propositions, polarity, modality, agents, aspect and referents; 2: partially correct; 0: contrary/major hallucination.'],
    ['Pragmatics & voice', '0–4', '4: preserve intent, politeness, characterization, irony, ellipsis and subtext given context; 2: partial; 0: opposite speech act.'],
    ['English fluency', '0–2', '2: natural and appropriate; 1: awkward but understandable; 0: severely unnatural.'],
    ['Critical error flags', 'not weighted', 'NEG negation; AGENT actor; MOD modality; IDIOM literalized idiom; REG politeness; IMPL implied intent; CULT culture; HALL hallucination.'],
    ['Total', '0–10', 'Sum 3 dimensions. Preserve alternative valid renderings. Do not require word-for-word matches to the references.'],
    ['Review protocol', 'manual', 'Blind reviewer sees Japanese and scene context with model answer, then independently assesses; review gold afterward if uncertain.'],
    ['Automatic metric', 'diagnostic', 'tools/score.py reports simple char ngram F2, NOT an authoritative accuracy/nuance metric.'],
]
rubric.get_range('A1:C8').values = rubric_lines
rubric.get_range('A1:C1').format = HEADER
rubric.get_range('A:A').format.column_width = 25
rubric.get_range('B:B').format.column_width = 17
rubric.get_range('C:C').format.column_width = 96
rubric.get_range('A1:C8').format.wrap_text = True
rubric.get_range('A1:C8').format.row_height = 52

# Workbook backend inspection verifies actual cell content and summary formulas.
print(wb.inspect({'kind':'table','range':'Corpus!A1:H3', 'include':'values,formulas',
                  'table_max_rows':3,'table_max_cols':8}).ndjson[:2500])
print(wb.inspect({'kind':'table','range':'Coverage!A1:C3', 'include':'values,formulas',
                  'table_max_rows':3,'table_max_cols':3}).ndjson[:1800])
SpreadsheetFile.export_xlsx(wb).save(str(ROOT/'data/build/jpmedia250_review.xlsx'))
print('Saved', ROOT/'data/build/jpmedia250_review.xlsx')

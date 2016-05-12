import sys
sys.path.append("/Users/Ryan/src/Thesis/NLTK")
import generate_local
from nltk import *

grammarString = """
S -> R | TH | F
R -> RT1 THT1 | RT2 FT2
TH -> THT1 FT1 | THT2 RT2
F -> FT1 RT1 | FT2 THT2
RT1 -> 'm3' 
RT2 -> 'P5'
THT1 -> 'M3' 
THT2 -> 'M6'
FT1 -> 'P4'
FT2 -> 'm6'
m3 -> 'm2' 'M2' | 'M2' 'm2' | 'P4' 
"""
gramStringRecur="""
S -> R | TH | F
R -> 'm3' THT | 'm3' TH | 'P5' F | 'P5' FT
TH -> 'M3' FT  |'M3' F | 'M6' R | 'M6' RT
F -> 'P4' RT |'P4' R | 'm6' TH |  'm6' THT
RT -> 'm3' | 'P5'
THT -> 'M3' | 'M6'
FT -> 'P4' | 'm6'
"""

gramStringRecurFixed="""
S -> R | TH | F
R -> 'm3' 'M3' | 'm3' TH | 'P5' F | 'P5' 'm6'
TH -> 'M3' 'P4'  |'M3' F | 'M6' R | 'M6' 'P5'
F -> 'P4' RT |'P4' R | 'm6' TH |  'm6' THT
RT -> 'm3' | 'P5'
THT -> 'M3' | 'M6'
FT -> 'P4' | 'm6'
"""

gramStringRecurFixed2="""
S ->  ROOT
ROOT -> 'm3' ROOT_THIRD | 'P5' ROOT_FIFTH
THIRD -> 'M3' THIRD_FIFTH | 'M6' THIRD_ROOT
FIFTH -> 'P4' FIFTH_ROOT | 'm6' FIFTH_THIRD
ROOT_THIRD -> 'M3' | 'M3' FIFTHX | 'M6' THIRD_ROOT
ROOT_FIFTH -> 'm6' | 'm6' THIRDX | 'P4' FIFTH_ROOT
THIRD_FIFTH ->  'P4' | 'P4' ROOTX | 'm6' FIFTH_THIRD
THIRD_ROOT -> 'P5' | 'P5' FIFTHX | 'm3' ROOT_THIRD
FIFTH_ROOT -> 'm3' | 'm3' THIRDX | 'P5' ROOT_FIFTH
FIFTH_THIRD -> 'M6' | 'M6' ROOTX | 'M3' THIRD_FIFTH
ROOTX -> 'm3' | 'P5' | 'm3' THIRDX | 'P5' FIFTHX
THIRDX -> 'M3' | 'M6' | 'M3' FIFTHX | 'M6' ROOTX
FIFTHX -> 'P4' | 'm6' | 'P4' ROOTX | 'm6' THIRDX
"""


gramHarmonyMinorBothDirections="""
S -> ROOT | THIRD | FIFTH
ROOT -> 3 ROOT_THIRD | m6 ROOT_THIRD | 7 ROOT_FIFTH | m5 ROOT_FIFTH
THIRD -> 4 THIRD_FIFTH | m8 THIRD_FIFTH | 9 THIRD_ROOT | m3 THIRD_ROOT
FIFTH -> 5 FIFTH_ROOT | m7 FIFTH_ROOT | 8 FIFTH_THIRD | m4 FIFTH_THIRD
ROOT_THIRD -> 4 | m8 | 4 FIFTHX | m8 FIFTHX | 9 THIRD_ROOT | m3 THIRD_ROOT
ROOT_FIFTH -> 8 | m4 | 8 THIRDX | m4 THIRDX | 5 FIFTH_ROOT | m7 FIFTH_ROOT
THIRD_FIFTH -> 5 | m7 | 5 ROOTX | m7 ROOTX | 8 FIFTH_THIRD | m4 FIFTH_THIRD
THIRD_ROOT -> 7 | m5 | 7 FIFTHX | m5 FIFTHX | 3 ROOT_THIRD | m9 ROOT_THIRD
FIFTH_ROOT -> 3 | m9 | 3 THIRDX | m9 THIRD X | 7 ROOT_FIFTH | m5 ROOT_FIFTH
FIFTH_THIRD -> 9 | m3 | 9 ROOTX | m3 ROOTX | 4 THIRD_FIFTH | m8 THIRD_FIFTH
ROOTX -> 3 | m9 | 7 | m5 | 3 THIRDX | m9 THIRDX | 7 FIFTHX | m5 FIFTHX
THIRDX -> 4 | m8 | 9 | m3 | 4 FIFTHX | m8 FIFTHX | 9 ROOTX | m3 ROOTX
FIFTHX -> 5 | m7 | 8 | m4 | 5 ROOTX | m7 ROOTX | 8 THIRDX | m4 THIRDX
0 -> m1 1
0 -> m2 2
0 -> 2 m2
0 -> 1 m1
0 -> 0 0
0 -> m1 1
m4 -> m2 m2
m3 -> m1 m2
m3 -> m2 m1
3 -> 2 1
3 -> 1 2
4 -> 2 2
0 -> '0'
1 -> '1'
2 -> '2'
3 -> '3'
4 -> '4'
5 -> '5'
6 -> '6'
7 -> '7'
8 -> '8'
9 -> '9'
10 -> '10'
11 -> '11'
12 -> '12'
13 -> '13'
14 -> '14'
15 -> '15'
16 -> '16'
17 -> '17'
18 -> '18'
19 -> '19'
20 -> '20'
21 -> '21'
22 -> '22'
23 -> '23'
24 -> '24'
m24 -> '-24'
m23 -> '-23'
m22 -> '-22'
m21 -> '-21'
m20 -> '-20'
m19 -> '-19'
m18 -> '-18'
m17 -> '-17'
m16 -> '-16'
m15 -> '-15'
m14 -> '-14'
m13 -> '-13'
m12 -> '-12'
m11 -> '-11'
m10 -> '-10'
m9 -> '-9'
m8 -> '-8'
m7 -> '-7'
m6 -> '-6'
m5 -> '-5'
m4 -> '-4'
m3 -> '-3'
m1 -> '-1'
m2 -> '-2'

"""


notes = {0:'C', 1:'C#', 2:'D', 3:'Eb',4:'E', 5:'F', 6:'F#', 7:'G', 8:'Ab', 9: 'A', 10:'Bb', 11:'B'}
intervalMap = {'m3':3, 'M3':4,'P4':5, 'P5': 7,'m6':8, 'M6':9}

oneExample =['m6', 'M6', 'P5', 'm6', 'M6', 'P5', 'P4', 'P5']
def main():
	S, R, TH, F = nonterminals('S, R, TH, F')
	thisGrammar = CFG.fromstring(gramHarmonyMinorBothDirections)
	#thisGrammar = parse_cfg(gramStringRecurFixed2)
	for l in generate_local.generate_local(thisGrammar, depth=10):
		startNote = 0
		lastNote = startNote
		octave = 0
		chord = notes[lastNote] + str(octave) + ','
		print(l)
		for i in l:
			curNote = int(i)
			lastNote = (lastNote + curNote) % 12
			if lastNote + curNote > 11:
				octave += 1
			if lastNote + curNote < -11:
				octave -= 1
			chord += notes[lastNote] + str(octave) + ','
		print(chord)
	thisParser = TopDownChartParser(thisGrammar)
	print(thisGrammar.check_coverage(oneExample))
	#thisParser.trace(3)
	#tree = thisParser.chart_parse(oneExample, 3)# = treebank.parsed_sents('wsj_0001.mrg')[0].leaves()
	#print sent
	print (str(thisParser.grammar().productions()))
	#for parse in thisParser.nbest_parse(oneExample):
	#	print (parse)

		#print ' '.join(sent)

if __name__ == "__main__":
    main()
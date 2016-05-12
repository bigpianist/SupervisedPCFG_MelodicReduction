
majorScaleMajorChords = ['I', 'IV', 'V']
majorScaleMinorChords = ['II', 'III', 'VI']

minorScaleMajorChords = ['III', 'VI', 'VII']
minorScaleMinorChords = ['I', 'IV', 'V']

majorScaleChordDegreeToPitchClass = {'I':0, 'II':2, 'III':4, 'IV':5, 'V':7, 'VI':9, 'VII':11}
minorScaleChordDegreeToPitchClass = {'I':0, 'II':2, 'III':3, 'IV':5, 'V':7, 'VI':8, 'VII':10}

majorDegreeToPitchClass = {1:0, 2:2, 3:4, 4:5, 5:7, 6:9, 7:11}
minorDegreeToPitchClass = {1:0, 2:2, 3:3, 4:5, 5:7, 6:8, 7:10}

#this function creates the string for a grammar that arpeggiates either a major or minor chord
#it also includes embellishment rules


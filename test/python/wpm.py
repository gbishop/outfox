import pyTTS

def words():
    return '''\
Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Nulla velit sapien, elementum sit amet, rhoncus vitae, mattis et, turpis. Pellentesque tristique, felis ac fringilla mollis, mi ante tincidunt dolor, non varius nisi est a ligula. Nulla elit eros, imperdiet sed, pretium a, facilisis eget, ante. Fusce quis magna non ipsum ornare pulvinar. Etiam facilisis eros. Nullam cursus gravida pede. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Suspendisse eros odio, sollicitudin a, aliquam nec, commodo id, ante. Nunc elit mi, lobortis eu, vestibulum eget, luctus at, arcu. Suspendisse ultricies. Pellentesque eget massa. Aliquam viverra, nunc. '''

tts = pyTTS.Create(output=False)
tts.SetOutputFormat(22, 8, 1)
w = words()
print len(w)
for i in xrange(-5,20):
    tts.Rate = i
    stream, events = tts.Speak(w)
    format = stream.Format.GetWaveFormatEx()
    bytes = stream.GetData()
    print i, (100.0/len(bytes)) * (22050) * 60

'''
y = ab**x
a = 102.19150898501448
b = 1.1154117185341268
-5 59
-4 66
-3 73
-2 82
-1 91
0 103
1 114
2 127
3 142
4 159
5 176
6 197
7 220
8 246
9 272
10 306
11 341
12 383
13 427
14 476
15 526
16 586
17 643
18 720
'''

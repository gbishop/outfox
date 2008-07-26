import pyTTS

def words():
    yield ('''\
Outfox is a Firefox extension that allows in-page JavaScript to access local platform services and devices such as text-to-speech synthesis, sound playback, game controllers, etc. The devices available for use are defined by optional modules loaded by an external socket server process. Communication between the external modules and the page JavaScript is bidirectional to support messages and callbacks in both directions.''', 64)
    yield ('''\
The ability to store and execute lists of instructions called programs makes computers extremely versatile and distinguishes them from calculators. The Church-Turing thesis is a mathematical statement of this versatility: any computer with a certain minimum capability is, in principle, capable of performing the same tasks that any other computer can perform. Therefore, computers with capability and complexity ranging from that of a personal digital assistant to a supercomputer are all able to perform the same computational tasks given enough time and storage capacity.''', 85)
    yield ('''\
In most cases, computer instructions are simple: add one number to another, move some data from one location to another, send a message to some external device, etc. These instructions are read from the computer's memory and are generally carried out (executed) in the order they were given. However, there are usually specialized instructions to tell the computer to jump ahead or backwards to some other place in the program and to carry on executing from there. These are called "jump" instructions (or branches). Furthermore, jump instructions may be made to happen conditionally so that different sequences of instructions may be used depending on the result of some previous calculation or some external event. Many computers directly support subroutines by providing a type of jump that "remembers" the location it jumped from and another instruction to return to the instruction following that jump instruction.
''', 143)

tts = pyTTS.Create(output=False)
tts.SetOutputFormat(22, 8, 1)
tts.Voice = 'MSMike'

for rate in xrange(-5,20):
    tts.Rate = rate
    avg = 0
    for text, count in words():
        stream, events = tts.Speak(text)
        format = stream.Format.GetWaveFormatEx()
        bytes = stream.GetData()
        avg += (float(count)/len(bytes)) * (22050) * 60
    avg /= 3.0
    print rate, round(avg,0)

'''
Sam    Mary Mike
-5 80  91   89
-4 89  101  100
-3 99  113  111
-2 111 126  124
-1 123 140  138
0  138 157  154
1  153 175  172
2  171 195  192
3  191 217  214
4  213 242  239
5  238 270  266
6  265 301  296
7  296 336  331
8  329 373  367
9  365 417  411
10 407 463  457
11 453 516  510
12 509 575  572
13 561 641  632
14 634 711  707
15 705 796  782
16 776 886  874
17 849 992  969
18 927 1103 1034
'''

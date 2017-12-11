import argparse
import logging
import multiprocessing
import os
import sys

import gentle

parser = argparse.ArgumentParser(
        description='Align a transcript to audio by generating a new language model.  Outputs JSON')
parser.add_argument(
        '--nthreads', default=multiprocessing.cpu_count(), type=int,
        help='number of alignment threads')
parser.add_argument(
        '-o', '--output', metavar='output', type=str, 
        help='output filename')
parser.add_argument(
        '--conservative', dest='conservative', action='store_true',
        help='conservative alignment')
parser.set_defaults(conservative=False)
parser.add_argument(
        '--disfluency', dest='disfluency', action='store_true',
        help='include disfluencies (uh, um) in alignment')
parser.set_defaults(disfluency=False)
parser.add_argument(
        '--log', default="INFO",
        help='the log level (DEBUG, INFO, WARNING, ERROR, or CRITICAL)')
parser.add_argument(
        'audiofile', type=str,
        help='audio file')
parser.add_argument(
        'txtfile', type=str,
        help='transcript text file')
args = parser.parse_args()

log_level = args.log.upper()
logging.getLogger().setLevel(log_level)

disfluencies = set(['uh', 'um'])

def on_progress(p):
    for k,v in p.items():
        logging.debug("%s: %s" % (k, v))


with codecs.open(args.txtfile, "r",encoding='utf-8', errors='ignore') as fh:
    transcript = fh.read()
    print transcript

resources = gentle.Resources()
logging.info("converting audio to 8K sampled wav")

sens_end_index = None
with gentle.resampled(args.audiofile) as wavfile:
    logging.info("starting alignment")

    aligner = gentle.ForcedAligner(resources, transcript, nthreads=args.nthreads, disfluency=args.disfluency, conservative=args.conservative, disfluencies=disfluencies)
    result = aligner.transcribe(wavfile, progress_cb=on_progress, logging=logging)
    sens_end_index=aligner.ms.get_sentences_index()

print result
res = result.to_json()
res = json.loads(res)
time_sentences_index = []
#print len(sens_end_index)
#print sens_end_index

time_sentences_index = []
ss_dot = 0
s_pos = None
time_pos = 0
for i,w in enumerate(res['words']):
    end_v = w['endOffset']
    start_v = w['startOffset']

    print end_v, sens_end_index[ss_dot]
    if s_pos is None:
        s_pos = start_v

    if end_v >= sens_end_index[ss_dot]:
        ss_dot += 1
        time_sentences_index.append((res['words'][time_pos]["start"], res['words'][i]["end"]))
        if i+1 < len(res['words']):
            s_pos = res['words'][i+1]['startOffset']
            time_pos =i+1
        else:
            s_pos = end_v
            time_pos = i

if len(sens_end_index) != len(time_sentences_index):
    time_sentences_index.append((res['words'][time_pos]["start"], res['words'][-1]["end"]))

print sens_end_index, len(sens_end_index)
print time_sentences_index, len(time_sentences_index)
sens_str=aligner.ms.get_sentences_string()
for i,t in enumerate(time_sentences_index):
    print "{{time}}%s/%s{{end}}"%(str(round(float(t[0]),2)),str(round(float(t[1]),2)))
    print "{{raw}}%s{{end}}"%(sens_str[i])



'''
with gentle.resampled(args.audiofile) as wavfile:
    logging.info("starting alignment")
    aligner = gentle.ForcedAligner(resources, transcript, nthreads=args.nthreads, disfluency=args.disfluency, conservative=args.conservative, disfluencies=disfluencies)
    result = aligner.transcribe(wavfile, progress_cb=on_progress, logging=logging)

fh = open(args.output, 'w') if args.output else sys.stdout
fh.write(result.to_json(indent=2))
if args.output:
    logging.info("output written to %s" % (args.output))
'''

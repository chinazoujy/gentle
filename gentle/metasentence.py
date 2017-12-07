# coding=utf-8
import re
import unicodedata
import chardet
reload(sys)
sys.setdefaultencoding('utf-8')

# [oov] no longer in words.txt
OOV_TERM = '<unk>'

def load_vocabulary(words_file):
    '''Load vocabulary words from an OpenFST SymbolTable formatted text file'''
    return set(x.split(' ')[0] for x in words_file if x != '')

def kaldi_normalize(word, vocab):
    """
    Take a token extracted from a transcript by MetaSentence and
    transform it to use the same format as Kaldi's vocabulary files.
    Removes fancy punctuation and strips out-of-vocabulary words.
    """
    # lowercase
    norm = word.lower()
    # Turn fancy apostrophes into simpler apostrophes
    norm = norm.replace("’", "'")
    if len(norm) > 0 and not norm in vocab:
        norm = OOV_TERM
    return norm

default_properties={
        "annotators": "ssplit",
        "outputFormat": "json",
        # Only split the sentence at End Of Line. We assume that this method only takes in one single sentence.
        #"ssplit.eolonly": "false",
        # Setting enforceRequirements to skip some annotators and make the process faster
        #"enforceRequirements": "false"
    }
def getCoreNLP(text, properties=default_properties):
    """
    :param text:
    :param properties:
    :return: None
            stanfordnlp error information
            json of response
    """
    import requests, json

    if properties is None:
        properties = {}
    else:
        assert isinstance(properties, dict)

    url = "http://123.56.233.88:9000/"
    # request_params = {"annotators": annotators}
    # r = requests.post(url, data=text, params=request_params)
    # return r.json()

    data = text.encode()
    try:
        r = requests.post(
            url, params={
                'properties': str(properties)
            }, data=data, headers={'Connection': 'close'})
    except:
        traceback.print_exc()
        return None

    output = r.text
    if ('outputFormat' in properties
        and properties['outputFormat'] == 'json'):
        try:
            output = json.loads(output, encoding='utf-8', strict=True)
        except:
            pass
    return output

def is_isalpha_or_value(ss):
    if ss==',' or ss=='.' or ss=='?' or ss=='!' or ss=='"' or ss=="'":
        return False
    return True

class MetaSentence:
    """Maintain two parallel representations of a sentence: one for
    Kaldi's benefit, and the other in human-legible form.
    """

    def __init__(self, sentence, vocab):
        self.raw_sentence = sentence
        #str_chartype = chardet.detect(sentence)
        #self.raw_sentence = sentence.decode(str_chartype["encoding"]).encode("utf-8").strip()
        if type(sentence) != unicode:
            self.raw_sentence = sentence.decode('utf-8')
        self.vocab = vocab
        self.stanford_info = getCoreNLP(self.raw_sentence)
        self._tokenize()

    def _tokenize(self):
        self._seq = []
        '''
        for m in re.finditer(ur'(\w|\’\w|\'\w)+', self.raw_sentence, re.UNICODE):
            start, end = m.span()
            word = m.group().encode('utf-8')
            token = kaldi_normalize(word, self.vocab)
            self._seq.append({
                "start": start, # as unicode codepoint offset
                "end": end, # as unicode codepoint offset
                "token": token,
            })
         '''
        sentences = self.stanford_info['sentences']
        for sen in sentences:
            next_continue = False
            for i,w in enumerate(sen['tokens']):
                #if next_continue:
                #    next_continue = False
                #    continue
                word = w['word'].encode('utf-8')
                if not is_isalpha_or_value(word):
                    continue
                '''
                if i+1 < len(sen['tokens']):
                    if sen['tokens'][i+1]['word'] == "n't":
                        token = kaldi_normalize(word+sen['tokens'][i+1]['word'], self.vocab)
                        self._seq.append({
                            "start": w['characterOffsetBegin'], # as unicode codepoint offset
                            "end": sen['tokens'][i+1]['characterOffsetEnd'], # as unicode codepoint offset
                            "token": token,
                        })
                        next_continue = True
                else:
                    token = kaldi_normalize(word, self.vocab)
                    self._seq.append({
                        "start": w['characterOffsetBegin'], # as unicode codepoint offset
                        "end": w['characterOffsetEnd'], # as unicode codepoint offset
                        "token": token,
                    })
                '''
                token = kaldi_normalize(word, self.vocab)
                self._seq.append({
                        "start": w['characterOffsetBegin'], # as unicode codepoint offset
                        "end": w['characterOffsetEnd'], # as unicode codepoint offset
                        "token": token,
                    })
    
    def get_sentences_string(self):
        sentences = []
        for sen in self.stanford_info['sentences']:
            sentences.append(" ".join([w['word'] for w in sen['tokens']]))
        return sentences
    
    def get_sentences_index(self):
        sentence_end_off = []
        for sen in self.stanford_info['sentences']:
            if len(sen['tokens']) < 2:
                continue
            #print sen['tokens'][-2]['word'],sen['tokens'][-2]['characterOffsetEnd']
            #print sen['tokens'][-1]['word'], sen['tokens'][-1]['characterOffsetEnd']
            if sen['tokens'][-1]['word'].isalpha():
                sentence_end_off.append(sen['tokens'][-1]['characterOffsetEnd'])
            else:
                sentence_end_off.append(sen['tokens'][-2]['characterOffsetEnd'])
        return sentence_end_off
            
    def get_kaldi_sequence(self):
        return [x["token"] for x in self._seq]

    def get_display_sequence(self):
        display_sequence = []
        for x in self._seq:
            start, end = x["start"], x["end"]
            word = self.raw_sentence[start:end].encode('utf-8')
            display_sequence.append(word)
        return display_sequence

    def get_text_offsets(self):
        return [(x["start"], x["end"]) for x in self._seq]

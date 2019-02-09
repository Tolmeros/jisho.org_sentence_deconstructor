import argparse
import re
import unicodedata
from urllib.request import urlopen


from bs4 import BeautifulSoup


jisho_org_sentences = re.compile(
    r'^https?://jisho\.org/sentences/[A-Z0-9]+/?$', re.IGNORECASE)


def check_url(value):
    if not test_url(value):
        raise argparse.ArgumentTypeError("%s is an invalid url." % value)
    return value


def test_url(url):
    return re.match(jisho_org_sentences, url) is not None

def get_page(url):
    return urlopen(url)

def get_sentence(html):
    #<div class="sentence_content">
    soup = BeautifulSoup(html, 'html.parser')
    return soup.find('div', attrs={'class':'sentence_content'})


def is_kanji(ch):
    return 'CJK UNIFIED IDEOGRAPH' in unicodedata.name(ch)

def process_sentence(sentence):
    def split_jishoorg_furigana(furigana,text):
        kanji_text=''
        for c in text:
            if is_kanji(c):
                kanji_text += c
        return text.replace(kanji_text,furigana)

    def ja(ul_tag):
        data = {
            'kana':[],
            'mixed':[],
        }

        for tag in ul_tag.find_all('li', recursive=False):
            spans = {x.attrs['class'][0]:x for x in tag.find_all('span')}
            if 'furigana' in spans:
                data['kana'].append(
                    split_jishoorg_furigana(spans['furigana'].text,
                                            spans['unlinked'].text))
            else:
                data['kana'].append(spans['unlinked'].text)

            data['mixed'].append(spans['unlinked'].text)
        return data


    #analyse
    collected_data = {}
    tags = []

    for tag in sentence.find_all(recursive=False):
        tags.append({'tag':tag.name, 'attrs': tag.attrs})
        if tag.name == 'div':
            if 'english_sentence' in tag.attrs['class']:
                #spans = tag.find_all('span', recursive=False)
                spans = { span.attrs['class'][0]: span for span in tag.find_all('span', recursive=False)}
                collected_data['english'] = {
                    'text': spans['english'].text,
                    'source': spans['inline_copyright'].find('a').attrs['href'],
                }


        elif tag.name == 'ul':
            if 'japanese_sentence' in tag.attrs['class']:
                collected_data['japanese'] = ja(tag)



    return collected_data


def make_text(data):
    s = ''
    s += '{}\n'.format(''.join(data['japanese']['mixed']))
    s += '{}\n'.format(' '.join(data['japanese']['kana']))
    s += '{}\n'.format(''.join(data['english']['text']))
    s += '\n{}\n'.format(''.join(data['english']['source']))
    return s


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', type=check_url)
    args = parser.parse_args()

    page = get_page(args.url)
    sentence = get_sentence(page)

    text = make_text(process_sentence(sentence))
    print(text)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Sample demo — runs with no database and no dependencies.

Uses a ~550-article sample of the Kosovo legal corpus (laws only, no court decisions,
no personal data). The production path is backend/hackathon/demo.py against Postgres +
pgvector with 353k chunks; this file exists so a judge can see the behaviour in seconds:

    python demo_sample.py "Çfarë duhet të përmbajë kontrata e punës?"

Scoring is the production idea, simplified: BM25 over the article text, a bonus when the
query terms appear in the article heading, and a refusal when nothing scores.
"""
import json, math, re, sys
from pathlib import Path

STOP = set('dhe të te e i a në ne me për per nga se si kur sa çka cka çfarë cfare është eshte kush cilat cilët ku ka kanë kane nuk po më'.split())
WORD = re.compile(r'[a-zëç0-9]+')


def stem(w):
    return w[:6] if len(w) > 6 else w


def tokens(text):
    return [stem(w) for w in WORD.findall(text.lower()) if w not in STOP and len(w) > 2]


class Index:
    def __init__(self, rows):
        self.rows = rows
        self.docs = [tokens(r['text']) for r in rows]
        heads = []
        for r in rows:
            lines = r['text'].split(chr(10))
            heading = lines[0] if lines else ''
            heads.append(tokens(r['title'] + ' ' + heading + ' ' + r['section']))
        self.heads = heads
        self.N = len(rows)
        self.avg = sum(len(d) for d in self.docs) / max(self.N, 1)
        self.df = {}
        for d in self.docs:
            for w in set(d):
                self.df[w] = self.df.get(w, 0) + 1

    def idf(self, w):
        n = self.df.get(w, 0)
        return math.log(1 + (self.N - n + 0.5) / (n + 0.5))

    def search(self, query, k=5):
        q = tokens(query)
        if not q:
            return []
        qs = set(q)
        scored = []
        for i, doc in enumerate(self.docs):
            tf = {}
            for w in doc:
                if w in qs:
                    tf[w] = tf.get(w, 0) + 1
            if not tf:
                continue
            s = 0.0
            for w, f in tf.items():
                s += self.idf(w) * (f * 2.2) / (f + 1.2 * (0.25 + 0.75 * len(doc) / self.avg))
            head_hits = sum(1 for w in qs if w in self.heads[i])
            cover = head_hits / len(qs)
            scored.append((s + 3.0 * cover, cover, i))
        scored.sort(reverse=True)
        return [(sc, cov, self.rows[i]) for sc, cov, i in scored[:k]]


def main() -> int:
    here = Path(__file__).resolve().parent
    rows = [json.loads(l) for l in (here / 'sample_corpus.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    idx = Index(rows)
    questions = sys.argv[1:] or ['Çfarë duhet të përmbajë kontrata e punës?']
    for q in questions:
        hits = idx.search(q)
        print('Pyetja:', q)
        if not hits or hits[0][0] < 2.0:
            print("  s'e di — asnjë nen në mostër nuk i përgjigjet kësaj pyetjeje.")
            print()
            continue
        for n, (score, cov, r) in enumerate(hits, 1):
            body = ' '.join(r['text'].split())[:230]
            print('  [%d] %s — %s  (skor %.2f, mbulim %.0f%%)' % (n, r['title'], r['section'], score, cov * 100))
            print('      ' + body)
        print()
    titles = len({r['title'] for r in rows})
    print('Mostra: %d nene nga %d ligje. Pa baze te dhenash, pa varesi.' % (len(rows), titles))
    return 0


if __name__ == '__main__':
    sys.exit(main())
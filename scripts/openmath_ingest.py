"""OpenMathReasoning Dataset Ingest (Prototype)

Usage:
  python scripts/openmath_ingest.py --input path/to/openmath.jsonl --output data/openmath_sample.jsonl --sample 5000

Steps:
 1. Stream read JSONL entries (expects keys: problem/question, solutions/answers)
 2. Deduplicate by SHA1 of problem text
 3. Filter overly long problems (>1500 chars) or empty solutions
 4. Down-sample to requested size
 5. Write normalized subset (problem, solution)
"""
from __future__ import annotations
import argparse, json, hashlib, random, os

def iter_jsonl(path):
    with open(path,'r',encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try:
                yield json.loads(line)
            except Exception:
                continue

def normalize_entry(entry):
    prob = entry.get('problem') or entry.get('question') or ''
    sols = entry.get('solutions') or entry.get('answers') or []
    if isinstance(sols, str):
        sols = [sols]
    first = sols[0] if sols else ''
    return prob.strip(), first.strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--sample', type=int, default=5000)
    args = ap.parse_args()
    seen = set()
    buf = []
    for obj in iter_jsonl(args.input):
        prob, sol = normalize_entry(obj)
        if not prob or not sol:
            continue
        if len(prob) > 1500:
            continue
        h = hashlib.sha1(prob.encode('utf-8')).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        buf.append({'problem': prob, 'solution': sol})
    random.shuffle(buf)
    subset = buf[:args.sample]
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output,'w',encoding='utf-8') as f:
        for e in subset:
            f.write(json.dumps(e, ensure_ascii=False)+'\n')
    print(f"Wrote {len(subset)} entries to {args.output}")

if __name__ == '__main__':
    main()

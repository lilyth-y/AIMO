"""Log Analysis Script

Parses logs/eval_log.jsonl and produces summary metrics:
 - Overall success rate
 - Strategy first-attempt success rate
 - Mismatch breakdown
 - Average complexity_score by strategy
 - Top lemma patterns (if lemma cache snapshot saved)

Usage:
  python scripts/analyze_logs.py
"""
from __future__ import annotations
import json, os, statistics
from collections import defaultdict, Counter

LOG_PATH = os.path.join('logs','eval_log.jsonl')

def load_logs(path=LOG_PATH):
    if not os.path.exists(path):
        print('No log file found:', path)
        return []
    entries = []
    with open(path,'r',encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try:
                entries.append(json.loads(line))
            except Exception:
                pass
    return entries

def summarize(entries):
    if not entries:
        print('No entries to summarize.')
        return
    total = len(entries)
    verified = sum(e.get('verified') for e in entries)
    print(f'Total entries: {total}')
    print(f'Overall success rate: {verified/total:.2%}')
    # first-attempt success (attempt==1 & verified True)
    first_attempt = [e for e in entries if e.get('attempt')==1]
    fa_rate = sum(e.get('verified') for e in first_attempt)/len(first_attempt) if first_attempt else 0
    print(f'First-attempt success rate: {fa_rate:.2%}')
    # strategy stats
    strat_stats = defaultdict(lambda: {'tries':0,'success':0,'complexities':[]})
    mismatch_counter = Counter()
    for e in entries:
        s = e.get('strategy')
        strat_stats[s]['tries']+=1
        if e.get('verified'): strat_stats[s]['success']+=1
        c = e.get('complexity_score')
        if c is not None: strat_stats[s]['complexities'].append(c)
        mt = e.get('mismatch_type')
        if mt: mismatch_counter[mt]+=1
    print('\nStrategy Performance:')
    for s,data in strat_stats.items():
        rate = data['success']/data['tries'] if data['tries'] else 0
        avg_c = statistics.mean(data['complexities']) if data['complexities'] else 0
        print(f" - {s}: success={rate:.2%} avg_complexity={avg_c:.2f} trials={data['tries']}")
    if mismatch_counter:
        print('\nMismatch Breakdown:')
        total_mm = sum(mismatch_counter.values())
        for k,v in mismatch_counter.items():
            print(f' - {k}: {v} ({v/total_mm:.1%})')

def main():
    entries = load_logs()
    summarize(entries)

if __name__ == '__main__':
    main()

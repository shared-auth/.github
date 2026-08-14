#!/usr/bin/env python3
import re,sys
from pathlib import Path
RULE=re.compile(r"^\s*-\s*path_regex:\s*(.+?)\s*$"); ITEM=re.compile(r"^\s*-\s*(\S+)\s*$")
EXACT={r"^env/enc/dev\.env\.enc$":"dev",r"^env/enc/prod\.env\.enc$":"prod"}
def parse(p):
 out={"dev":set(),"prod":set()}; cur=None; age=False
 for raw in Path(p).read_text().splitlines():
  m=RULE.match(raw)
  if m: cur=EXACT.get(m.group(1).strip().strip("\"'")); age=False; continue
  if cur and raw.strip()=="age:": age=True; continue
  if age:
   m=ITEM.match(raw)
   if m and m.group(1).startswith("age1"): out[cur].add(m.group(1)); continue
   if raw.strip() and not raw.strip().startswith("#"): age=False
 return out
if len(sys.argv)!=3: raise SystemExit(2)
if sys.argv[2].lower()!="prod": raise SystemExit(0)
r=parse(sys.argv[1]); d=r["dev"]; p=r["prod"]
if not d or len(p)<2 or not p-d or p==d: raise SystemExit("invalid production SOPS recipient policy")
print(f"production SOPS policy verified (dev recipients={len(d)}, prod recipients={len(p)})")

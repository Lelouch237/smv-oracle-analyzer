from __future__ import annotations
import json
import time
import logging
import ccxt
import pandas as pd
from datetime import datetime, timezone
from os import getenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

EXCHANGE_ID=getenv("EXCHANGE","binance")
SYMBOLS=[x.strip() for x in getenv("SYMBOLS","BTC/USDT").split(",") if x.strip()]
HTF=getenv("HTF","1h")
LTF=getenv("LTF","5m")
LIMIT=int(getenv("CANDLE_LIMIT","500"))
POLL_SECONDS=int(getenv("POLL_SECONDS","30"))
LEFT=int(getenv("PIVOT_LEFT","2"))
RIGHT=int(getenv("PIVOT_RIGHT","2"))

def fetch(ex, symbol, tf):
    rows=ex.fetch_ohlcv(symbol, tf, limit=LIMIT)
    return pd.DataFrame(rows, columns=["ts","open","high","low","close","volume"])

def pivots(df):
    out=[]
    for i in range(LEFT, len(df)-RIGHT):
        h=float(df.iloc[i].high); l=float(df.iloc[i].low)
        if h>df.iloc[i-LEFT:i].high.max() and h>=df.iloc[i+1:i+1+RIGHT].high.max():
            out.append((i,"HIGH",h))
        if l<df.iloc[i-LEFT:i].low.min() and l<=df.iloc[i+1:i+1+RIGHT].low.min():
            out.append((i,"LOW",l))
    out.sort()
    return out

def structure(df):
    ps=pivots(df)
    highs=[(i,p) for i,k,p in ps if k=="HIGH"]
    lows=[(i,p) for i,k,p in ps if k=="LOW"]
    labels=[]
    for j in range(1,len(highs)):
        i,p=highs[j]; prev=highs[j-1][1]
        labels.append((i,"HH" if p>prev else "LH",p))
    for j in range(1,len(lows)):
        i,p=lows[j]; prev=lows[j-1][1]
        labels.append((i,"HL" if p>prev else "LL",p))
    labels.sort()
    recent=[x[1] for x in labels[-6:]]
    if len(recent)>=2 and all(x in {"HH","HL"} for x in recent[-2:]) and ("HH" in recent and "HL" in recent):
        bias="BULLISH"
    elif len(recent)>=2 and all(x in {"LL","LH"} for x in recent[-2:]) and ("LL" in recent and "LH" in recent):
        bias="BEARISH"
    else:
        bias="MIXED/UNDEFINED"
    return {"bias":bias,"last_label":recent[-1] if recent else None,"recent_labels":recent}

def run_once():
    ex=getattr(ccxt,EXCHANGE_ID)({"enableRateLimit":True})
    report={"timestamp":datetime.now(timezone.utc).isoformat(),"execution_allowed":False,"symbols":{}}
    for symbol in SYMBOLS:
        htf=fetch(ex,symbol,HTF); ltf=fetch(ex,symbol,LTF)
        report["symbols"][symbol]={
            "htf":structure(htf),
            "ltf":structure(ltf),
            "liquidity":"UNDEFINED",
            "intervention_zones":"UNDEFINED",
            "order_blocks":"UNDEFINED",
            "breaker_blocks":"UNDEFINED",
            "refinement":"UNDEFINED",
            "swing_strategy":"UNDEFINED",
            "intraday_strategy":"UNDEFINED",
            "precise_entry":"UNDEFINED",
            "final_signal":"WAIT / INCOMPLETE_RULESET"
        }
    with open("last_report.json","w",encoding="utf-8") as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
    logging.info(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=="__main__":
    logging.info("SMV ORACLE Analyzer — lecture seule — execution disabled")
    while True:
        try:
            run_once()
        except Exception:
            logging.exception("Erreur pendant l'analyse")
        time.sleep(max(5,POLL_SECONDS))

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import yfinance as yf
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

from smv.structure import analyze_structure

app = FastAPI(title="SMV ORACLE Analyzer", version="0.1.0")

INDEX_HTML = """
<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SMV ORACLE — EUR/USD</title>
<style>
:root{color-scheme:dark}
body{margin:0;background:#0e1117;color:#e7edf4;font-family:Arial,sans-serif}
header{padding:18px 22px;border-bottom:1px solid #29303b;background:#151922}
h1{font-size:22px;margin:0 0 5px}.sub{color:#9aa5b4}
main{display:grid;grid-template-columns:2fr 1fr;gap:14px;padding:14px}
.card{background:#151922;border:1px solid #29303b;border-radius:10px;overflow:hidden}
.title{padding:12px 14px;border-bottom:1px solid #29303b;font-weight:700}
iframe{display:block;width:100%;height:650px;border:0}
.panel{padding:14px}.row{display:flex;justify-content:space-between;gap:10px;padding:9px 0;border-bottom:1px solid #252c36}
.muted{color:#9aa5b4}.on{color:#8ee69a}.wait{color:#ffd166}.off{color:#ff8e8e}
.value{font-weight:700}
.note{margin-top:14px;padding:12px;border-radius:8px;background:#202632;color:#c8d0da;line-height:1.45}
.updated{font-size:12px;color:#7f8998;margin-top:10px}
@media(max-width:900px){main{grid-template-columns:1fr}iframe{height:500px}}
</style>
</head>
<body>
<header>
<h1>SMV ORACLE — EUR/USD</h1>
<div class="sub">Analyseur en lecture seule • aucun ordre n'est possible</div>
</header>
<main>
<section class="card">
<div class="title">EUR/USD — graphique</div>
<iframe src="https://www.tradingview.com/widgetembed/?symbol=FX%3AEURUSD&interval=5&theme=dark&style=1&timezone=Africa%2FDouala&hideideas=1&hidevolume=1" loading="eager"></iframe>
</section>
<aside class="card">
<div class="title">Analyse réelle du backend</div>
<div class="panel" id="panel">
<div class="row"><span class="muted">Statut</span><b class="wait">Connexion...</b></div>
</div>
</aside>
</main>
<script>
async function refresh(){
  const p=document.getElementById("panel");
  try{
    const r=await fetch("/api/analysis",{cache:"no-store"});
    const d=await r.json();
    const rows=[
      ["Heure UTC",d.timestamp],
      ["Dernier prix",d.price ?? "—"],
      ["HTF (1h)",d.htf.bias],
      ["Dernier label HTF",d.htf.last_label ?? "—"],
      ["Pivots HTF",d.htf.pivots.length],
      ["LTF (5m)",d.ltf.bias],
      ["Dernier label LTF",d.ltf.last_label ?? "—"],
      ["Pivots LTF",d.ltf.pivots.length],
      ["HH / HL / LL / LH","ACTIVÉS"],
      ["Liquidité","À DÉFINIR ORACLE"],
      ["Zones d'intervention","À DÉFINIR ORACLE"],
      ["Order Blocks","À DÉFINIR ORACLE"],
      ["Breaker Blocks","À DÉFINIR ORACLE"],
      ["Raffinage","À DÉFINIR ORACLE"],
      ["Entrée précise","À DÉFINIR ORACLE"],
      ["Ordres réels","DÉSACTIVÉS"],
    ];
    p.innerHTML=rows.map(([a,b])=>`<div class="row"><span class="muted">${a}</span><b class="value">${b}</b></div>`).join("")
      + `<div class="note"><b>Décision actuelle :</b><br>${d.decision}<br><br>${d.explanation.join("<br>")}</div>`;
  }catch(e){
    p.innerHTML='<div class="row"><span class="muted">Statut</span><b class="off">Erreur de flux</b></div><div class="note">'+e.message+'</div>';
  }
}
refresh(); setInterval(refresh,30000);
</script>
</body>
</html>
"""

def get_data(period: str, interval: str) -> pd.DataFrame:
    ticker = yf.Ticker("EURUSD=X")
    df = ticker.history(period=period, interval=interval, auto_adjust=False)
    if df.empty:
        raise RuntimeError("Aucune donnée EUR/USD reçue.")
    df = df.reset_index()
    df.columns = [str(c).lower().replace(" ", "_") for c in df.columns]
    rename = {"datetime":"timestamp"}
    df = df.rename(columns=rename)
    if "timestamp" not in df:
        df["timestamp"] = pd.date_range(end=datetime.now(timezone.utc), periods=len(df), freq=interval)
    for c in ("open","high","low","close","volume"):
        if c not in df.columns:
            raise RuntimeError(f"Colonne manquante: {c}")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df[["timestamp","open","high","low","close","volume"]].dropna().reset_index(drop=True)

@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX_HTML

@app.get("/health")
def health() -> dict[str, str]:
    return {"status":"ok","execution":"disabled"}

@app.get("/api/analysis", response_class=JSONResponse)
def analysis() -> dict[str, Any]:
    htf = get_data("7d", "1h")
    ltf = get_data("2d", "5m")
    hs = analyze_structure(htf, "HTF", 2, 2)
    ls = analyze_structure(ltf, "LTF", 2, 2)
    price = float(ltf.iloc[-1]["close"])

    explanations = []
    explanations.extend(hs.explanation[-3:])
    explanations.extend(ls.explanation[-3:])

    if hs.bias == "BULLISH":
        decision = "Contexte HTF haussier — attente des règles Liquidité/Zones/OB avant tout setup."
    elif hs.bias == "BEARISH":
        decision = "Contexte HTF baissier — attente des règles Liquidité/Zones/OB avant tout setup."
    else:
        decision = "Pas de biais HTF complet selon les règles de structure actuellement codées."

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "price": round(price, 6),
        "htf": {
            "bias": hs.bias,
            "last_label": hs.last_label,
            "pivots": hs.pivots[-10:],
        },
        "ltf": {
            "bias": ls.bias,
            "last_label": ls.last_label,
            "pivots": ls.pivots[-10:],
        },
        "decision": decision,
        "explanation": explanations,
        "execution_allowed": False,
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT","10000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

from __future__ import annotations
import argparse, json, logging, time
from marketplace.near_market import NearMarketClient
from worker.config import SETTINGS
from worker.scoring import score_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def sample_jobs():
    from marketplace.base import Job
    return [
        Job("sample-001","Write Python script to normalize CSV data",
            "Create a small Python utility that reads a CSV and cleans headers. Include README.",
            5,"NEAR",{"python","data"},1,24),
        Job("sample-002","Research two API providers",
            "Produce a short comparison with public sources.",
            1,"NEAR",{"research","api"},8,8),
        Job("sample-003","Vague task","",0.5,"NEAR",{"other"},20,1),
    ]

def rank(jobs):
    out = []
    for job in jobs:
        o = score_job(job, SETTINGS)
        out.append({
            "job_id": job.job_id, "title": job.title, "score": o.score,
            "reward": job.reward, "currency": job.reward_currency, "reasons": o.reasons
        })
    return sorted(out, key=lambda x: x["score"], reverse=True)

def run_sample():
    ranked = rank(sample_jobs())
    print(json.dumps(ranked, ensure_ascii=False, indent=2))
    logging.info("Mode sécurisé: DRY_RUN=%s ENABLE_AUTONOMY=%s", SETTINGS.dry_run, SETTINGS.enable_autonomy)

def run_scan():
    client = NearMarketClient(SETTINGS.market_base_url, SETTINGS.market_api_key)
    jobs = client.list_open_jobs(100)
    ranked = rank(jobs)
    print(json.dumps(ranked[:20], ensure_ascii=False, indent=2))

    if SETTINGS.dry_run or not SETTINGS.enable_autonomy:
        logging.info("DRY RUN / AUTONOMY OFF: aucun bid envoyé.")
        return

    selected = [x for x in ranked if x["score"] >= SETTINGS.min_score][:SETTINGS.max_bids_per_run]
    for item in selected:
        proposal = (
            f"I can deliver a verified result for '{item['title']}'. "
            "I will follow the exact requirements and provide clear verification steps."
        )
        logging.info("Bid result: %s", client.place_bid(item["job_id"], item["reward"], proposal))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sample", action="store_true")
    p.add_argument("--scan", action="store_true")
    p.add_argument("--loop", action="store_true")
    a = p.parse_args()

    if a.sample or not (a.scan or a.loop):
        run_sample()
        return

    if a.loop:
        while True:
            try:
                run_scan()
            except Exception:
                logging.exception("Cycle failed")
            time.sleep(max(30, SETTINGS.poll_seconds))
    else:
        run_scan()

if __name__ == "__main__":
    main()

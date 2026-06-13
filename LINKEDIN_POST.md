# LinkedIn launch post (ready to paste)

> Tip: paste the post body below directly into LinkedIn. Put the **GitHub repo link in the FIRST COMMENT**, not in the post body — LinkedIn suppresses reach on posts with outbound links. Upload the chart image where the screenshot marker is.

---

I built an end-to-end data pipeline that runs with **zero dependencies** — and it taught me more than any tutorial ever did.

As a student aiming for Data Analyst / Data Engineer roles, I wanted a project that proves I can do the *whole* flow, not just one notebook cell. So I built `ecommerce-data-pipeline`: it generates a realistic synthetic e-commerce dataset, loads it into a SQL warehouse, models it into a **star schema** (staging → dimensions + fact), and runs the analytics — all with the Python standard library only. Anyone can clone it and reproduce every number with one command: `python3 run_pipeline.py`.

[paste screenshot of outputs/charts/monthly_revenue_line.svg here]

A few things I actually learned building it:
- **Modeling matters more than queries.** Once I got the star schema right (fact at order-item grain + conformed dimensions), the "hard" business questions became simple SQL.
- **Window functions are everywhere.** I used LAG for month-over-month growth, RANK for a product leaderboard, and SUM() OVER() for share-of-total — they replaced a ton of messy subqueries.
- **Reproducibility is a feature.** Fixing a random seed and removing every external dependency means the project just *works* for whoever opens it. That mindset is half the job.

What the data showed (on 2,000 customers / 20K orders over 24 months):
- Revenue grew **+312%**, from ~$342K/mo to ~$1.41M/mo.
- **Enterprise customers = ~10% of accounts but 50% of revenue**, with a $2,749 AOV vs $605 for Consumer.
- Signup cohorts retain at **~46% after 3 months** — measured with a SQL cohort analysis.

I'd love feedback from people working in data — what would you add next? dbt? a real warehouse? a dashboard? Tearing it apart is how I learn.

Repo link in the first comment 👇

#DataAnalytics #DataEngineering #SQL #Python #BuildInPublic

---

## First comment (paste as the first comment after posting)

Here's the repo (clone + `python3 run_pipeline.py`, runs offline with no installs): <paste your GitHub repo URL here>

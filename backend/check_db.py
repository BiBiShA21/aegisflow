from pymongo import MongoClient
import os

client = MongoClient('mongodb://localhost:27017/')
db = client['aegisflow']
scans = list(db.repo_scans.find({'user_id': 'github_ci_cd_bot'}).sort('_id', -1).limit(2))
for s in scans:
    print(f"Repo: {s.get('repo_url')}, Risk: {s.get('overall_risk')}, Vulns: {s.get('total_vulnerabilities')}")

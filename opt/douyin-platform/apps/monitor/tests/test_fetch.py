import sys
sys.path.insert(0, "/opt/douyin-platform/apps/monitor")
from app import fetch_and_store_creator_works
fetch_and_store_creator_works()
print("Done")
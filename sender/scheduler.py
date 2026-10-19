import os
import json
import time
import subprocess
import logging
import hashlib
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
JOBS_DIR = "/app/jobs"
TZ = os.environ.get("TZ", "Europe/Moscow")
scheduler = BackgroundScheduler(timezone=TZ)

job_hashes = {}

def execute_job(name):
    file_path = os.path.join(JOBS_DIR, f"{name}.json")
    if not os.path.exists(file_path):
        return
    try:
        with open(file_path, "r") as f:
            job = json.load(f)
            
        text = job.get("text", "")
        logging.info(f"Выполняю: {name} -> {text}")
        
        subprocess.run(["python3", "/send.py"], env={**os.environ, "MSG_TEXT": text})

        if job.get("type") == "once":
            logging.info(f"Разовое задание {name} выполнено. Удаляю.")
            if scheduler.get_job(name):
                scheduler.remove_job(name)
            if os.path.exists(file_path):
                os.remove(file_path)
            return

        job["runs"] = job.get("runs", 0) + 1
        max_runs = job.get("max_runs", 0)

        if max_runs > 0 and job["runs"] >= max_runs:
            logging.info(f"Задание {name} выполнено {max_runs} раз. Удаляю.")
            if scheduler.get_job(name):
                scheduler.remove_job(name)
            if os.path.exists(file_path):
                os.remove(file_path)
        else:
            with open(file_path, "w") as f:
                json.dump(job, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Ошибка в задании {name}: {e}")

def get_file_hash(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def sync_jobs():
    if not os.path.exists(JOBS_DIR):
        return
        
    current_files = set()

    for filename in os.listdir(JOBS_DIR):
        if not filename.endswith(".json"):
            continue
        name = filename[:-5]
        file_path = os.path.join(JOBS_DIR, filename)
        current_files.add(name)

        new_hash = get_file_hash(file_path)
        if not new_hash:
            continue

        if name not in job_hashes or job_hashes[name] != new_hash:
            logging.info(f"Обнаружено новое или измененное задание: {name}")
            job_hashes[name] = new_hash
            
            if scheduler.get_job(name):
                scheduler.remove_job(name)

            try:
                with open(file_path, "r") as f:
                    job_data = json.load(f)
                
                if job_data.get("type") == "once":
                    run_date = datetime.strptime(job_data["run_date"], "%Y-%m-%d %H:%M:%S")
                    if run_date > datetime.now():
                        scheduler.add_job(execute_job, DateTrigger(run_date=run_date), args=[name], id=name)
                    else:
                        os.remove(file_path)
                elif job_data.get("type") == "interval":
                    val = int(job_data["interval_value"])
                    start_date = datetime.strptime(job_data["start_date"], "%Y-%m-%d %H:%M:%S") if job_data.get("start_date") else None
                    itype = job_data["interval_type"]
                    
                    if itype == "minutes":
                        trigger = IntervalTrigger(minutes=val, start_date=start_date)
                    elif itype == "hours":
                        trigger = IntervalTrigger(hours=val, start_date=start_date)
                    elif itype == "days":
                        trigger = IntervalTrigger(days=val, start_date=start_date)
                        
                    scheduler.add_job(execute_job, trigger, args=[name], id=name)
            except Exception as e:
                logging.error(f"Failed to schedule {name}: {e}")
                job_hashes.pop(name, None)

    for name in list(job_hashes.keys()):
        if name not in current_files:
            logging.info(f"Задание {name} удалено. Снимаю с расписания.")
            if scheduler.get_job(name):
                scheduler.remove_job(name)
            job_hashes.pop(name, None)

scheduler.start()
logging.info(f"Планировщик запущен. Часовой пояс: {TZ}")

while True:
    sync_jobs()
    time.sleep(2)
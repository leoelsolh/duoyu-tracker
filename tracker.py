
import os
import time
import json
import requests
from decrypt_getapp import load_config


URL = "https://transportstyrelsen-biljett.top/getApp"
FETCH = True
WEBHOOK_URL = os.environ.get("TRACKER_WEBHOOK_URL", "")
TRACKED_FIELDS = ["sn", "country", "pay_amount", "created_at", "updated_at", "wss_server"]


def tracked(config):

    return {k: config.get(k) for k in TRACKED_FIELDS}


def build_report(added, removed, modified, inventory, old_state):

    if not (added or removed or modified):
        return None

    lines = []

    if added:
        lines.append(f"[+] NEW DEPLOYMENTS ({len(added)}):")
        for id_ in added:
            c = inventory[id_]
            lines.append(
                f"    #{id_:>3}  {c['sn']:<14}  {c['country']:<4}  "
                f"{c['pay_amount']:<14}  created {c['created_at']}"
            )

    if removed:
        if lines:
            lines.append("")
        lines.append(f"[-] REMOVED ({len(removed)}):")
        for id_ in removed:
            lines.append(f"    #{id_}  ({old_state[id_]['sn']})")

    if modified:
        if lines:
            lines.append("")
        lines.append(f"[~] MODIFIED ({len(modified)}):")
        for id_ in modified:
            lines.append(f"    #{id_}  {inventory[id_]['sn']}")
            old_t = tracked(old_state[id_])
            new_t = tracked(inventory[id_])
            for key in TRACKED_FIELDS:
                if old_t[key] != new_t[key]:
                    lines.append(f"        {key}: {old_t[key]} -> {new_t[key]}")

    return "\n".join(lines)


def notify_discord(message):

    if not WEBHOOK_URL:
        return
    try:
        payload = {"content": f"**ts-styrelsen tracker**\n```\n{message}\n```"}
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"[!] discord notify failed: {e}")

# main
if __name__ == '__main__':

    inventory = {}
    old_state = {}

    if os.path.exists("state.json"):
        with open("state.json") as f:
            old_state = json.load(f)

    print(f"[*] loaded previous state: {len(old_state)} deployments")

    if FETCH:
        for app_id in range(1, 51):
            try:
                r = requests.get(URL, params={"app_id": app_id})
                data = r.json()
                    
                if data.get("code") == 200:

                    config = load_config(data["data"])
                    inventory[str(config["id"])] = config
                    print(f"#{config['id']:>3} {config['sn']:<14} {config['country']}")

                time.sleep(0.3)

            except (requests.RequestException, ValueError) as e:
                print(f"Error: {e}")

        print(f"\n[*] {len(inventory)} deployments found")

    else:
        inventory = old_state.copy()
        print(f"[*] using cached state ({len(inventory)} deployments), no fetch")

    old_ids = set(old_state.keys())
    new_ids = set(inventory.keys())

    added = sorted(new_ids - old_ids, key=int)
    removed = sorted(old_ids - new_ids, key=int)

    modified = []

    for id_ in sorted(old_ids & new_ids, key=int):

        if tracked(old_state[id_]) != tracked(inventory[id_]):
            modified.append(id_)

    report = build_report(added, removed, modified, inventory, old_state)

    if report is None:
        print("[=] no changes")

    else:
        print(report)
        notify_discord(report)

    if FETCH:

        with open("state.json", "w") as f:
            json.dump(inventory, f, indent=2, ensure_ascii=False)
        print("[*] state saved to state.json")

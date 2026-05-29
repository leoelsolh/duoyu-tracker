# duoyu-tracker

Polls the `/getApp?app_id=N` endpoint on a phishing kit deployment, decrypts the encrypted response, and dumps the operator's deployment inventory.

### What this is

This tool works against a specific family of phishing kits documented [here](https://leoelsolh.com). The kits run a multi-tenant backend where any deployment's hostname returns any other deployment's config when queried with the right `app_id`. The configuration response is encrypted, but the kit ships its own decryption keys inside each response, so the data can be recovered from outside without further compromise.

### Setup

```bash
git clone https://github.com/leoelsolh/duoyu-tracker.git
cd duoyu-tracker
pip install -r requirements.txt
```

### Quick start

```bash
python tracker-cron.py
```

The first run pulls every config the backend returns for `app_id` 1 to 50 and writes them all to `state.json`. On subsequent runs the script diffs against the saved state and reports added, removed, and modified deployments.

### Scripts

#### `decrypt_getapp.py`

The decryption module. Exposes `load_config(data)` for use as a library, or runs standalone against a saved response file.

```bash
# Decrypt a single saved response (expects ./getapp_response.json)
python decrypt_getapp.py
```

The `data` argument to `load_config` is the `data` field of a full `/getApp` response: the `{s, k, d}` object that carries the encrypted payload and the keys to undo it.

#### `tracker-cron.py`

The polling tracker. Iterates `app_id` 1..50 at the configured deployment, decrypts each response with `load_config`, and saves the inventory to `state.json`. On each run after the first, it diffs against the saved state and prints a report of what changed. Designed to run on a schedule.

#### `decrypt_all.py`

Batch decrypter. If you have a `configs/` directory full of saved raw `/getApp?app_id=N` responses (numbered `1.json`, `2.json`, and so on), this decrypts them all into `decrypted/` and prints a summary table. Useful when you want to separate the fetching step from the decryption step (for example, when curl-pulling responses offline and decrypting them later).

### Configuration

#### Target hostname

The default target is `transportstyrelsen-biljett.top`. To point at a different deployment of the same kit family, edit the `URL` constant at the top of `tracker-cron.py`:

```python
URL = "https://your-target-hostname/getApp"
```

#### `app_id` range

The default range is 1 to 50. That covers the operator's inventory at the time of writing with headroom. If you're tracking a different deployment or the inventory grows, adjust the `range()` call in `tracker-cron.py`.

#### Discord notifications

If you're using this as a cronjob to track an active phishing family, you'll probably want notifications when new deployments appear. The script reads a webhook URL from the `TRACKER_WEBHOOK_URL` environment variable and posts a formatted summary to that Discord channel whenever something changes:

```bash
export TRACKER_WEBHOOK_URL="https://discord.com/api/webhooks/..."
python tracker-cron.py
```

If you'd rather not use an env var, you can hardcode the URL directly into the script. Find this line near the top of `tracker-cron.py`:

```python
WEBHOOK_URL = os.environ.get("TRACKER_WEBHOOK_URL", "")
```

And replace it with:

```python
WEBHOOK_URL = "https://discord.com/api/webhooks/..."
```

With no webhook configured at all, the change report just prints to stdout. The script still works fine, you just don't get notified.

#### Running on cron

Twice daily is what produced the writeup's timeline. Example crontab line:

```
0 7,19 * * *  cd /path/to/duoyu-tracker && /usr/bin/python tracker-cron.py >> tracker.log 2>&1
```

Cron strips most environment variables by default, so if you're using `TRACKER_WEBHOOK_URL` you'll need to set it inside the cronjob itself or in a wrapper script. The wrapper approach looks like:

```bash
#!/usr/bin/env bash
export TRACKER_WEBHOOK_URL="https://discord.com/api/webhooks/..."
cd /path/to/duoyu-tracker
/usr/bin/python tracker-cron.py
```

Then point cron at the wrapper script.

### Disclaimer

For research and defensive use only. Do not interact with infrastructure you are not authorised to interact with. Querying a phishing kit's publicly exposed API for research purposes is generally accepted, but jurisdictions vary and you are responsible for your own use.

### Background

Full writeup of the operation this tool was built against: [link](https://leoelsolh.com).

### License

MIT
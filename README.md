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

The tracker has two modes: **fetch** (hit the live endpoint) and **cached** (work off the last saved state). By default it runs in cached mode and does *not* touch the network, you have to ask for a fetch explicitly.

```bash
# First run: pull live and build the initial state
python tracker.py -f
```

`-f` pulls every config the backend returns for `app_id` 1 to 50 and writes them all to `state.json`. On subsequent fetches the script diffs against the saved state and reports added, removed, and modified deployments.

```bash
# Re-read the saved state without fetching (no network)
python tracker.py
```

With no flags, the script loads `state.json`, reports it as cached, and exits without contacting the target.

### Flags

#### `-f` / `--fetch`

Fetch live from the configured deployment. Iterates `app_id` 1..50, decrypts each response, diffs against the saved state, prints a change report, and writes the new inventory back to `state.json`. Without this flag nothing is fetched and `state.json` is never overwritten.

#### `-c` / `--country CODE`

Filter the **cached** state by country code and print only matching deployments.

```bash
python tracker.py -c SE
```

This operates on whatever is already in `state.json` (run a `-f` first to populate it). Codes are matched case-insensitively.

### Scripts

#### `decrypt_getapp.py`

The decryption module. Exposes `load_config(data, verbose=False)` for use as a library, or runs standalone against a saved response file.

```bash
# Decrypt a single saved response (expects ./getapp_response.json)
python decrypt_getapp.py
```

The `data` argument to `load_config` is the `data` field of a full `/getApp` response: the `{s, k, d}` object that carries the encrypted payload and the keys to undo it. Pass `verbose=True` to print the recovered RSA key preview and the AES key in hex while decrypting.

#### `tracker.py`

The polling tracker. See **Quick start** and **Flags** above. Designed to run on a schedule with `-f`.

The change report only flags a deployment as *modified* when one of the tracked fields actually changes: `sn`, `country`, `pay_amount`, `created_at`, `updated_at`, `wss_server`.

#### `decrypt_all.py`

Batch decrypter. If you have a `configs/` directory full of saved raw `/getApp?app_id=N` responses (numbered `1.json`, `2.json`, and so on), this decrypts them all into `decrypted/` and prints a summary table. Useful when you want to separate the fetching step from the decryption step (for example, when curl-pulling responses offline and decrypting them later).

### Configuration

#### Target hostname

The default target is `transportstyrelsen-biljett.top`. To point at a different deployment of the same kit family, edit the `URL` constant at the top of `tracker.py`:

```python
URL = "https://your-target-hostname/getApp"
```

#### `app_id` range

The default range is 1 to 50. That covers the operator's inventory at the time of writing with headroom. If you're tracking a different deployment or the inventory grows, adjust the `range()` call in `tracker.py`.

#### Discord notifications

If you're using this as a cronjob to track an active phishing family, you'll probably want notifications when new deployments appear. The script reads a webhook URL from the `TRACKER_WEBHOOK_URL` environment variable and posts a formatted summary to that Discord channel whenever something changes:

```bash
export TRACKER_WEBHOOK_URL="https://discord.com/api/webhooks/..."
python tracker.py -f
```

If you'd rather not use an env var, you can hardcode the URL directly into the script. Find this line near the top of `tracker.py`:

```python
WEBHOOK_URL = os.environ.get("TRACKER_WEBHOOK_URL", "")
```

And replace it with:

```python
WEBHOOK_URL = "https://discord.com/api/webhooks/..."
```

The reason i chose to use an env var is for the fact im posting this to the public. I still don't recommend hard-coding your webhooks just because its bad practice from a security angle. But hey, you do you.

With no webhook configured at all, the change report just prints to stdout. The script still works fine, you just don't get notified.

#### Running on cron

Twice daily is what produced the writeup's timeline. Note the `-f`, cron runs need it or they'll just re-read cached state and never poll. Example crontab line:

```
0 7,19 * * *  cd /path/to/duoyu-tracker && /usr/bin/python tracker.py -f >> tracker.log 2>&1
```

Cron strips most environment variables by default, so if you're using `TRACKER_WEBHOOK_URL` you'll need to set it inside the cronjob itself or in a wrapper script. The wrapper approach looks like:

```bash
#!/usr/bin/env bash
export TRACKER_WEBHOOK_URL="https://discord.com/api/webhooks/..."
cd /path/to/duoyu-tracker
/usr/bin/python tracker.py -f
```

Then point cron at the wrapper script.

### Disclaimer

For research and defensive use only. Do not interact with infrastructure you are not authorised to interact with. Querying a phishing kit's publicly exposed API for research purposes is generally accepted, but jurisdictions vary and you are responsible for your own use.

### Background

Full writeup of the operation this tool was built against: [link](https://leoelsolh.com).

### License

MIT
# Exporting Reports to Remote Destinations

Secrover generates HTML reports into your local `output/` folder. You can keep them locally or **export them to any remote destination** (SFTP, WebDAV, SMB, S3, etc.) using **[rclone](https://rclone.org/)**.

## Step 1 — Create an rclone configuration

Create a local `rclone.conf` with your remote(s):

```ini
[prod-remote]
type = sftp
host = myserver.com
user = deploy
pass = mypassword

[nextcloud]
type = webdav
url = https://cloud.example.com/remote.php/webdav
user = alice
pass = secret
```

> See the [official rclone docs](https://rclone.org/docs/) for full examples for S3, Google Drive, SFTP, and others.
>
> Save the resulting `rclone.conf` in your project folder and mount it into the container at `/root/.config/rclone/rclone.conf`.

## Step 2 — Update `.env` for export

Add the following variables to your `.env`:

```env
EXPORT_ENABLED=true
RCLONE_REMOTES=prod-remote,nextcloud      # matches remote(s) in rclone.conf
RCLONE_PATH=/secrover-reports/            # remote path prefix for this project
```

## Step 3 — Run Secrover with rclone

Mount your `rclone.conf` in addition to the usual volumes:

```bash
docker run -it --rm \
  --env-file .env \
  -v $(PWD)/rclone.conf:/root/.config/rclone/rclone.conf:ro \
  secrover/secrover
```

* `:ro` → read-only mount for safety.
* Secrover automatically calls `rclone copy` at the end of each run if `EXPORT_ENABLED=true`.

## Step 4 — Optional: Timestamped Exports

You can configure Secrover to **create a new subfolder per run** for historical tracking:

```
RCLONE_PATH=/secrover-reports/$(date +%Y-%m-%d_%H-%M-%S)
```

* Secrover expands $(date +FORMAT) automatically to UTC timestamps.
* Each run will generate a folder like `/secrover-reports/2025-10-11_12-00-00/`
* Keeps all reports versioned and avoids overwriting previous exports.

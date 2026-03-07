# Showrunner Disaster Recovery Guide

**Prepared for**: Data loss, corruption, or accidental deletion emergencies

**Philosophy**: Your story is backed by git and local YAML files. This guide helps you recover from almost any failure.

---

## Quick Recovery Matrix

| Problem | Cause | Solution | Time |
|---------|-------|----------|------|
| Missing YAML file | Accidental delete | `showrunner trash restore <id>` | 1 min |
| Database corrupted | SQLite crash | `showrunner index rebuild` | 2 min |
| Character overwrit | Save conflict | `git checkout characters/zara.yaml` | 1 min |
| Event log lost | DB deletion | Rebuild from YAML + git | 5 min |
| All YAML gone | Folder delete | Restore from backup zip | 10 min |
| Git corrupted | Merge conflict | Restore from backup, redo changes | 30 min |

---

## Scenario 1: Accidentally Deleted a YAML File

**Symptoms**: Character, location, or scene file is gone but wasn't supposed to be.

**Recovery**:

```bash
# Step 1: Check the trash
ls .showrunner/trash/

# Step 2: Find the file you deleted
# Files are named: original_name-{timestamp}.yaml
ls .showrunner/trash/character*/zara*

# Step 3: Restore it
showrunner trash restore zara

# Step 4: Verify it's back
ls characters/zara.yaml
```

**If you don't remember the name**:

```bash
# Browse all trashed files with their timestamps
find .showrunner/trash -name "*.yaml" -exec ls -lh {} \;

# Search by creation time
find .showrunner/trash -mtime -1  # Modified in last day
```

**If trash is also empty**: Go to Scenario 6 (Restore from Backup).

---

## Scenario 2: SQLite Database Corrupted

**Symptoms**:
- Web UI crashes on load
- Search returns errors
- "database disk image is malformed"

**Recovery**:

```bash
# Step 1: Rebuild the index from YAML files
showrunner index rebuild

# This will:
#   - Detect all YAML files in project
#   - Re-parse them
#   - Recreate SQLite tables
#   - Rebuild search index (ChromaDB)

# Step 2: Verify the rebuild
showrunner status

# Step 3: Test the web UI
showrunner server start --reload
# Open http://localhost:3000 — should work now

# If it still fails:
# Step 4: Hard reset SQLite
rm event_log.db
showrunner index rebuild
```

**What's being recovered**:
- Character/location/scene index (SQLiteIndexer)
- Event sourcing log (TimeMachine)
- Search index (ChromaDB embeddings)
- Sync metadata (FileWatcher state)

All are **rebuilt from your YAML files** — your data is safe.

---

## Scenario 3: Character Overwritten by Accident

**Symptoms**: "I modified the character but saved the wrong version."

**Recovery**:

```bash
# Step 1: See the diff (what changed)
git diff characters/zara.yaml

# Step 2: Revert to last committed version
git checkout characters/zara.yaml

# Step 3: If you want to compare versions
git log --oneline characters/zara.yaml | head -10
git show HEAD~1:characters/zara.yaml  # See previous version

# Step 4: If you want to cherry-pick changes
# Use your editor to manually merge, or:
git mergetool characters/zara.yaml
```

**If you already committed** the wrong version:

```bash
# See the commit that broke it
git log --oneline characters/zara.yaml | head

# Revert that commit
git revert <commit-hash>

# Your git history now shows the revert (safer than reset)
```

---

## Scenario 4: Event Log Database Lost

**Symptoms**:
- Undo/redo not working
- Timeline shows no events
- "event_log.db" is missing or corrupted

**Recovery**:

```bash
# Step 1: Event log is reconstructible from git history
# Each scene/character save creates a git commit with the changes
# Showrunner can rebuild the event log from these commits

showrunner rebuild-events

# This will:
#   - Walk git history in commit order
#   - Reconstruct each edit as an event
#   - Recreate event_log.db
#   - Restore undo/redo functionality

# Step 2: Verify
showrunner timeline show
# Should show all your edits as events

# Step 3: Test undo/redo
showrunner timeline undo
git diff  # Should show one commit's changes reverted
```

---

## Scenario 5: Multiple YAML Files Corrupted

**Symptoms**:
- Multiple YAML files have garbage data
- XML/JSON mixed in
- Files are partially overwritten

**Recovery**:

```bash
# Step 1: See what changed recently
git status
git log --oneline -10

# Step 2: Revert all corrupted files to last good state
git checkout HEAD -- characters/ world/ containers/

# Step 3: Or, if corruption was committed:
git revert <bad-commit-hash>

# Step 4: If you don't know which files are bad:
git fsck --full  # Check git repository integrity

# If git says files are fine:
# YAML parser might be strict. Try:
showrunner check validate  # Validates all YAML syntax
```

---

## Scenario 6: Restore from Backup

**Symptoms**: "Major data loss. Need to restore from backup file."

**Recovery**:

```bash
# Step 1: Find your backup
ls *.zip
ls story-backup-*.zip

# Step 2: Create a new directory for safety
mkdir story-recovery
cd story-recovery

# Step 3: Extract the backup
unzip ../story-backup-2026-03-07.zip

# Step 4: Verify the contents
ls characters/ world/ fragment/
cat CLAUDE.md

# Step 5: Restore to your project
# Option A: Copy files back (careful of overwriting)
cp -i characters/* ../my-project/characters/
cp -i fragment/* ../my-project/fragment/

# Option B: Use backup as new project root
# Rename it to your project
cd ..
mv my-project my-project-broken
mv story-recovery my-project
cd my-project

# Step 6: Restore git history (if backup included git bundle)
git remote add origin file:///path/to/bundle.git
git fetch origin
git merge origin/main  # or whatever branch

# Step 7: Commit the recovery
git add -A
git commit -m "Recovered from backup-2026-03-07.zip"
```

---

## Scenario 7: Git Repository Corrupted

**Symptoms**:
- `.git/` directory is corrupted
- "fatal: bad object" errors
- `git log` doesn't work

**Recovery**:

```bash
# Step 1: Try git's built-in repair
git fsck --full

# Step 2: If that doesn't work, try garbage collection
git gc --aggressive

# Step 3: If git is beyond repair:
# Your YAML files are still safe
# Create a fresh git repo

mv .git .git.broken  # Backup the broken one
git init
git add -A
git commit -m "Recovered from corrupted git state"

# You've now created a new git history starting from your current YAML state
# You've lost the old commit history, but kept all your files
```

**Note**: If you had the git bundle backup, restore from that instead:

```bash
git clone bundle.git
# This fully restores the commit history
```

---

## Scenario 8: Web UI Crashes on Startup

**Symptoms**: Web UI won't load, shows 500 errors or crashes during sync.

**Recovery**:

```bash
# Step 1: Check the logs
tail -50 ~/.showrunner/logs/showrunner.log

# Step 2: Common issue — FileWatcher out of sync
# Force a complete resync
showrunner index rebuild

# Step 3: Restart the server
showrunner server stop
showrunner server start

# Step 4: If that doesn't work — clear caches
rm -rf .showrunner/cache/
rm -rf src/web/.next/
showrunner index rebuild
showrunner server start

# Step 5: Check database
python3 -c "import sqlite3; conn = sqlite3.connect('.showrunner/event_log.db'); conn.execute('PRAGMA integrity_check')"
# Should print "ok"
```

---

## Scenario 9: Cloud Sync Conflicts

**Symptoms**: Files are conflicted between local and Google Drive versions.

**Recovery**:

```bash
# Step 1: Stop the sync
showrunner sync stop

# Step 2: Check what's conflicting
git status
ls **/*conflict*

# Step 3: Resolve using git
# Option A: Keep local version
git checkout --ours <file>
git add <file>

# Option B: Keep remote version
git checkout --theirs <file>
git add <file>

# Option C: Manual merge
# Edit the file, choose which version to keep
git add <file>

# Step 4: Commit the resolution
git commit -m "Resolved sync conflict"

# Step 5: Restart sync
showrunner sync start
```

---

## Scenario 10: Lost Entire Project Directory

**Symptoms**: Whole project folder was deleted or corrupted.

**Recovery**:

```bash
# Step 1: Restore from backup
unzip story-backup-2026-03-07.zip
mv Showrunner my-project  # Rename if needed

# Step 2: Restore git history
cd my-project
git clone file:///path/to/story.bundle my-repo-restored
cd my-repo-restored

# Step 3: You now have:
#   - All YAML files from the backup
#   - Full git commit history from the bundle
#   - Complete recovery

# Step 4: Continue working
showrunner status
showrunner server start
```

---

## Prevention Strategy

### Automated Backups

Run this cron job to create daily backups:

```bash
# Save to ~/.showrunner/cron_backup.sh
#!/bin/bash
cd ~/Documents/Showrunner
showrunner backup --output backups/story-backup-$(date +%Y-%m-%d).zip
# Keep only last 30 days of backups
find backups/ -name "*.zip" -mtime +30 -delete
```

Then add to crontab:

```bash
crontab -e
# Add this line:
0 2 * * * ~/.showrunner/cron_backup.sh  # Run at 2 AM daily
```

### Git Workflow Best Practices

```bash
# Commit regularly after important changes
showrunner git stage-story
showrunner git commit-message

# Push to remote weekly
git push origin main

# Create backup before risky operations
showrunner backup
git branch experiment  # Work on experiment branch
# Test changes...
git checkout main      # Back to main if experiment was bad
```

### Monitoring

```bash
# Weekly: Check that backups are being created
ls -lh story-backup-*.zip | tail -5

# Monthly: Test a recovery
# Extract a backup to a temp directory and verify it works

# Quarterly: Full backup to external drive
cp story-backup-*.zip /Volumes/External\ Drive/showrunner-backups/
```

---

## When to Call for Help

If recovery steps don't work:

1. **Check the logs**: `showrunner debug logs` (includes full stack traces)
2. **Search the docs**: [docs/IDE_GUIDE.md](IDE_GUIDE.md) has troubleshooting
3. **Issue on GitHub**: Report with logs attached
4. **Manual recovery**: Worst case, extract YAML files from `.git/objects/` using `git cat-file`

---

## Your Data Safety Summary

✅ **YAML files**: Tracked by git, backed up to `.showrunner/trash/`
✅ **Git history**: Can be exported as bundle or backed up
✅ **Databases**: Rebuilt from YAML + git
✅ **Backups**: Zip exports capture complete state

**Bottom line**: You almost never lose your story. Worst case: restore from backup and redo ~1 hour of changes.

---

## Key Files to Back Up Regularly

```bash
# Daily
story-backup-*.zip

# Weekly
.git/                    # Git repository (entire folder)
characters/
world/
fragment/
containers/

# Monthly
event_log.db             # For undo/redo history
.showrunner/decisions.yaml   # Author decisions
.showrunner/sessions/    # Session logs
```

**Recommended**: Use cloud storage (Google Drive, Dropbox) or external drive for monthly backups.


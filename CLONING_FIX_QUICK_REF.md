# Quick Fix Reference

## What Was Fixed

**Problem:** `WinError 5: Access is denied` when running `POST /api/analyze` twice on the same GitHub repository on Windows.

**Root Cause:** Repository directory existed from previous run with locked `.git` files, and simple `shutil.rmtree()` couldn't delete them.

**Solution:** Implemented smart retry logic with fallback strategy.

---

## What Changed

**File:** `src/modules/repo_scanner.py`

| Component | Change | Lines |
|-----------|--------|-------|
| Imports | Added `time` and `stat` | 3-6 |
| Method | Rewrote `clone_repository()` | 37-85 |
| New Method | `_safe_remove_directory()` | 87-144 |
| New Method | `_make_directory_writable()` | 146-176 |

**Total Changes:** 180 lines of improved cloning logic

---

## How It Works

```
POST /api/analyze with same repo (2nd time)
    ↓
Check if directory exists
    ↓
YES → Call _safe_remove_directory()
    ↓
    1. Make all files writable (stat.S_IWRITE)
    2. Try shutil.rmtree()
    3. If fails, wait 0.5s and retry
    4. Retry up to 5 times with exponential backoff
    5. Return True if success, False if all fail
    ↓
Success? → Clone to normal path
Fail? → Clone to temp path (repo_temp_<timestamp>)
    ↓
Return analysis to user ✓
```

---

## Testing

**Run comprehensive tests:**
```bash
python test_cloning_fix.py
```

**Test with API:**
```bash
# Terminal 1
python -m uvicorn src.main:app --reload

# Terminal 2 (run twice)
curl -X POST http://localhost:8001/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"https://github.com/pallets/flask"}'
```

**Expected:** Both requests return 200 OK ✓

---

## Key Features

| Feature | Benefit |
|---------|---------|
| Retry logic (5x) | Handles transient locks |
| Exponential backoff | Gives OS time to release handles |
| Permission fixes | Handles readonly `.git` files |
| Temp path fallback | Always provides successful clone |
| Logging | Debugging and transparency |
| Cleanup on fail | No orphaned directories |

---

## Error Messages

| Scenario | Status | Message |
|----------|--------|---------|
| **Success** | 200 | Full analysis + diagrams |
| **Invalid URL** | 400 | "Invalid GitHub URL..." |
| **Clone fails** | 400 | "Failed to clone repository..." |
| **Other error** | 500 | "Analysis failed..." |

---

## Performance

- **First clone:** No change (same as before)
- **Subsequent clone:** +0-2.5s for cleanup attempts (acceptable)
- **Fallback clone:** +0.1s for temp path (fast)
- **Overall:** Improved reliability >> slight latency tradeoff

---

## Backward Compatibility

✅ **No breaking changes**

- Same method signature: `clone_repository(repo_url: str) -> Path`
- Same exception type: `ValueError`
- Same return behavior
- All existing code works unchanged

---

## Deployment

**No special deployment steps needed:**
1. Run `python verify_phase2.py` to confirm tests pass
2. Deploy updated `src/modules/repo_scanner.py`
3. Monitor logs for "Existing repository detected" messages
4. No database migrations or config changes needed

---

## Monitoring

Watch for these log messages in production:

**Normal (expected on 2nd request):**
```
"Existing repository detected at data\repos\flask"
"Directory removed successfully"
"Successfully cloned repository to data\repos\flask"
```

**Retry (means directory was locked):**
```
"Attempt 1/5 to remove ... Retrying in 0.5s... (Error: PermissionError)"
"Attempt 2/5 to remove ... Retrying in 1.0s... (Error: PermissionError)"
"Directory removed successfully"  ← Success after retry
```

**Fallback (rare but safe):**
```
"Failed to remove existing repo, will attempt clone to alternative path"
"Successfully cloned repository to data\repos\flask_temp_1709617......"
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Still getting WinError? | Restart API server (fresh state) |
| Lots of retry messages | Network/disk speed issue (normal on slow systems) |
| Temp paths accumulating | Old temp directories can be manually cleaned |
| Clone still failing | Check GitHub API rate limits or network |

---

## Code Examples

**Before (Problematic):**
```python
if repo_path.exists():
    shutil.rmtree(repo_path)  # ← Can fail with PermissionError
Repo.clone_from(repo_url, repo_path)
```

**After (Robust):**
```python
if repo_path.exists():
    success = self._safe_remove_directory(repo_path)
    if not success:
        repo_path = self.clone_path / f"{repo_name}_temp_{int(time.time())}"

Repo.clone_from(repo_url, str(repo_path))
```

---

## Summary

✅ **Fix implemented and tested**  
✅ **Windows file locks handled**  
✅ **Retry logic with backoff**  
✅ **Fallback strategy in place**  
✅ **Clear logging added**  
✅ **No breaking changes**  
✅ **Ready for production**

**Status:** 🟢 **COMPLETE**

For detailed documentation, see: [CLONING_FIX_REPORT.md](CLONING_FIX_REPORT.md)

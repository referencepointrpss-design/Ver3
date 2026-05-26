# Survey Equipment Manager UI / Navigation Fixes

This package includes:

- Compact top headers to remove excessive empty area.
- ScreenManager `NoTransition()` to stop left/right slide animation.
- Android hardware back-button handling:
  - Detail/profile screen returns to list.
  - Add/log/list screens return to main menu.
  - Main menu consumes the back button so the app does not close by accident.
- Existing database, reports, export, delete, and calendar logic preserved.

Rebuild with:

```bash
source ~/buildozer_env/bin/activate
buildozer -v android debug
```

# Bug Fix Summary for EZpanso

## Issues Fixed

### Bug 1: TSM Error on Multi-Row Deletion

**Problem**: When selecting multiple entries and deleting them, terminal showed error:

```
Python [] TSMSendMessageToUIServer: CFMessagePortSendRequest FAILED(-1) to send to port com.apple.tsm.uiserver
```

**Root Cause**: After deletion, the table selection model still referenced old row indices that no longer existed after the data changes and table repopulation. This caused PyQt's Table Selection Model (TSM) to fail when trying to access non-existent rows.

**Additional Issue**: TSM errors also occurred during save confirmation dialogs when table selections were active, due to macOS Qt messaging conflicts.

**Solution**:

1. Added `self.table.clearSelection()` before refreshing the table in `_delete_snippets_by_triggers()`
2. Added `self.table.clearSelection()` before showing save confirmation dialogs in `_save_all_with_confirmation()` and `closeEvent()`

**Files Changed**:

- `main.py` lines 559-562: Added table selection clearing before refresh in deletion
- `main.py` lines 720-722: Added table selection clearing before save confirmation dialog  
- `main.py` lines 1049-1051: Added table selection clearing before close confirmation dialog

### Bug 2: Table Mismatch After In-Place Editing

**Problem**: After in-pla3ce editing a cell, the table would refresh/reorganize and mismatches between trigger and replace values were found due to rows moving to different positions.

**Root Cause**: After in-place editing, `_on_item_changed()` called `_mark_modified_and_refresh()` which completely rebuilt and reordered the table. This caused the edited row to potentially move to a different position, breaking the visual connection between what the user edited and the result.

**Solution**:

1. Modified `_mark_modified_and_refresh()` to accept an optional `skip_table_refresh` parameter
2. Updated `_on_item_changed()` to call `_mark_modified_and_refresh(skip_table_refresh=True)` to avoid table repopulation during in-place editing

**Files Changed**:

- `main.py` lines 678-687: Modified `_mark_modified_and_refresh()` to accept skip parameter
- `main.py` lines 649-653: Updated `_on_item_changed()` to skip table refresh

### Bug 3: Incorrect Trigger-Replace Mapping in In-Place Editing

**Problem**: In-place editing was updating the wrong trigger-replace pairs. Changes to a replace field would be saved to a completely different trigger, causing data corruption.

**Root Cause**: Critical data structure mismatch in table population:

1. `_populate_table()` stored `self.current_matches = matches.copy()` (unsorted original order)
2. But displayed `sorted_matches` in the table (sorted by complexity and trigger alphabetically)  
3. `_on_item_changed()` used table row index to access `self.current_matches[row]`
4. This created a mismatch where `self.current_matches[row]` didn't correspond to the actual table row after sorting

**Solution**:

1. Fixed `_populate_table()` to store sorted matches: `self.current_matches = sorted_matches.copy()`
2. Simplified `_on_item_changed()` to directly use row index since it now corresponds correctly
3. Added debug logging and better error handling

**Files Changed**:

- `main.py` lines 413-416: Fixed current_matches to store sorted data
- `main.py` lines 604-645: Simplified and fixed _on_item_changed() method

## Technical Details

### Code Changes

#### 1. Enhanced `_mark_modified_and_refresh()` method

```python
def _mark_modified_and_refresh(self, skip_table_refresh: bool = False):
    """Mark the file as modified and refresh the UI."""
    if self.active_file_path:
        self.modified_files.add(self.active_file_path)
    self.is_modified = True
    self._update_title()
    self._update_save_button_state()
    if self.active_file_path and not skip_table_refresh:
        matches = self.files_data.get(self.active_file_path, [])
        self._populate_table(matches)
```

#### 2. Updated deletion method to clear selection

```python
# In _delete_snippets_by_triggers()
self.files_data[self.active_file_path] = remaining_matches

# Clear table selection before refreshing to prevent TSM errors
self.table.clearSelection()

# Mark as modified and refresh
self._mark_modified_and_refresh()
```

#### 3. Modified in-place editing to skip table refresh

```python
# In _on_item_changed()
if self._validate_and_update_field(item, target_match, target_index, field_name, new_value, original_trigger):
    # Also update the current_matches to keep it in sync
    current_match[field_name] = self._format_yaml_value(new_value)
    # Mark as modified but skip table refresh to avoid disrupting in-place editing
    self._mark_modified_and_refresh(skip_table_refresh=True)
```

#### 4. Fixed trigger-replace mapping in in-place editing

```python
# In _populate_table()
self.current_matches = sorted_matches.copy()  # Store sorted matches

# In _on_item_changed()
# Directly use row index as it now corresponds to the actual table row
```

## Testing

### Verification Steps

1. **Bug 1 Test**: Created test that simulates multi-row deletion and verifies no TSM errors occur
2. **Bug 2 Test**: Created test that verifies in-place editing doesn't cause table reorganization
3. **Bug 3 Test**: Created test that verifies trigger-replace mapping is correct after in-place editing
4. **Regression Test**: Ran full test suite (38 tests) to ensure no existing functionality was broken

### Test Results

- ✅ All 38 existing tests pass
- ✅ Bug fix verification tests pass
- ✅ No regression issues detected

## Impact

### User Experience Improvements

- **Smoother Deletion**: Multi-row deletion now works without terminal errors
- **Stable In-Place Editing**: Users can edit cells without losing track of their changes due to table reorganization
- **Correct Data Mapping**: Trigger-replace mappings remain consistent and correct, preventing data corruption
- **Maintained Functionality**: All existing features continue to work as expected

### Code Quality

- **Backward Compatible**: Changes are additive and don't break existing API
- **Minimal Impact**: Fixes are targeted and don't affect unrelated functionality
- **Follows Patterns**: Solutions use existing code patterns and maintain consistency

## Files Modified

- `/Users/longman/Documents/myCode/EZpanso/main.py` (3 targeted changes)
- `/Users/longman/Documents/myCode/EZpanso/tests/test_bug_fixes.py` (new test file)

## Summary

All bugs were successfully fixed with minimal, targeted changes that address the root causes while maintaining full backward compatibility and not breaking any existing functionality.

Mouse action still feels bad. Please add keyboard shortcuts to make it up.

Where does the code handle keyboard shortcuts?
Should we refactor the existing keyboard shortcuts functions and start a new module for that?



Up/ Down: Browse thru row. (But the delay of holding down the key until it keeps going is too long)
Shift Up/ Down: Select multiple
Return: Edit existing snippet (I think this function is missing.)
Esc: Cancel selection

Fairly conventional shortcuts. Feel free to suggest more
 


Changes are automatically saved.


New Function 1:
Add Category: Create a new yml file under match

Work on shortcuts:
Command+Shift+N for "New Category"
Command+N for "Add" (not "New Snippet")

New functions 2:
Besides using "Add" and shortcut to trigger the dialog box, the user should be allowed to type to the table directly (eg. always prepare an empty row at the bottom, preferably freezed to the bottom)

:dagger



Remove 1 snippet(s) from base?
This is permanent upon saving.
:

Show custom Dialog box for delete. No logo. Text to:
Delete {}?
No Yes

Refresh the yml list upon start and refresh.
I don't see the newly created ymls yet.
In the end of the yml list, create one option "Add new Category..." and then trigger the "Create New Espanso Category File" dialogue box.

Change to "Create New Espanso Category File" box.
title: Add new category
"New Category Name (e.g., 'my_work_snippets'):"  into "Title:"
add a description: "path/to/{}.yml will be created"
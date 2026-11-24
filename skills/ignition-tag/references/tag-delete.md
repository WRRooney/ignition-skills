# Deleting tags, folders, instances, and types

```bash
ign tag delete --provider default --path Tanks/T01 --dry-run     # prints the directory
ign tag delete --provider default --path Tanks/T01               # tag-definition dir + scan
ign tag delete --provider default --path Equipment --kind type   # tag-type-definition dir + scan
ign tag delete --provider default --path Tanks --name T01        # one tag in the folder, siblings kept
ign tag delete --provider default --path Tanks --name 'T0*' --name Spare --dry-run   # lists matches
```

Without `--name` it removes the whole directory (`tags.json` and/or `udts.json` plus `unary-resource.json`); the gateway drops the tags on the scan. With `--name` it removes only the matching top-level entries of that folder's data files (`*`, `?`, `[...]` wildcards, case-insensitive, repeatable) and leaves every sibling untouched; a file left empty is removed and the folder stays with `"files": []`, the gateway's own shape for a folder that only holds subfolders. Subfolders are directories, not entries: give their path without `--name`. No match exits 1 and writes nothing. There is no REST delete for tags, so this is the only sanctioned remover. Confirm the path with the user before running without `--dry-run`.

Python script to migrate playlists and user ratings from a source navidrome server to a target navidrome server.

The migration script assumes all the music files in source exist in target with the same ids. The script is simply creating the metadata playlist info and moving the songs in to the playlists through use of the subsonic APIs.

# Run Instructions

Define your source and target server urls at the top of `nav_migration.py`

Run from a python 3 environment with:

`
python src/navmigration/nav_migration.py <source_username> <source_password> <target_username> <target_password>
`
from app.dropbox_sync import DropBox

"""
Download videos
Rename
Split
Upload to channels
"""

if __name__ == "__main__":
    dbx = DropBox()
    dbx.list_dir()
    a = 44

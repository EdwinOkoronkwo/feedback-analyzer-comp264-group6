import os
import shutil

def archive_files():
    # 1. Define the Archive Directory
    archive_dir = "archive"
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        print(f"📁 Created {archive_dir} directory.")

    # 2. List of files to move (The "Bloat")
    # Mapping: "current_path": "archive_subfolder"
    to_archive = {
        "web/app_aws.py": "web",
        "web/app_local.py": "web",
        "web/components/local_analyzer_ui.py": "web/components",
        "web/components/local_history_ui.py": "web/components",
        "web/components/results_viewer.py": "web/components",
        "web/components/results_ui.py": "web/components", # Redundant if using integrated history
    }

    print("🚀 Archiving redundant Streamlit files...")

    for file_path, sub_folder in to_archive.items():
        if os.path.exists(file_path):
            # Ensure target subfolder exists in archive
            target_path = os.path.join(archive_dir, sub_folder)
            if not os.path.exists(target_path):
                os.makedirs(target_path)
            
            # Move the file
            shutil.move(file_path, os.path.join(target_path, os.path.basename(file_path)))
            print(f"✅ Moved: {file_path} -> {target_path}/")
        else:
            print(f"ℹ️ Skipping (not found): {file_path}")

    print("\n✨ Cleanup Complete! Your 'web/' folder is now unified.")
    print("💡 Kept 'implementations/local/api/local_api.py' for your Lambda simulation.")

if __name__ == "__main__":
    archive_files()
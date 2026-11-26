"""Beginner-friendly terminal menu for Android Termux."""
from pathlib import Path
from organizer import OrganizerError, organize, undo_last
from reports import write_report

def ask_folder(prompt: str, must_exist: bool = False) -> Path:
    while True:
        entered = input(prompt).strip()
        if not entered:
            print("Folder path khali nahi ho sakta.")
            continue
        path = Path(entered).expanduser()
        if must_exist and not path.is_dir():
            print("Yeh folder nahi mila. Path dobara check karein.")
            continue
        return path

def main() -> None:
    source = destination = None
    print("\n=== Smart File Organizer ===")
    print("Termux shared storage path aksar: /storage/emulated/0")
    while True:
        print("\n1. Source aur destination folder set karein")
        print("2. Preview (default, koi file move nahi hogi)")
        print("3. Files organize karein")
        print("4. Pichhla operation undo karein")
        print("5. Exit")
        choice = input("Apna option chunein (1-5): ").strip()
        try:
            if choice == "1":
                source = ask_folder("Source folder path: ", must_exist=True)
                destination = ask_folder("Destination folder path (banaya ja sakta hai): ")
                print("Folder paths save ho gaye.")
            elif choice in {"2", "3"}:
                if source is None or destination is None:
                    print("Pehle option 1 se dono folders set karein.")
                    continue
                if choice == "2":
                    result = organize(source, destination)
                else:
                    preview = organize(source, destination)
                    if not preview["plan"]:
                        print("Source folder ke top level par koi file nahi mili.")
                        continue
                    print("Move hone wali files:")
                    for row in preview["plan"]:
                        print(f"[{row['category']}] {row['source']} -> {row['destination']}")
                    answer = input("Kya in files ko move karna hai? (yes/no): ").strip().lower()
                    if answer not in {"yes", "y", "haan", "हां"}:
                        print("Cancel kar diya. Koi file move nahi hui.")
                        continue
                    result = organize(source, destination, dry_run=False)
                print(f"Preview mein {len(result['plan'])} file(s) hain.")
                if result.get("moved"):
                    print(f"{len(result['moved'])} file(s) move hui.")
                for issue in result.get("errors", []):
                    print("Issue:", issue)
                print("TXT report save hui:", write_report(result, destination))
            elif choice == "4":
                if destination is None:
                    destination = ask_folder("Operation ka destination folder path: ")
                result = undo_last(destination)
                print(f"{len(result['restored'])} file(s) restore hui.")
                for issue in result["errors"]:
                    print("Issue:", issue)
            elif choice == "5":
                print("Dhanyavaad!")
                break
            else:
                print("1 se 5 ke beech option chunein.")
        except OrganizerError as exc:
            print("Kaam nahi ho saka:", exc)
        except PermissionError as exc:
            print("Permission nahi mili. Termux ko storage access dein, phir koshish karein:", exc)
        except OSError as exc:
            print("File system error:", exc)

if __name__ == "__main__":
    main()

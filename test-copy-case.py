# Copy an Eclipse case to a new place.

# Import libraries.
import ecl_tokenizer as et
import os

# Read source case.
case = et.EclCase(r"C:\GitHub\opm-tests\norne\NORNE_ATW2013.DATA")

top_dir = case.get_top_dir()
new_dir = r"C:\GitHub\norne"

print("INFO: Top Directory is: ", top_dir)

# Copy files one by one.
for file in case.processed_files:
    pfile_rel_path = os.path.relpath(file, top_dir)
    new_file_path  = os.path.join(new_dir, pfile_rel_path)
    new_file_dir   = os.path.dirname(new_file_path)
    print("INFO: Dest file name:", new_file_path)
    if not os.path.exists(new_file_dir):
        _ = os.makedirs(new_file_dir, exist_ok=True)
        print("INFO: Making directory:", new_file_dir)
    else:
        print("INFO: Ok, dest directory exists", new_file_dir)
    # Collect keywords of given file.
    kwds = [i for i in case.keywords if i.parent == file]
    #print(len(kwds))
    with open(new_file_path, "w+") as f:
        for kwd in kwds:
            _ = f.write(kwd.name + "\n")
            _ = f.writelines([i + "\n" for i in kwd.value])
            _ = f.write("\n")

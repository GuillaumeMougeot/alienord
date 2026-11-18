import os

def compare_filenames(folder1, folder2):
    files_folder1 = {os.path.splitext(file)[0] for file in os.listdir(folder1)}
    files_folder2 = {os.path.splitext(file)[0] for file in os.listdir(folder2)}
    
    # find non-matching filenames
    non_matching_folder1 = files_folder1 - files_folder2
    non_matching_folder2 = files_folder2 - files_folder1
    
    # print non-matching filenames from folder1
    if non_matching_folder1:
        print("Files in folder1 without a match in folder2:")
        for file in non_matching_folder1:
            print(file)
    else:
        print("All files in folder1 have a match in folder2.")
    
    # print non-matching filenames from folder2
    if non_matching_folder2:
        print("\nFiles in folder2 without a match in folder1:")
        for file in non_matching_folder2:
            print(file)
    else:
        print("\nAll files in folder2 have a match in folder1.")

if __name__ == "__main__":
    folder1 = '/Users/aleksandra/Desktop/biodiversity/xnx2' 
    folder2 = '/Users/aleksandra/Desktop/xnx2'  
    
    compare_filenames(folder1, folder2)

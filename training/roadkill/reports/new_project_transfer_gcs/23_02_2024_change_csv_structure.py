import os
import pandas as pd

csv_path = '/Users/aleksandra/Desktop/Roadkill_project/vd-biodiversity/training/roadkill/reports/checked_imgs.csv'
txt_path = '/Users/aleksandra/Desktop/Roadkill_project/vd-biodiversity/training/roadkill/reports/filename_mapping.txt'

df_csv = pd.read_csv(csv_path)
df_txt = pd.read_table(txt_path, header=None, delimiter=",", names=["json_filename", "image_filename"])

df_txt["file_name"] = df_txt["image_filename"].apply(lambda x: x.replace(".json", ".jpg"))

csv_dict = df_csv.set_index('image_name').to_dict(orient='index')

new_data = []
for idx, row in df_txt.iterrows():
    base_name = os.path.splitext(row["json_filename"])[0]
    
    animal = csv_dict.get(base_name + ".jpg", {}).get("animal", False)
    unblurred = csv_dict.get(base_name + ".jpg", {}).get("unblurred", False)

    new_data.append({
        "number": idx,
        "file_name": row["file_name"],
        "animal": animal,
        "unblurred licence plate": unblurred
    })

df_new = pd.DataFrame(new_data)

output_path = '/Users/aleksandra/Desktop/Roadkill_project/vd-biodiversity/training/roadkill/reports/report_roadkill.csv'
df_new.to_csv(output_path, index=False)

print(f"New CSV file has been saved to {output_path}")

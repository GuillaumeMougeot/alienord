import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import json

# load paths from config file
def load_config(config_path):
    with open(config_path, 'r') as file:
        return json.load(file)


config = load_config('detections_statistics/config.yml')
file_path = config['animal_confidence_file']
histogram_path = config['histogram_path']


# parsing the text file
parsed_data = []

with open(file_path, 'r') as f:
    for line in f:
        elements = line.split(',')
        if len(elements) != 4:
            print(f"Unexpected format: {line}")
            continue
        
        try:
            row_data = {
                'Filename': elements[0].split(':')[1].strip(),
                'GPS Timestamp': elements[1].split(':')[1].strip(),
                'Confidence': float(elements[2].split(':')[1].strip()),
                'Animal': elements[3].split(':')[1].strip().lower() == 'true'
            }
            parsed_data.append(row_data)
        except IndexError:
            print(f"Error parsing: {line}")

data = pd.DataFrame(parsed_data)

# calculate percentages for Confidence < 0.5
true_count = sum(data[data['Animal']]['Confidence'] < 0.5)
false_count = sum(data[~data['Animal']]['Confidence'] < 0.5)

true_percentage = (true_count / len(data[data['Animal']])) * 100
false_percentage = (false_count / len(data[~data['Animal']])) * 100

# plotting histograms
fig, axes = plt.subplots(2, 1, figsize=(10, 10))

# histogram for Animal=True
sns.histplot(data[data['Animal']]['Confidence'], kde=False, bins=30, ax=axes[0], color='blue')
axes[0].set_title(f'True positives - {true_percentage:.2f}% with Confidence < 0.5')
axes[0].set_xlabel('Confidence')
axes[0].set_ylabel('Count')

# histogram for Animal=False
sns.histplot(data[~data['Animal']]['Confidence'], kde=False, bins=30, ax=axes[1], color='lightblue')
axes[1].set_title(f'False positives - {false_percentage:.2f}% with Confidence < 0.5')
axes[1].set_xlabel('Confidence')
axes[1].set_ylabel('Count')

plt.tight_layout()
fig.savefig(histogram_path, format='jpg')
plt.show()

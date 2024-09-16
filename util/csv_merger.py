import csv
from collections import defaultdict

def load_csv(filename):
    data = []
    with open(filename, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file, dialect='excel')
        headers = next(reader)  # Read the header row
        for row in reader:
            # Handle potential unescaped commas in the tag column
            tag = row[0]
            if len(row) > 4:  # If we have more than 4 columns, we might have unescaped commas
                # Combine extra columns into the tag, up to the category column
                extra_columns = []
                for i in range(1, len(row)):
                    if row[i].isdigit():  # Assume we've reached the 'count' column
                        break
                    extra_columns.append(row[i])
                tag = tag + ',' + ','.join(extra_columns)
                row = [tag] + row[i:]
            
            # Create a dictionary for the row
            row_dict = dict(zip(headers, row))
            data.append(row_dict)
    return data

def merge_csvs(file1, file2):
    # Load both CSV files
    data1 = load_csv(file1)
    data2 = load_csv(file2)

    # Create a set of all tags from file2
    tags_in_file2 = set(row['tag'] for row in data2)

    # Merge data
    merged_data = defaultdict(lambda: {'category': '', 'count': 0, 'tag aliases': set()})

    # Process file1
    for row in data1:
        tag = row['tag']
        merged_data[tag]['category'] = row['category']
        merged_data[tag]['count'] += int(row['count'])
        if row['tag aliases']:
            # Only add aliases that are not tags in file2
            aliases = set(alias.strip() for alias in row['tag aliases'].split(','))
            merged_data[tag]['tag aliases'].update(aliases - tags_in_file2)

    # Process file2
    for row in data2:
        tag = row['tag']
        # Prepend "by " to the tag if category is '1'
        if row['category'] == '1':
            tag = 'by ' + tag
        
        # Always update count, regardless of whether the tag already exists
        merged_data[tag]['count'] += int(row['count'])
        
        # If the tag didn't exist in file1, update category and aliases
        if merged_data[tag]['category'] == '':
            merged_data[tag]['category'] = row['category']
        if "tag aliases" in row:
            if row['tag aliases']:
                merged_data[tag]['tag aliases'].update(alias.strip() for alias in row['tag aliases'].split(','))

    # Convert merged data to list of dictionaries and sort by count in descending order
    result = []
    for tag, data in merged_data.items():
        result.append({
            'tag': tag,
            'category': data['category'],
            'count': data['count'],
            'tag aliases': ','.join(sorted(data['tag aliases']))  # Join aliases without spaces
        })
    
    # Sort the result list by count in descending order
    result.sort(key=lambda x: x['count'], reverse=True)

    return result

def save_csv(data, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['tag', 'category', 'count', 'tag aliases']
        writer = csv.DictWriter(file, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for row in data:
            # Ensure 'count' is not quoted by converting it to int
            row['count'] = int(row['count'])
            # Ensure 'tag aliases' is a string
            row['tag aliases'] = row['tag aliases'] if isinstance(row['tag aliases'], str) else ','.join(row['tag aliases'])
            writer.writerow(row)

# Usage
file1 = 'autocomplete/csv/resonance_furry.csv'
file2 = 'autocomplete/csv/resonance_anime.csv'
output_file = 'merged_output.csv'

merged_data = merge_csvs(file1, file2)
save_csv(merged_data, output_file)

print(f"Merged CSV saved to {output_file}")
#!.finPayVenv/bin/python3

import pandas as pd
import json


def make_initial_state_file(file_path, json_out_path):
    """Get unique names from files [...]"""
    df = pd.read_excel(file_path)
    df['Name'] = df['Name'].apply(lambda x: x.strip())
    df = df.drop_duplicates()
    grouped_df = df.groupby('Name')['Year'].apply(list).reset_index()
    grouped_df['Department'] = None
    grouped_list = grouped_df.to_dict(orient='records')
    with open(json_out_path, 'w') as json_file:
        json.dump(grouped_list, json_file, indent=2)
        print(f"JSON data has been written to {json_out_path}")


def get_fresh_chunk(state_file_path, chunk_size):
    with open(state_file_path, 'r') as json_file:
        state_data = json.load(json_file)

    chunk = {}
    null_found = False
    for entry in state_data:
        if entry['Department'] is None:
            if not null_found: null_found = True
            chunk[entry['Name']] = None
            if len(chunk) == chunk_size: break
        elif null_found:
            continue
    return chunk

def omit_last_letter(name):
    # Split the name by the comma
    parts = name.split(',')
    
    if len(parts) == 2:
        # Get the first name part (which might contain a middle initial)
        first_middle = parts[1].strip()
        
        # Split the first and middle names
        first_middle_parts = first_middle.split()
        
        if len(first_middle_parts) == 2:  # Means there's a first name and a middle initial
            # Omit the middle initial by taking only the first name
            first_name_only = first_middle_parts[0]
            return f"{parts[0]},{first_name_only}"
    
    # Return the name unchanged if no middle initial exists
    return name

def getFirstAndLastNameOnly(name):
     # Split the name by the comma
    parts = name.split(',')
    
    # Ensure that the name has both last and first/middle parts
    if len(parts) == 2:
        last_name = parts[0].strip().split()[0]  # Take only the actual last name (ignore suffix)
        
        # Extract the first and middle name part, if exists
        first_middle = parts[1].strip()
        first_middle_parts = first_middle.split()
        
        # Ensure there are enough parts to get the first name
        if len(first_middle_parts) > 0:
            first_name = first_middle_parts[-1]  # First name should be the last part (e.g., "ALLEN")
            # Return the formatted last name and first name
            return f"{last_name},{first_name}"
    
    # Return the input unchanged if the format is unexpected
    return name
def suppressMiddleName(name):
    # Split the name by comma to separate the last name and first/middle names
    parts = name.split(',')
    
    if len(parts) != 2:
        return name  # Return the name unchanged if the format is not as expected

    last_name = parts[0].strip()
    first_middle = parts[1].strip()

    # Split the first/middle names by spaces
    name_parts = first_middle.split()
    
    if len(name_parts) == 1:
        # Only first name, no middle name
        return f"{last_name},{name_parts[0]}"
    elif len(name_parts) == 2:
        # First name and middle name
        first_name, middle_name = name_parts
        return f"{last_name},{first_name} {middle_name[0]}"
    elif len(name_parts) > 2:
        first_name = name_parts[0]
        middle_name_initial = name_parts[1][0]  # Take the first letter of the middle name
        remaining_parts = name_parts[2:]  # Remaining parts after the middle name
        remaining_name = " ".join(remaining_parts)  # Join remaining parts as last name
        
        return f"{remaining_name},{first_name} {middle_name_initial}"
    else:
        # Return the name as is if it doesn't fit expected patterns
        return name
    
def suppressLastName(name):
    name_parts = name.split(" ")
    # Check if there are at least two parts to the name
    if len(name_parts) > 1 and name_parts[1] != "":
        name = name_parts[0] + " " + name_parts[1][0]
    
    return name
    
def update_state_file(state_file_path, new_data):
    with open(state_file_path, 'r') as json_file:
        state_data = json.load(json_file)
    counter = 0 
    new_data_copy = new_data.copy()
    for entry in state_data:
        if entry['Name'] in new_data:
            entry['Department'] = new_data[entry['Name']]
            new_data_copy.pop(entry['Name'],None)
            counter += 1
        elif omit_last_letter(entry['Name']) in new_data:
            entry['Department'] = new_data[omit_last_letter(entry['Name'])]
            new_data_copy.pop(omit_last_letter(entry['Name']), None)
            counter += 1
        elif getFirstAndLastNameOnly(entry['Name']) in new_data:
            entry['Department'] = new_data[getFirstAndLastNameOnly(entry['Name'])]
            new_data_copy.pop(getFirstAndLastNameOnly(entry['Name']), None)
            counter += 1
        elif suppressMiddleName(entry['Name']) in new_data:
            #print(f"SUPPRESS MIDDLE NAME: {entry['Name']} to {suppressMiddleName(entry['Name'])}")
            entry['Department'] = new_data[suppressMiddleName(entry['Name'])]
            new_data_copy.pop(suppressMiddleName(entry['Name']), None)
            counter += 1
        elif suppressLastName(entry['Name']) in new_data:
            entry['Department'] = new_data[suppressLastName(entry['Name'])]
            new_data_copy.pop(suppressLastName(entry['Name']), None)
            counter += 1
    for name, department in new_data_copy.items():
        print(f"Name:  {name} was not found in the state file")
    print(f"Updated {counter} entries in the state file")

    with open(state_file_path, 'w') as json_file:
        json.dump(state_data, json_file, indent=2)
        print(f"JSON data has been updated in {state_file_path}")

def normalize_name(scraped_name):
    parts = scraped_name.upper().replace('.', '').split()
    
    if len(parts) == 2:
        first_name, last_name = parts
        return f"{last_name},{first_name}"
    elif len(parts) > 2:
        first_name_middle = ' '.join(parts[:-1])  # Join all parts except the last one for the first name + middle initial
        last_name = parts[-1]  # Last part is the last name
        return f"{last_name},{first_name_middle}"
    else:
        return scraped_name.upper()

def checkStateStatus(state_file):
    with open(state_file, 'r') as json_file:
        state_data = json.load(json_file)
    null_count = 0
    for entry in state_data:
        if entry['Department'] is not None:
            null_count += 1
    print(f"Number of entries filled: {null_count}")
    print(f"Total entries: {len(state_data)}")
#make_initial_state_file('2_salaries/UoI/uoi_2023.xlsx', '2_salaries/UoI/state_2023.json')
#make_initial_state_file('../IOWAsalary1993-2023upd.xlsx', '2_salariesUoIstate_2023.json')
# chunk = get_fresh_chunk('data/2_salariesUoIstate_2023.json', 5)
# print(chunk)
if __name__ == '__main__':
    # excel_file_path = '../../dentistryIowa.xlsx'
    # df = pd.read_excel(excel_file_path)
    # print(len(df['Name'].tolist()))
    # df['Name'] = df['Name'].apply(normalize_name)


    # # Step 2: Convert the DataFrame to a dictionary
    # # Assuming the columns are "Name" and "Department"
    # new_data = pd.Series(df.Department.values, index=df.Name).to_dict()
    # state_file_path = '../data/2_salariesUoIstate_2023.json'
    # update_state_file(state_file_path, new_data)

    state_file_path = '../data/2_salariesUoIstate_2023.json'
    checkStateStatus(state_file_path)
    # print(omit_last_letter("SUKALSKI,JENNIFER M"))

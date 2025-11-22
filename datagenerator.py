import csv
import random
first_names_male = [
    "Aarav", "Vihaan", "Aditya", "Sai", "Arjun", "Reyansh", "Atharv", "Krishna", 
    "Shaurya", "Rudra", "Ishaan", "Dhruv", "Kabir", "Rohan", "Rahul", "Prakash",
    "Anil", "Suresh", "Ramesh", "Amit", "Sanjay", "Rajesh", "Vikram", "Karan",
    "Mohammed", "Ankit", "Rohit", "Manoj", "Sandeep", "Deepak"
]

first_names_female = [
    "Saanvi", "Aadya", "Kiara", "Diya", "Pihu", "Ananya", "Fatima", "Priya", 
    "Riya", "Isha", "Meera", "Sita", "Geeta", "Lakshmi", "Pooja", "Anjali",
    "Kavita", "Sunita", "Anita", "Manju", "Asha", "Usha", "Rekha", "Shanti",
    "Aisha", "Neha", "Priyanka", "Smita", "Rani", "Gayatri"
]

last_names = [
    "Kumar", "Singh", "Patel", "Sharma", "Devi", "Khan", "Gupta", "Yadav",
    "Chauhan", "Verma", "Jain", "Mehta", "Reddy", "Nair", "Iyer", "Rao",
    "Mishra", "Pandey", "Das", "Sharma", "Malhotra", "Kapoor", "Jha",
    "Srivastava", "Agarwal", "Lal", "Pawar", "Kaur", "Ali", "Chopra"
]

TOTAL_ENTRIES = 3600
organ_list = (  
    ["Kidney"] * 2567 + 
    ["Liver"] * 932 +
    ["Heart"] * 47 +  
    ["Lung"] * 43 +     
    ["Pancreas"] * 7 +    
    ["Small Bowel"] * 4    
) 
blood_type_list = (
    ["O+"] * 1296 + 
    ["B+"] * 1152 + 
    ["A+"] * 792 +   
    ["AB+"] * 252 +  
    ["O-"] * 36 +    
    ["B-"] * 36 +    
    ["A-"] * 18 +  
    ["AB-"] * 18     
) 

def get_random_name():
    """Generates a random full name."""
    if random.choice([True, False]):
        first = random.choice(first_names_male)
    else:
        first = random.choice(first_names_female)
    last = random.choice(last_names)
    return f"{first} {last}"

def get_recipient_age(organ):
    """
    Generates a realistic age for a recipient based on the organ.
    Uses random.triangular() to create a weighted distribution.
    """
    if organ == "Kidney":
        return int(random.triangular(25, 70, 48))
    elif organ == "Liver":
        return int(random.triangular(30, 70, 52))
    elif organ == "Heart":
        return int(random.triangular(35, 65, 50))
    elif organ == "Lung":
        return int(random.triangular(40, 70, 55))
    else:
        return int(random.triangular(20, 55, 38))
random.shuffle(organ_list)
random.shuffle(blood_type_list)

database = []
header = ["Serial No", "Name", "Age", "Organ", "Blood_Type", "Viability Duration (hrs)"]
database.append(header)

for i in range(TOTAL_ENTRIES):
    organ = organ_list[i]
    name = get_random_name()
    age = get_recipient_age(organ)
    blood_type = blood_type_list[i]
    duration = random.randint(6, 72)
    
    database.append([
        i + 1,       
        name,
        age,
        organ,
        blood_type,
        duration     
    ])
filename = "transplant_database.csv"
try:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(database)
    print(f"Successfully generated {filename} with {TOTAL_ENTRIES} entries ")

except IOError:
    print(f"Error: Could not write to the file {filename}.")
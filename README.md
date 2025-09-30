# Organ Donation Matching Project  

## Introduction  
This project is about helping patients who need organ transplants by matching them with possible donors. We collect information from the internet and from PDF files about available organs and donor details. When a patient needs a particular organ, our system checks their details (like blood group, organ type, etc.) and finds the best matching donor. The main idea is to make the process of finding donors faster and easier.  

## Features  
- Collect donor and organ information from online sources and PDFs.  
- Store and manage the collected data in a structured way.  
- Match patients to donors based on important factors (blood group, organ type, etc.).  
- Provide donor details to patients (or doctors) who need them.  

## Technology Used  
- **Python** for scraping and data processing  
- **BeautifulSoup** for web scraping  
- **PyPDF2** for extracting data from PDFs  
- **Pandas / NumPy** for cleaning and handling data  
- **Database**:  MongoDB  
- **Matching logic**: rule-based (blood group, organ type, age)  

## How It Works  
1. Data is scraped from the internet or extracted from PDFs.  
2. The data is cleaned and saved into a database.  
3. A patient request is entered into the system with their details.  
4. The program runs a matching algorithm to compare the patient’s needs with available donors.  
5. The result shows the most suitable donor(s).  

This change is made from branch master
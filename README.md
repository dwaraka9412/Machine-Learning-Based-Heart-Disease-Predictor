
❤️ Heart Disease Prediction Web Application

A machine learning–powered web application that predicts the risk of heart disease based on clinical parameters. The system integrates a trained ML model with a user-friendly website to provide real-time prediction, visual risk analysis, and downloadable PDF medical reports.


---

📌 Overview

Heart disease is one of the leading causes of death worldwide. Early detection can significantly reduce risks. This project demonstrates how machine learning models can be deployed as a real-world web application to assist in early heart disease risk assessment.

Users enter medical details through a web interface, and the system predicts whether the patient is at risk of heart disease along with probability visualization.


---

✨ Features

Machine learning–based heart disease prediction

Interactive web interface

Color-coded medical input fields (safe / warning / risk)

Risk meter and probability visualization

Threshold-based decision logic

PDF medical report generation

Data persistence after page refresh

Fast and optimized performance



---

🛠️ Technologies Used

Machine Learning

Logistic Regression

Scikit-learn

Pandas

NumPy


Backend

Python

Flask


Frontend

HTML

CSS

JavaScript


Other Tools

Joblib (model persistence)

ReportLab (PDF generation)



---

⚙️ System Architecture

1. User enters clinical data via the web interface


2. Data is sent to the Flask backend


3. ML model predicts heart disease risk


4. Prediction result is returned to frontend


5. Results are displayed visually


6. PDF medical report can be generated




---

🚀 How to Run the Project

1️⃣ Clone the Repository

git clone https://github.com/your-username/heart-disease-prediction-web.git
cd heart-disease-prediction-web

2️⃣ Create Virtual Environment (Optional but Recommended)

python -m venv venv
venv\Scripts\activate   # Windows

3️⃣ Install Requirements

pip install -r requirements.txt

4️⃣ Run the Application

python app.py

5️⃣ Open in Browser

http://127.0.0.1:5000/


---

📊 Input Parameters

The model uses the following clinical parameters:

Age

Sex

Chest pain type

Resting blood pressure

Serum cholesterol

Fasting blood sugar

Resting ECG results

Maximum heart rate

Exercise-induced angina

Oldpeak

Slope

Number of major vessels

Thalassemia



---

📄 PDF Report

The generated PDF report includes:

Patient name

Input medical values

Prediction result

Disease probability

Clinician notes



---

⚠️ Disclaimer

This project is intended for educational and research purposes only.
It is not a replacement for professional medical diagnosis.


---

🔮 Future Enhancements

Deep learning models

Cloud deployment

User authentication

Mobile application support

Hospital system integration



---

👨‍💻 Author

Saravana Priyan S

# GovExpense: ระบบคำนวณเงินเบิกจ่ายเดินทางไปราชการ 🇹🇭

**GovExpense** is a Python-based application designed to simplify the calculation and documentation of Thai government travel expenses. It calculates per diem, accommodation, and transportation allowances according to Ministry of Finance regulations and generates the necessary PDF forms.

## Features ✨

*   **Automated Calculation:**
    *   **Per Diem:** Calculates daily allowance based on travel duration, overnight stays, and meal deductions.
    *   **Accommodation:** Supports lump-sum and actual receipt methods with automatic ceiling checks based on C-Level.
    *   **Transportation:** Includes a taxi meter estimator and mileage calculator for private vehicles.
*   **PDF Generation:** Automatically fills out standard government expense forms (experimental support).
*   **User-Friendly Interface:** Built with Streamlit for an intuitive web-based experience.
*   **Regulation Compliance:** Logic based on standard Thai government travel expense rules (can be customized).

## Installation 🛠️

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/cal-allowance.git
    cd cal-allowance
    ```

2.  **Install dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Font Setup (Critical for PDF):**
    The application requires the **TH Sarabun New** font to generate Thai PDFs correctly.
    *   Create a folder: `assets/fonts/`
    *   Download `THSarabunNew.ttf` and place it in `assets/fonts/`.
    *   *Note: If the font is missing, the application will warn you, and PDFs may not render Thai characters correctly.*

## Usage 🚀

Run the Streamlit application:

```bash
streamlit run app_streamlit.py
```

The application will open in your default web browser (usually at `http://localhost:8501`).

1.  **Fill in Traveler Info:** Name, Position, Level (C-Level), Department.
2.  **Trip Details:** Enter dates, times, and purpose.
3.  **Expenses:**
    *   Check Per Diem calculation.
    *   Select Accommodation type (Lump sum vs Actual).
    *   Add Transportation items (Taxi, Private Car, etc.).
4.  **Export:** Review the summary and click "Generate PDF" to download the expense form.

## Project Structure 📂

*   `app_streamlit.py`: Main application file (UI).
*   `expense_calculator.py`: Core business logic for expense calculations.
*   `pdf_generator.py`: PDF generation logic using ReportLab.
*   `requirements.txt`: Python dependencies.
*   `assets/`: Contains static assets like fonts.

## Contributing 🤝

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License 📄

[MIT](https://choosealicense.com/licenses/mit/)

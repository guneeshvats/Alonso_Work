# Recordbook_Demo_Page

Current Interface looks like :
![image](https://github.com/user-attachments/assets/eb3527a7-776a-4d15-a695-d10df998adfa)


# Interactive Table Demo

##  Project Overview
This project is a **web-based interactive table demo** that displays individual football passing records. Users can interact with an **annotated image**, select a table, and view its data in a structured format.

- The **left panel** contains an **image with Annotorious annotations**, allowing users to click on different table sections.
- The **right panel** dynamically updates with metadata and tabular data when a table is selected.
- Users can **edit table data** and **submit changes** (mock functionality for now).
- The interface includes **dropdowns** for filtering stat labels, stat periods, and entities.

---

##  Project Directory Structure
```bash
Recordbook_Demo_Page/
│── images/                   # Stores page images used in the UI
│   ├── page-0007.png         # Image of Page 7 with annotations
│── data.json                 # JSON file containing table data
│── index.html                # Main HTML file (entry point)
│── script.js                 # Handles table interaction & data population
│── styles.css                # Stylesheet for UI design
│── README.md                 # Project documentation (this file)
│── script.js                 # JavaScript logic for dynamic table updates
│── styles.css                # CSS styles for layout and elements
```

---

## 🛠️ Setup Instructions

### **1️. Clone the Repository**
```sh
git clone <repository-url>
cd Recordbook_Demo_Page
```

### **2️. Open the Project in a Browser**
Since this project is **purely frontend-based**, you can simply open the `index.html` file in a browser.

- On **Windows/macOS/Linux**, open the folder and **double-click `index.html`**
- Or use a terminal command (for Mac/Linux):
  ```sh
  open index.html   # macOS
  xdg-open index.html   # Linux
  ```

### **3️. Run a Local Server (Optional for CORS Issues)**
If your browser has **CORS restrictions** preventing local file loading, you can serve the project using Python:

```sh
# Python 3
python -m http.server 8000
```
Then, open your browser and navigate to:
```
http://localhost:8000/index.html
```

---

##  Features & Functionality
###  **1. Interactive Image Annotation (Left Panel)**
- Uses **Annotorious** to highlight different tables on an image.
- Clicking on a table annotation loads its corresponding data.

###  **2. Dynamic Table Data (Right Panel)**
- Fetches table details from `data.json`.
- Displays selected table records, including:
  - **Player Name**
  - **Stat Value**
  - **Opponent**
  - **Game Date**
  - **Season**

###  **3. Editable Table Entries**
- Clicking **Edit** makes table cells editable.
- Clicking **Submit** saves changes (mock functionality).

###  **4. Dropdown Filters (Above Table)**
- **Stat Period Dropdown** (Game, Season, Career)
- **Stat Label Dropdown** (Blocked Kicks, Passing Yards, etc.)
- **Entity Dropdown** (Player, Team)

---

##  Technologies Used
- **HTML5** - Structure of the page
- **CSS3** - Styling and layout
- **JavaScript (ES6+)** - Dynamic updates & interactivity
- **Annotorious** - Image annotation functionality
- **JSON** - Data storage for records

---

##  Future Improvements
- Add **backend integration** to persist table edits.
- Improve **dropdown filtering functionality**.
- Enhance **UI responsiveness** for mobile devices.

---

##  License
This project is open-source and available under the **MIT License**.

---

## ✉️ Contact
For any issues or improvements, feel free to contribute or raise an issue.

**Enjoy exploring interactive table data!**


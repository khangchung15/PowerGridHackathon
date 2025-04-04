import requests
from bs4 import BeautifulSoup
from datetime import datetime

def scrape_ercot_data():
    url = "https://www.ercot.com/content/cdr/html/actual_loads_of_weather_zones"
    
    try:
        response = requests.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table")

        if not table:
            return {"error": "Table not found on the page"}, 404

        # Find all rows
        rows = table.find_all("tr")
        data = []
        
        # Process data rows
        for row in rows[1:]:  # Skip header row
            cols = row.find_all("td", class_="labelClassCenter")
            if cols:
                row_data = [col.text.strip() for col in cols]
                print(row_data)  # Keep your debug print
                data.append(row_data)

        return {
            "data": data,
            "timestamp": datetime.now().isoformat()
        }

    except requests.exceptions.RequestException as e:
        return {"error": f"Error fetching URL: {e}"}, 500
    except Exception as e:
        return {"error": f"An error occurred: {e}"}, 500
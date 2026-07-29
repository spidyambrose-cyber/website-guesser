import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
import time

# 1. App Setup
st.title("Bulk Website Guesser 🚀")
st.write("Upload an Excel file with a column named **'Company'** and optional **'Keyword'**.")

# 2. File Uploader
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

if uploaded_file:
    # Read the Excel file
    df = pd.read_excel(uploaded_file)
    
    # Check if 'Company' column exists
    if 'Company' not in df.columns:
        st.error("Error: Your file must have a column named 'Company'.")
    else:
        st.write(f"Found {len(df)} companies. Starting search...")
        
        # Create a progress bar
        my_bar = st.progress(0)
        
        # create a placeholder for the results list so it updates live
        results_list = []

        # 3. Loop through each row
        for index, row in df.iterrows():
            company = str(row['Company'])
            # Use keyword if it exists, otherwise empty string
            keyword = str(row['Keyword']) if 'Keyword' in df.columns else ""
            
            query = f"{company} {keyword} official website"
            
            try:
                # Search DuckDuckGo (limit 1)
                search_results = DDGS().text(query, max_results=1)
                
                if search_results:
                    url = search_results[0]['href']
                else:
                    url = "Not Found"
            except Exception:
                url = "Error"
            
            # Save result
            results_list.append(url)
            
            # Update progress bar
            my_bar.progress((index + 1) / len(df))
            
            # IMPORTANT: Sleep to prevent being blocked (rate limiting)
            time.sleep(1.0)
        
        # 4. Add results to DataFrame and Show Download
        df['Website_Guess'] = results_list
        st.success("Done! ✅")
        st.dataframe(df)

        # Convert to Excel for download
        output_file = "companies_with_websites.xlsx"
        df.to_excel(output_file, index=False)
        
        with open(output_file, "rb") as file:
            st.download_button(
                label="Download Excel Result",
                data=file,
                file_name="companies_with_websites.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

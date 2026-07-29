import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
from urllib.parse import urlparse
import time

# Helper function to clean a URL into a raw domain (e.g., https://nike.com -> nike.com)
def get_clean_domain(url):
    try:
        netloc = urlparse(url).netloc
        domain = netloc.replace("www.", "")
        return domain.lower()
    except Exception:
        return ""

# 1. App Setup
st.title("Strict Domain Guesser 🚀")
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
        st.write(f"Found {len(df)} companies. Starting strict validation search...")
        
        my_bar = st.progress(0)
        results_list = []

        # 3. Loop through each row
        for index, row in df.iterrows():
            company = str(row['Company']).strip().lower()
            keyword = str(row['Keyword']).strip().lower() if 'Keyword' in df.columns and pd.notna(row['Keyword']) else ""
            
            # Formulate search query
            query = f"{company} {keyword} official website"
            final_domain = "Not Found"
            
            try:
                # Fetch top 5 results to find a match
                search_results = DDGS().text(query, max_results=5)
                
                if search_results:
                    for result in search_results:
                        link = result['href']
                        raw_domain = get_clean_domain(link)
                        
                        # FILTER 1: Skip massive social/info platforms
                        junk_domains = ['wikipedia.org', 'facebook.com', 'linkedin.com', 'twitter.com', 'instagram.com', 'crunchbase.com', 'youtube.com']
                        if any(jd in raw_domain for jd in junk_domains):
                            continue
                        
                        # FILTER 2: Strict Match
                        # The domain must contain either the company name or the keyword to be considered a match
                        if (company in raw_domain) or (keyword and keyword in raw_domain):
                            final_domain = raw_domain
                            break  # Found a match, stop looking at other results for this company
                            
            except Exception:
                final_domain = "Error"
            
            # Save the clean domain result
            results_list.append(final_domain)
            
            # Update progress bar
            my_bar.progress((index + 1) / len(df))
            time.sleep(1.2)  # Maintain safety delay
        
        # 4. Add results to DataFrame and Show Download
        df['Clean_Domain'] = results_list
        st.success("Done! ✅")
        st.dataframe(df)

        # Convert to Excel for download
        output_file = "companies_with_domains.xlsx"
        df.to_excel(output_file, index=False)
        
        with open(output_file, "rb") as file:
            st.download_button(
                label="Download Clean Domains Excel",
                data=file,
                file_name="companies_with_domains.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

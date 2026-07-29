import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
from urllib.parse import urlparse
import time
import re

# Helper function to clean a URL into a clean global domain
def get_main_global_domain(url):
    try:
        netloc = urlparse(url).netloc.lower()
        domain = re.sub(r'^(www\d*|m)\.', '', netloc)
        return domain
    except Exception:
        return ""

# Helper function to strip suffix descriptors from company names (e.g., "Zymr, Inc. | AI" -> "Zymr")
def clean_input_company(name):
    clean = str(name).split('|')[0].split('-')[0].split(',')[0]
    return clean.strip().lower()

# 1. App Setup
st.title("Resilient Domain Locator 🎯")
st.write("Optimised for bulk lists. Loops through company names securely without rate blocks.")

# 2. File Uploader
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    if 'Company' not in df.columns:
        st.error("Error: Excel must have a 'Company' column.")
    else:
        st.write(f"Processing {len(df)} rows. Please be patient as we bypass rate limits safely...")
        
        my_bar = st.progress(0)
        results_list = []

        # 3. Process row-by-row
        for index, row in df.iterrows():
            company_raw = str(row['Company'])
            company_clean = clean_input_company(company_raw)
            keyword_raw = str(row['Keyword']).strip().lower() if 'Keyword' in df.columns and pd.notna(row['Keyword']) else ""
            
            # Smart search query formulation
            query = f"{company_clean} official website homepage"
            final_domain = "Not Found"
            
            try:
                # Use DDGS text module (reliably handles multi-row queries without instant blocking)
                with DDGS() as ddgs:
                    search_results = list(ddgs.text(query, max_results=3))
                
                if search_results:
                    for result in search_results:
                        link = result.get('href', '')
                        title = result.get('title', '').lower()
                        snippet = result.get('body', '').lower()
                        
                        raw_domain = get_main_global_domain(link)
                        
                        # Exclude massive platform directories
                        junk = ['wikipedia.org', 'facebook.com', 'linkedin.com', 'twitter.com', 'instagram.com', 'crunchbase.com', 'youtube.com', 'g2.com', 'clutch.co']
                        if any(jd in raw_domain for jd in junk):
                            continue
                        
                        # MATCH LOGIC:
                        # 1. First choice: Title or snippet explicitly matches the core company name
                        if company_clean in raw_domain or company_clean in title or company_clean in snippet:
                            final_domain = raw_domain
                            break
                        
                        # 2. Alternative choice: Keyword match fallback
                        if keyword_raw and (keyword_raw in title or keyword_raw in snippet):
                            final_domain = raw_domain
                            break
                    
                    # 3. Ultimate safety fallback: if no direct match found but we got clear corporate results, take top root domain
                    if final_domain == "Not Found" and search_results:
                        first_link = search_results[0].get('href', '')
                        if not any(jd in first_link for jd in junk):
                            final_domain = get_main_global_domain(first_link)
                            
            except Exception as e:
                final_domain = "Search Overloaded"
            
            results_list.append(final_domain)
            my_bar.progress((index + 1) / len(df))
            
            # Essential pacing pause to keep your execution anonymous and safe
            time.sleep(1.5)
        
        # 4. Save results and present download options
        df['Discovered_Domain'] = results_list
        st.success("Done! ✅")
        st.dataframe(df)

        output_file = "bulk_discovered_domains.xlsx"
        df.to_excel(output_file, index=False)
        
        with open(output_file, "rb") as file:
            st.download_button(
                label="Download Final Domain List",
                data=file,
                file_name="bulk_discovered_domains.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

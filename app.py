import streamlit as st
import pandas as pd
from googlesearch import search
from urllib.parse import urlparse
import time
import re

# Helper function to extract ONLY the main global domain name
def get_main_global_domain(url):
    try:
        netloc = urlparse(url).netloc.lower()
        # Remove www. and any regional prefixes like www2. or m.
        domain = re.sub(r'^(www\d*|m)\.', '', netloc)
        
        # Clean up common regional subdirectories if they exist (e.g., ://domain.com)
        # We only want the root base network location
        return domain
    except Exception:
        return ""

# 1. App Setup
st.title("Smart Google Content Matcher 🎯")
st.write("Combines Company + Keyword row-by-row and scans Google search content for matches.")

# 2. File Uploader
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    # Validation check
    if 'Company' not in df.columns or 'Keyword' not in df.columns:
        st.error("Error: Excel must have both a 'Company' column and a 'Keyword' column.")
    else:
        st.write(f"Found {len(df)} rows. Commencing advanced content-match search...")
        
        my_bar = st.progress(0)
        results_list = []

        # 3. Process row-by-row matching Company and adjacent Keyword cell
        for index, row in df.iterrows():
            company_raw = str(row['Company']).strip()
            keyword_raw = str(row['Keyword']).strip() if pd.notna(row['Keyword']) else ""
            
            # Lowercase versions for background string matching checks
            company_lower = company_raw.lower()
            keyword_lower = keyword_raw.lower()
            
            # Search query linking them tightly together
            query = f"{company_raw} {keyword_raw} official website"
            final_domain = "Not Found"
            
            try:
                # Ask Google for advanced results including descriptive text snippets
                # We check the top 5 links to inspect their context data
                google_results = search(query, num_results=5, advanced=True, lang="en")
                
                for result in google_results:
                    link = result.url
                    title = result.title.lower() if result.title else ""
                    snippet = result.description.lower() if result.description else ""
                    
                    raw_domain = get_main_global_domain(link)
                    
                    # Ignore massive directory/social targets
                    junk = ['wikipedia.org', 'facebook.com', 'linkedin.com', 'twitter.com', 'instagram.com', 'crunchbase.com', 'youtube.com']
                    if any(jd in raw_domain for jd in junk):
                        continue
                    
                    # CORE RULE: Scan information *around* the link (Title and Snippet Text)
                    # Check if the text surrounding the link explicitly mentions our targets
                    company_in_text = company_lower in title or company_lower in snippet or company_lower in raw_domain
                    keyword_in_text = True
                    
                    if keyword_lower:
                        keyword_in_text = keyword_lower in title or keyword_lower in snippet or keyword_lower in raw_domain
                    
                    # If the data text around the link matches both targets, grab it!
                    if company_in_text and keyword_in_text:
                        final_domain = raw_domain
                        break
                        
            except Exception as e:
                final_domain = "Error: Blocked or Rate Limited"
            
            results_list.append(final_domain)
            my_bar.progress((index + 1) / len(df))
            
            # Safe padding delay for scraping 500 rows on Google search indexes
            time.sleep(1.8)  
        
        # 4. Save results and present download options
        df['Discovered_Domain'] = results_list
        st.success("Done! ✅")
        st.dataframe(df)

        output_file = "matched_google_domains.xlsx"
        df.to_excel(output_file, index=False)
        
        with open(output_file, "rb") as file:
            st.download_button(
                label="Download Matched Domains Excel",
                data=file,
                file_name="matched_google_domains.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
